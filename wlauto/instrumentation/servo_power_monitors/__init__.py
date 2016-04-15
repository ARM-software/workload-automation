#    Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


# pylint: disable=W0613,E1101,attribute-defined-outside-init
from __future__ import division
import os
import subprocess
import signal
import csv
import threading
import time
import getpass
from collections import defaultdict

from wlauto import Instrument, Parameter, Executable
from wlauto.exceptions import InstrumentError, ConfigError
from wlauto.utils.types import list_of_strings
from wlauto.utils.misc import check_output
from wlauto.utils.cros_sdk import CrosSdkSession
from wlauto.utils.misc import which, ensure_directory_exists


class ServoPowerMonitor(Instrument):

    name = 'servo_power_monitor'
    description = """Collects power traces using the Chromium OS Servo Board.

                     Servo is a debug board used for Chromium OS test and development. Among other uses, it allows
                     access to the built in power monitors (if present) of a Chrome OS device. More information on
                     Servo board can be found in the link bellow:

                     https://www.chromium.org/chromium-os/servo

                     In order to use this instrument you need to be a sudoer and you need a chroot environment. More
                     information on the chroot environment can be found on the link bellow:

                     https://www.chromium.org/chromium-os/developer-guide

                    """

    parameters = [
        Parameter('power_domains', kind=list_of_strings, default=[],
                  description="""The names of power domains to be monitored by the instrument using servod."""),
        Parameter('labels', kind=list_of_strings, default=[],
                  description="""Meaningful labels for each of the monitored domains."""),
        Parameter('chroot_path', kind=str, default='',
                  description="""Path to chroot direcory on the host."""),
        Parameter('sampling_rate', kind=int, default=10,
                  description="""Samples per second."""),
        Parameter('board_name', kind=str, mandatory=True,
                  description="""The name of the board under test."""),
    ]

    # When trying to initialize servod, it may take some time until the server is up
    # Therefore we need to poll to identify when the sever has successfully started
    # servod_max_tries specifies the maximum number of times we will check to see if the server has started
    # while servod_delay_between_tries is the sleep time between checks.
    servod_max_tries = 100
    servod_delay_between_tries = 0.1

    def initialize(self, context):
        # pylint: disable=access-member-before-definition
        self.poller = None
        password = ''
        checks = 0
        self.power_data = None
        self.stopped = True

        self.in_chroot = which('dut-control') is not None
        if not self.in_chroot:
            self.logger.info('Instrument {} requires sudo acces on this machine'.format(self.name))
            self.logger.info('You need to be sudoer to use it.')
            password = getpass.getpass()
            check = subprocess.call('echo {} | sudo -S ls > /dev/null'.format(password), shell=True)
            if check:
                raise InstrumentError('Given password was either wrong or you are not a sudoer')

        self.server_session = CrosSdkSession(self.chroot_path, password=password)
        self.cros_session = CrosSdkSession(self.chroot_path, password=password)

        self.logger.debug("Waiting for servod to start")
        self.server_session.send_command('sudo servod -b {b} -c {b}.xml&'.format(b=self.board_name))
        while True:
            if checks >= self.servod_max_tries:
                raise InstrumentError('Failed to start servod in cros_sdk environment')
            server_lines = self.server_session.get_lines(timeout=1, from_stderr=True,
                                                         timeout_only_for_first_line=False)
            for line in server_lines:
                self.logger.debug(line)
            if server_lines and 'Listening on' in server_lines[-1]:
                break
        time.sleep(self.servod_delay_between_tries)
        checks += 1
        self.port = int(server_lines[-1].split()[-1])

        for domain in self.power_domains:
            self.cros_session.send_command("dut-control {} -p {}".format(domain, self.port))
            result = self.cros_session.get_lines()
            self.logger.debug(result)
            if "No control named" in result:
                raise ConfigError("No control named {}".format(domain))

        self.command = 'dut-control {} -p {}'.format(' '.join(set(self.power_domains)), self.port)

    def validate(self):
        # pylint: disable=access-member-before-definition
        if self.labels and len(self.power_domains) != len(self.labels):
            raise ConfigError('There should be exactly one label per power domain')
        if not self.labels:
            self.labels = [domain for domain in self.power_domains]
        self.power_domains = [domain if domain.endswith('_mw') else domain + '_mw' for domain in self.power_domains]

    def setup(self, context):
        self.output_directory = os.path.join(context.output_directory, 'servo_power_monitor')
        self.poller = PowerPoller(self.cros_session, self.command, self.power_domains, self.sampling_rate)

    def start(self, context):
        self.poller.start()
        self.stopped = False

    def stop(self, context):
        self.power_data = self.poller.stop()
        self.poller.join()
        self.stopped = True

    def update_result(self, context):
        ensure_directory_exists(self.output_directory)
        for domain, label in zip(self.power_domains, self.labels):
            metric_name = '{}_power'.format(label)
            sample_sum = sum(self.power_data[domain])
            power = sample_sum / len(self.power_data[domain])
            context.result.add_metric(metric_name, round(power, 3), 'Watts')

            metric_name = '{}_energy'.format(label)
            energy = sample_sum * (1.0 / self.sampling_rate)
            context.result.add_metric(metric_name, round(energy, 3), 'Joules')

            outfile = os.path.join(self.output_directory, '{}.csv'.format(label))
            with open(outfile, 'wb') as f:
                c = csv.writer(f)
                c.writerow(['{}_power'.format(domain)])
                for val in self.power_data[domain]:
                    c.writerow([val])

    def teardown(self, context):
        if not self.stopped:
            self.stop(context)
        self.server_session.kill_session()
        self.cros_session.kill_session()


class PowerPoller(threading.Thread):

    def __init__(self, cros_session, command, power_domains, sampling_rate):
        super(PowerPoller, self).__init__()
        self.command = command
        self.power_data = {domain: [] for domain in power_domains}
        self.samples_per_frame = sampling_rate
        self.period = 1.0 / sampling_rate
        self.term_signal = threading.Event()
        self.term_signal.set()
        self.cros_session = cros_session

    def run(self):
        while self.term_signal.is_set():
            time.sleep(self.period)
            self.cros_session.send_command(self.command)
            lines = self.cros_session.get_lines()
            for line in lines:
                domain, value = line.split(':')
                self.power_data[domain].append(float(value) / 1000)

    def stop(self):
        self.term_signal.clear()
        self.join()
        return self.power_data

