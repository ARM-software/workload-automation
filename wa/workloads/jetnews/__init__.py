#    Copyright 2023 ARM Limited
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

from wa import ApkWorkload, Parameter
from wa.utils.types import list_or_string


class JetNews(ApkWorkload):
    name = 'jetnews'

    description = '''
    JetNews-based benchmarks for UI performance measurement.
    '''

    package_names = ['com.example.jetnews']

    # All the supported test types that can be executed for this workload.
    all_test_types = ['ScrollArticleTest',
                      'ScrollArticleSlowlyTest',
                      'UserSimulationTest']

    # All the available parameters for this workload.
    parameters = [
        Parameter('tests',
                  kind=list_or_string,
                  default=all_test_types,
                  allowed_values=all_test_types,
                  description='''
                  Select the type of test to run:

                      - ScrollArticleTest
                      - ScrollArticleSlowlyTest
                      - UserSimulationTest

                  By default all the tests are executed.
                  '''),
        Parameter('iterations',
                  kind=int,
                  default=1,
                  constraint=lambda x: x > 0,
                  description='''
                  Specifies the number of times the benchmark will be run in a "tight loop",
                  i.e. without performing setup/teardown in between.

                  The default is 1 iteration.
                  ''')
    ]

    def run(self, context):
        super().run(context)

        # Invoke each test one after the other.
        # These tests are part of a separate apk that interacts with the main
        # JetNews app.
        for iteration in range(self.iterations):  # pylint: disable=W0612
            for test in self.tests:
                command = f'am instrument -w -e class com.arm.test. {test} com.arm.benchmark/androidx.test.runner.AndroidJUnitRunner'
                self.target.execute(command)
