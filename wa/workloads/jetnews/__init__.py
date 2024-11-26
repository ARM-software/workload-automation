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

from wa import Parameter, ApkUiautoJankTestWorkload, TestPackageHandler

from wa.utils.types import list_of_strs


class Jetnews(ApkUiautoJankTestWorkload):  # pylint: disable=too-many-ancestors

    name = 'jetnews'
    package_names = ['com.example.jetnews']
    description = '''
    This workload uses the JetNews sample app to run a set of UiAutomation
    tests, with the goal of gathering frame metrics and calculating jank
    frame percentages.

    It uses two APK's, the JetNews app itself (modified to contain more posts)
    and the UiAutomation tests that interact with the app.

    There are 3 available tests, two in portrait mode and 1 in landscape mode.

    Please note the UiAutomation APK bundled with Workload Automation requires
    Android 9 (API level 28) to work correctly, otherwise it will fail to
    install.
    '''

    default_test_strings = [
        'PortraitVerticalTest',
        'PortraitHorizontalTest',
        'LandscapeVerticalTest',
    ]

    # List of jank tests to invoke for this workload.
    jetnews_jank_tests = ['test1']

    parameters = [
        Parameter('tests', kind=list_of_strs,
                  description="""
                  List of tests to be executed. The available
                  tests are PortraitVerticalTest, LandscapeVerticalTest and
                  PortraitHorizontalTest. If none are specified, the default
                  is to run all of them.
                  """, default=default_test_strings,
                  constraint=lambda x: all(v in ['PortraitVerticalTest', 'PortraitHorizontalTest', 'LandscapeVerticalTest'] for v in x)),
        Parameter('flingspeed', kind=int,
                  description="""
                  Default fling speed for the tests. The default is 5000 and
                  the minimum value is 1000.
                  """, default=5000, constraint=lambda x: x >= 1000),
        Parameter('repeat', kind=int,
                  description="""
                  The number of times the tests should be repeated. The default
                  is 1.
                  """, default=1, constraint=lambda x: x > 0)
    ]

    def __init__(self, target, **kwargs):
        super(Jetnews, self).__init__(target, **kwargs)
        self.gui.jank_tests = self.jetnews_jank_tests
        self.gui.uiauto_params['tests'] = self.tests
        self.gui.uiauto_params['flingspeed'] = self.flingspeed
        self.gui.uiauto_params['repeat'] = self.repeat

    def run(self, context):
        # Run the jank tests.
        self.gui.run()

    def update_output(self, context):
        super(Jetnews, self).update_output(context)
        # Parse the frame metrics and output the results file.
        self.gui.parse_metrics(context)
