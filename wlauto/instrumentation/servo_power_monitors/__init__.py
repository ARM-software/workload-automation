#    Copyright 2016 ARM Limited
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
import logging
import xmlrpclib
from datetime import datetime

from wlauto import Instrument, Parameter, Executable
from wlauto.exceptions import InstrumentError, ConfigError
from wlauto.utils.types import list_of_strings
from wlauto.utils.misc import check_output
from wlauto.utils.cros_sdk import CrosSdkSession
from wlauto.utils.misc import which


class ServoPowerMonitor(Instrument):

    name = 'servo_power'
    description = """
    Collects power traces using the Chromium OS Servo Board.

    Servo is a debug board used for Chromium OS test and development. Among other uses, it allows
    access to the built in power monitors (if present) of a Chrome OS device. More information on
    Servo board can be found in the link bellow:

    https://www.chromium.org/chromium-os/servo

    In order to use this instrument you need to be a sudoer and you need a chroot environment. More
    information on the chroot environment can be found on the link bellow:

    https://www.chromium.org/chromium-os/developer-guide

    If you wish to run servod on a remote machine you will need to allow it to accept external connections
    using the `--host` command line option, like so:
    `sudo servod -b some_board -c some_board.xml --host=''`

    """

    parameters = [
        Parameter('power_domains', kind=list_of_strings, default=[],
                  description="""The names of power domains to be monitored by the
                                 instrument using servod."""),
        Parameter('labels', kind=list_of_strings, default=[],
                  description="""Meaningful labels for each of the monitored domains."""),
        Parameter('chroot_path', kind=str,
                  description="""Path to chroot direcory on the host."""),
        Parameter('sampling_rate', kind=int, default=10,
                  description="""Samples per second."""),
        Parameter('board_name', kind=str, mandatory=True,
                  description="""The name of the board under test."""),
        Parameter('autostart', kind=bool, default=True,
                  description="""Automatically start `servod`. Set to `False` if you want to
                                 use an already running `servod` instance or a remote servo"""),
        Parameter('host', kind=str, default="localhost",
                  description="""When `autostart` is set to `False` you can specify the host
                                 on which `servod` is running allowing you to remotelly access
                                 as servo board.

                                 if `autostart` is `True` this parameter is ignored and `localhost`
                                 is used instead"""),
        Parameter('port', kind=int, default=9999,
                  description="""When `autostart` is set to false you must provide the port
                                 that `servod` is running on

                                 If `autostart` is `True` this parameter is ignored and the port
                                 output during the startup of `servod` will be used."""),
        Parameter('vid', kind=str,
                  description="""When more than one servo is plugged in, you must provide
                                 a vid/pid pair to identify the servio you wish to use."""),
        Parameter('pid', kind=str,
                  description="""When more than one servo is plugged in, you must provide
                                 a vid/pid pair to identify the servio you wish to use."""),
    ]

    # When trying to initialize servod, it may take some time until the server is up
    # Therefore we need to poll to identify when the sever has successfully started
    # servod_max_tries specifies the maximum number of times we will check to see if the server has started
    # while servod_delay_between_tries is the sleep time between checks.
    servod_max_tries = 100
    servod_delay_between_tries = 0.1

    def validate(self):
        # pylint: disable=access-member-before-definition
        if self.labels and len(self.power_domains) != len(self.labels):
            raise ConfigError('There should be exactly one label per power domain')
        if self.autostart:
            if self.host != 'localhost':  # pylint: disable=access-member-before-definition
                self.logger.warning('Ignoring host "%s" since autostart is set to "True"', self.host)
                self.host = "localhost"
        if (self.vid is None) != (self.pid is None):
            raise ConfigError('`vid` and `pid` must both be specified')

    def initialize(self, context):
        # pylint: disable=access-member-before-definition
        self.poller = None
        self.data = None
        self.stopped = True

        if self.device.platform != "chromeos":
            raise InstrumentError("servo_power instrument only supports Chrome OS devices.")

        if not self.labels:
            self.labels = ["PORT_{}".format(channel) for channel, _ in enumerate(self.power_domains)]

        self.power_domains = [channel if channel.endswith("_mw") else
                              "{}_mw".format(channel) for channel in self.power_domains]
        self.label_map = {pd: l for pd, l in zip(self.power_domains, self.labels)}

        if self.autostart:
            self._start_servod()

    def setup(self, context):
        # pylint: disable=access-member-before-definition
        self.outfile = os.path.join(context.output_directory, 'servo.csv')
        self.poller = PowerPoller(self.host, self.port, self.power_domains, self.sampling_rate)

    def start(self, context):
        self.poller.start()
        self.stopped = False

    def stop(self, context):
        self.data = self.poller.stop()
        self.poller.join()
        self.stopped = True

        timestamps = self.data.pop("timestamp")
        for channel, data in self.data.iteritems():
            label = self.label_map[channel]
            data = [float(v) / 1000.0 for v in data]
            sample_sum = sum(data)

            metric_name = '{}_power'.format(label)
            power = sample_sum / len(data)
            context.result.add_metric(metric_name, round(power, 3), 'Watts')

            metric_name = '{}_energy'.format(label)
            energy = sample_sum * (1.0 / self.sampling_rate)
            context.result.add_metric(metric_name, round(energy, 3), 'Joules')

        with open(self.outfile, 'wb') as f:
            c = csv.writer(f)
            headings = ['timestamp'] + ['{}_power'.format(label) for label in self.labels]
            c.writerow(headings)
            for row in zip(timestamps, *self.data.itervalues()):
                c.writerow(row)

    def teardown(self, context):
        if not self.stopped:
            self.stop(context)
        if self.autostart:
            self.server_session.kill_session()

    def _start_servod(self):
        in_chroot = False if which('dut-control') is None else True
        password = ''
        if not in_chroot:
            msg = 'Instrument %s requires sudo access on this machine to start `servod`'
            self.logger.info(msg, self.name)
            self.logger.info('You need to be sudoer to use it.')
            password = getpass.getpass()
            check = subprocess.call('echo {} | sudo -S ls > /dev/null'.format(password), shell=True)
            if check:
                raise InstrumentError('Given password was either wrong or you are not a sudoer')
        self.server_session = CrosSdkSession(self.chroot_path, password=password)
        password = ''

        command = 'sudo servod -b {b} -c {b}.xml'
        if self.vid and self.pid:
            command += " -v " + self.vid
            command += " -p " + self.pid
        command += '&'
        self.server_session.send_command(command.format(b=self.board_name))
        for _ in xrange(self.servod_max_tries):
            server_lines = self.server_session.get_lines(timeout=1, from_stderr=True,
                                                         timeout_only_for_first_line=False)
            if server_lines:
                if 'Listening on' in server_lines[-1]:
                    self.port = int(server_lines[-1].split()[-1])
                    break
            time.sleep(self.servod_delay_between_tries)
        else:
            raise InstrumentError('Failed to start servod in cros_sdk environment')


class PowerPoller(threading.Thread):

    def __init__(self, host, port, channels, sampling_rate):
        super(PowerPoller, self).__init__()
        self.proxy = xmlrpclib.ServerProxy("http://{}:{}/".format(host, port))
        self.proxy.get(channels[1])  # Testing connection
        self.channels = channels
        self.data = {channel: [] for channel in channels}
        self.data['timestamp'] = []
        self.period = 1.0 / sampling_rate

        self.term_signal = threading.Event()
        self.term_signal.set()
        self.logger = logging.getLogger(self.__class__.__name__)

    def run(self):
        while self.term_signal.is_set():
            self.data['timestamp'].append(str(datetime.now()))
            for channel in self.channels:
                self.data[channel].append(float(self.proxy.get(channel)))
            time.sleep(self.period)

    def stop(self):
        self.term_signal.clear()
        self.join()
        return self.data
