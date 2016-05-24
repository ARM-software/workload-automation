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

from wlauto import Workload, Parameter, Executable


class Blogbench(Workload):

    name = 'blogbench'
    description = """
    Blogbench is a portable filesystem benchmark that tries to reproduce the
    load of a real-world busy file server.

    Blogbench stresses the filesystem with multiple threads performing random
    reads, writes and rewrites in order to get a realistic idea of the
    scalability and the concurrency a system can handle.

    Source code are available from:
        https://download.pureftpd.org/pub/blogbench/
    """

    parameters = [
        Parameter('iterations', kind=int, default=30,
                  description='The number of iterations to run')
    ]

    def setup(self, context):
        host_binary = context.resolver.get(Executable(self, self.device.abi,
                                                      'blogbench'))
        self.binary = self.device.install_if_needed(host_binary)
        # Total test duration equal to iteration*frequency
        # The default frequency is 10 seconds, plus 5 here as a buffer.
        self.timeout = self.iterations * 15
        # An empty and writable directory is needed.
        self.directory = self.device.path.join(self.device.working_directory,
                                               'blogbench')
        self.device.execute('rm -rf {}'.format(self.directory), timeout=300)
        self.device.execute('mkdir -p {}'.format(self.directory))
        self.results = self.device.path.join(self.device.working_directory,
                                             'blogbench.output')
        self.command = ('{} --iterations {} --directory {} > {}'
                        .format(self.binary, self.iterations, self.directory,
                                self.results))

    def run(self, context):
        self.output = self.device.execute(self.command, timeout=self.timeout)

    def update_result(self, context):
        host_file = os.path.join(context.output_directory, 'blogbench.output')
        self.device.pull_file(self.results, host_file)

        with open(host_file, 'r') as blogbench_output:
            for line in blogbench_output:
                if any('Final score for ' + x in line
                       for x in ['writes', 'reads']):
                    line = line.split(':')
                    metric = line[0].lower().strip().replace(' ', '_')
                    score = int(line[1].strip())
                    context.result.add_metric(metric, score, 'blogs')

    def finalize(self, context):
        self.device.execute('rm -rf {}'.format(self.directory), timeout=300)
