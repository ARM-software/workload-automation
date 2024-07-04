#    Copyright 2024 ARM Limited
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

from wa import ApkUiautoWorkload, Parameter, TestPackageHandler
from wa.utils.types import list_of_strs
import re

class Jetnews(ApkUiautoWorkload):

    name = 'jetnews'
    package_names = ['com.example.jetnews']
    description = '''
    JetNews
    '''

    default_test_strings = [
        'PortraitVerticalTest',
        'PortraitHorizontalTest',
        'LandscapeVerticalTest',
    ]

    parameters = [
        Parameter('tests', kind=list_of_strs,
                  description="""
                  List of tests to be executed. The available
                  tests are PortraitVerticalTest, LandscapeVerticalTest and
                  PortraitHorizontalTest. If none are specified, the default
                  is to run all of them.
                  """, default=default_test_strings),
        Parameter('flingspeed', kind=int,
                  description="""
                  Default fling speed for the tests. The default is 5000 and
                  the minimum value is 1000.
                  """, default=5000),
        Parameter('repeat', kind=int,
                  description="""
                  The number of times the tests should be repeated. The default
                  is 1.
                  """, default=1)
    ]

    _OUTPUT_SECTION_REGEX = re.compile(
        r'(\s*INSTRUMENTATION_STATUS: gfx-[\w-]+=[-+\d.]+\n)+'
        r'\s*INSTRUMENTATION_STATUS_CODE: (?P<code>[-+\d]+)\n?', re.M)
    _OUTPUT_GFXINFO_REGEX = re.compile(
        r'INSTRUMENTATION_STATUS: (?P<name>[\w-]+)=(?P<value>[-+\d.]+)')

    def __init__(self, target, **kwargs):
        super(Jetnews, self).__init__(target, **kwargs)
        # This test uses the androidx library.
        self.gui.uiauto_runner = 'androidx.test.runner.AndroidJUnitRunner'
        # Class for the regular instrumented tests.
        self.gui.uiauto_class = 'UiAutomation'
        # Class containing the jank tests.
        self.gui.uiauto_jank_class = 'UiAutomationJankTests'
        # A list of all the individual jank tests contained in the jetnews
        # uiauto apk.
        self.gui.jank_stages = ['test1']
        self.gui.uiauto_params['tests'] = self.tests
        self.gui.uiauto_params['flingspeed'] = self.flingspeed
        self.gui.uiauto_params['repeat'] = self.repeat
        # Declared here so we can hold the test output for later processing.
        self.output = {}

    def run(self, context):
        # Run the jank tests and capture the output so we can parse it
        # into the output result file.
        self.output['test1'] = self.gui._execute('test1', self.gui.timeout)

    def update_output(self, context):
        super(Jetnews, self).update_output(context)
        # Parse the test result and filter out the results so we can output
        # a meaningful result file.
        for test, test_output in self.output.items():
            for section in self._OUTPUT_SECTION_REGEX.finditer(test_output):
                if int(section.group('code')) != -1:
                    msg = 'Run failed (INSTRUMENTATION_STATUS_CODE: {}). See log.'
                    raise RuntimeError(msg.format(section.group('code')))
                for metric in self._OUTPUT_GFXINFO_REGEX.finditer(section.group()):
                    context.add_metric(metric.group('name'), metric.group('value'),
                                       classifiers={'test_name': test})
