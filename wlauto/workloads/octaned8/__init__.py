#    Copyright 2014-2016 ARM Limited
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

#pylint: disable=E1101,W0201

import os
import re

from wlauto import Workload, Parameter, Executable
from wlauto.common.resources import File
from wlauto.exceptions import ConfigError


regex_map = {
    "Richards": (re.compile(r'Richards: (\d+.*)')),
    "DeltaBlue": (re.compile(r'DeltaBlue: (\d+.*)')),
    "Crypto": (re.compile(r'Crypto: (\d+.*)')),
    "RayTrace": (re.compile(r'RayTrace: (\d+.*)')),
    "EarleyBoyer": (re.compile(r'EarleyBoyer: (\d+.*)')),
    "RegExp": (re.compile(r'RegExp: (\d+.*)')),
    "Splay": (re.compile(r'Splay: (\d+.*)')),
    "SplayLatency": (re.compile(r'SplayLatency: (\d+.*)')),
    "NavierStokes": (re.compile(r'NavierStokes: (\d+.*)')),
    "PdfJS": (re.compile(r'PdfJS: (\d+.*)')),
    "Mandreel": (re.compile(r'Mandreel: (\d+.*)')),
    "MandreelLatency": (re.compile(r'MandreelLatency: (\d+.*)')),
    "Gameboy": (re.compile(r'Gameboy: (\d+.*)')),
    "CodeLoad": (re.compile(r'CodeLoad: (\d+.*)')),
    "Box2D": (re.compile(r'Box2D: (\d+.*)')),
    "zlib": (re.compile(r'zlib: (\d+.*)')),
    "Score": (re.compile(r'Score .*: (\d+.*)'))
}


class Octaned8(Workload):

    name = 'octaned8'
    description = """
    Runs the Octane d8 benchmark.

    This workload runs d8 binaries built from source and placed in the dependencies folder along
    with test assets from https://github.com/chromium/octane which also need to be placed in an
    assets folder within the dependencies folder.

    Original source from::

        https://github.com/v8/v8/wiki/D8%20on%20Android

    """

    parameters = [
        Parameter('run_timeout', kind=int, default=180,
                  description='Timeout, in seconds, for the test execution.'),
    ]

    supported_platforms = ['android']

    executables = ['d8', 'natives_blob.bin', 'snapshot_blob.bin']

    def initialize(self, context):  # pylint: disable=no-self-use
        assets_dir = self.device.path.join(self.device.working_directory, 'assets')
        self.device.execute('mkdir -p {}'.format(assets_dir))

        assets_tar = 'octaned8-assets.tar'
        fpath = context.resolver.get(File(self, assets_tar))
        self.device.push_file(fpath, assets_dir, timeout=300)
        self.command = 'cd {}; {} busybox tar -x -f {}'.format(assets_dir, self.device.busybox, assets_tar)
        self.output = self.device.execute(self.command, timeout=self.run_timeout)

        for f in self.executables:
            binFile = context.resolver.get(Executable(self, self.device.abi, f))
            self.device_exe = self.device.install(binFile)

    def setup(self, context):
        self.logger.info('Copying d8 binaries to device')
        assets_dir = self.device.path.join(self.device.working_directory, 'assets')
        device_file = self.device.path.join(self.device.working_directory, 'octaned8.output')
        self.command = 'cd {}; {}/d8 ./run.js >> {} 2>&1'.format(assets_dir, self.device.binaries_directory, device_file)

    def run(self, context):
        self.logger.info('Starting d8 tests')
        self.output = self.device.execute(self.command, timeout=self.run_timeout)

    def update_result(self, context):
        host_file = os.path.join(context.output_directory, 'octaned8.output')
        device_file = self.device.path.join(self.device.working_directory, 'octaned8.output')
        self.device.pull_file(device_file, host_file)

        with open(os.path.join(host_file)) as octaned8_file:
            for line in octaned8_file:
                for label, regex in regex_map.iteritems():
                    match = regex.search(line)
                    if match:
                        context.result.add_metric(label, float(match.group(1)))

        self.device.execute('rm {}'.format(device_file))

    def finalize(self, context):
        for f in self.executables:
            self.device.uninstall_executable(f)
            self.device.execute('rm  {}'.format(self.device.path.join(self.device.working_directory, f)))
        assets_dir = self.device.path.join(self.device.working_directory, 'assets')
        self.device.execute('rm -rf {}'.format(assets_dir))
