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
import re

from wa import ApkUiautoWorkload, WorkloadError, Parameter
from wa.utils.types import list_or_string


class Gfxbench(ApkUiautoWorkload):

    name = 'gfxbench-corporate'
    package_names = ['net.kishonti.gfxbench.gl.v50000.corporate']
    clear_data_on_reset = False
    score_regex = re.compile(r'.*?([\d.]+).*')
    description = '''
    Execute a subset of graphical performance benchmarks

    Test description:
    1. Open the gfxbench application
    2. Execute Car Chase, Manhattan and Tessellation benchmarks

    Note: Some of the default tests are unavailable on devices running
          with a smaller resolution than 1080p.

    '''

    default_test_list = [
        "Car Chase",
        "1080p Car Chase Offscreen",
        "Manhattan 3.1",
        "1080p Manhattan 3.1 Offscreen",
        "1440p Manhattan 3.1.1 Offscreen",
        "Tessellation",
        "1080p Tessellation Offscreen",
    ]

    parameters = [
        Parameter('timeout', kind=int, default=3600,
                  description=('Timeout for an iteration of the benchmark.')),
        Parameter('tests', kind=list_or_string, default=default_test_list,
                  description=('List of tests to be executed.')),
    ]

    def __init__(self, target, **kwargs):
        super(Gfxbench, self).__init__(target, **kwargs)
        self.gui.timeout = self.timeout
        self.gui.uiauto_params['tests'] = self.tests

    def update_output(self, context):
        super(Gfxbench, self).update_output(context)
        expected_results = len(self.test_list)
        regex_matches = [re.compile('{} score (.+)'.format(t)) for t in self.test_list]
        logcat_file = context.get_artifact_path('logcat')
        with open(logcat_file, errors='replace') as fh:
            for line in fh:
                for regex in regex_matches:
                    match = regex.search(line)
                    # Check if we have matched the score string in logcat
                    if match:
                        score_match = self.score_regex.search(match.group(1))
                        # Check if there is valid number found for the score.
                        if score_match:
                            result = float(score_match.group(1))
                        else:
                            result = 'NaN'
                        entry = regex.pattern.rsplit(None, 1)[0]
                        context.add_metric(entry, result, 'FPS', lower_is_better=False)
                        expected_results -= 1
        if expected_results > 0:
            msg = "The GFXBench workload has failed. Expected {} scores, Detected {} scores."
            raise WorkloadError(msg.format(len(self.regex_matches), expected_results))
