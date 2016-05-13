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
# pylint: disable=attribute-defined-outside-init
import os
import yaml

from wlauto import Workload, Parameter, Executable
from wlauto.exceptions import WorkloadError, ConfigError


class StressNg(Workload):

    name = 'stress_ng'
    description = """
    stress-ng will stress test a computer system in various selectable ways. It
    was designed to exercise various physical subsystems of a computer as well
    as the various operating system kernel interfaces.

    stress-ng can also measure test throughput rates; this can be useful to
    observe performance changes across different operating system releases or
    types of hardware. However, it has never been intended to be used as a
    precise benchmark test suite, so do NOT use it in this manner.

    The official website for stress-ng is at:
        http://kernel.ubuntu.com/~cking/stress-ng/

    Source code are available from:
        http://kernel.ubuntu.com/git/cking/stress-ng.git/
    """

    parameters = [
        Parameter('stressor', kind=str, default='cpu',
                  allowed_values=['cpu', 'io', 'fork', 'switch', 'vm', 'pipe',
                                  'yield', 'hdd', 'cache', 'sock', 'fallocate',
                                  'flock', 'affinity', 'timer', 'dentry',
                                  'urandom', 'sem', 'open', 'sigq', 'poll'],
                  description='Stress test case name. The cases listed in '
                              'allowed values come from the stable release '
                              'version 0.01.32. The binary included here '
                              'compiled from dev version 0.06.01. Refer to '
                              'man page for the definition of each stressor.'),
        Parameter('threads', kind=int, default=0,
                  description='The number of workers to run. Specifying a '
                              'negative or zero value will select the number '
                              'of online processors.'),
        Parameter('duration', kind=int, default=60,
                  description='Timeout for test execution in seconds')
    ]

    def initialize(self, context):
        if not self.device.is_rooted:
            raise WorkloadError('stress-ng requires root premissions to run')

    def validate(self):
        if self.stressor == 'vm' and self.duration < 60:
            raise ConfigError('vm test duration need to be >= 60s.')

    def setup(self, context):
        host_binary = context.resolver.get(Executable(self, self.device.abi,
                                                      'stress-ng'))
        self.binary = self.device.install_if_needed(host_binary)
        self.log = self.device.path.join(self.device.working_directory,
                                         'stress_ng_output.txt')
        self.results = self.device.path.join(self.device.working_directory,
                                             'stress_ng_results.yaml')
        self.command = ('{} --{} {} --timeout {}s --log-file {} --yaml {} '
                        '--metrics-brief --verbose'
                        .format(self.binary, self.stressor, self.threads,
                                self.duration, self.log, self.results))
        self.timeout = self.duration + 10

    def run(self, context):
        self.output = self.device.execute(self.command, timeout=self.timeout,
                                          as_root=True)

    def update_result(self, context):
        host_file_log = os.path.join(context.output_directory,
                                     'stress_ng_output.txt')
        host_file_results = os.path.join(context.output_directory,
                                         'stress_ng_results.yaml')
        self.device.pull_file(self.log, host_file_log)
        self.device.pull_file(self.results, host_file_results)

        with open(host_file_results, 'r') as stress_ng_results:
            results = yaml.load(stress_ng_results)

        try:
            metric = results['metrics'][0]['stressor']
            throughput = results['metrics'][0]['bogo-ops']
            context.result.add_metric(metric, throughput, 'ops')
        # For some stressors like vm, if test duration is too short, stress_ng
        # may not able to produce test throughput rate.
        except TypeError:
            self.logger.warning('{} test throughput rate not found. '
                                'Please increase test duration and retry.'
                                .format(self.stressor))
