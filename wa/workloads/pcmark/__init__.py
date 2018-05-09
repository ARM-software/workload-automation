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
import glob
import os

from wa import ApkUiautoWorkload, Parameter
from wa.framework.exception import ValidationError
from wa.utils.types import list_of_strs
from wa.utils.misc import unique


class PcMark(ApkUiautoWorkload):

    name = 'pcmark'
    package_names = ['com.futuremark.pcmark.android.benchmark']
    description = '''
    A workload to execute the Work 2.0 benchmarks within PCMark - https://www.futuremark.com/benchmarks/pcmark-android

    Test description:
    1. Open PCMark application
    2. Swipe right to the Benchmarks screen
    3. Select the Work 2.0 benchmark
    4. Install the Work 2.0 benchmark
    5. Execute the Work 2.0 benchmark

    Known working APK version: 2.0.3716
    '''

    def __init__(self, target, **kwargs):
        super(PcMark, self).__init__(target, **kwargs)
        self.gui.timeout = 1500

    def extract_results(self, context):
        results_path = self.target.path.join(self.target.external_storage, "PCMark for Android")
        result_file = self.target.execute('ls -1 \"' + results_path + '\"| tail -n 1')
        result_file = result_file.rstrip()
        result = (results_path + "/" + result_file)
        self.target.pull(result, context.output_directory)

