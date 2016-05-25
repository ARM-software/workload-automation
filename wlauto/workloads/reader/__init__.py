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

import os
import logging
import re
import time

from wlauto import AndroidUiAutoBenchmark, Parameter
from wlauto.exceptions import DeviceError

__version__ = '0.1.0'


class Reader(AndroidUiAutoBenchmark):

    activity = 'com.adobe.reader.AdobeReader'
    name = 'reader'
    package = 'com.adobe.reader'
    view = [package+'/com.adobe.reader.help.AROnboardingHelpActivity',
            package+'/com.adobe.reader.viewer.ARSplitPaneActivity',
            package+'/com.adobe.reader.viewer.ARViewerActivity']
    description = """
    The Adobe Reader workflow carries out the following typical productivity tasks using
    Workload-Automation.

    Test description:

    1. Open the application and sign in to an Adobe Cloud account over wifi
    2. Select the local files browser list - a test measuring the time taken to navigate through the
       menus and for the list to be created.
    3. Search for a specific file from within the - a test measuring the entry of a search string
       and time taken to locate the document within the file list.
    4. Open the selected file - a test measuring the time taken to open the document and present
       within a new view.
    5. Gestures test - measurement of fps, jank and other frame statistics, via dumpsys, for swipe
       and pinch gestures.
    6. Search test - a test measuring the time taken to search a large 100+ page mixed content
       document for specific strings.  Steps 2-4 are repeated to open the Cortex M4 manual.
    """

    parameters = [
        Parameter('dumpsys_enabled', kind=bool, default=True,
                  description="""
                  If ``True``, dumpsys captures will be carried out during the
                  test run.  The output is piped to log files which are then
                  pulled from the phone.
                  """),
        Parameter('email', kind=str, default="email@gmail.com",
                  description="""
                  Email account used to register with Adobe online services.
                  """),
        Parameter('password', kind=str, default="password",
                  description="""
                  Password for Adobe online services.
                  """),
    ]

    instrumentation_log = ''.join([name, '_instrumentation.log'])

    def validate(self):
        super(Reader, self).validate()
        self.output_file = os.path.join(self.device.working_directory, self.instrumentation_log)
        self.uiauto_params['package'] = self.package
        self.uiauto_params['output_dir'] = self.device.working_directory
        self.uiauto_params['output_file'] = self.output_file
        self.uiauto_params['email'] = self.email
        self.uiauto_params['password'] = self.password
        self.uiauto_params['dumpsys_enabled'] = self.dumpsys_enabled

    def initialize(self, context):
        super(Reader, self).initialize(context)

        if not self.device.is_wifi_connected():
            raise DeviceError('Wifi is not connected for device {}'.format(self.device.name))

    def setup(self, context):
        super(Reader, self).setup(context)

        self.reader_local_dir = self.device.path.join(self.device.external_storage_directory,
                                                      'Android/data/com.adobe.reader/files/')

        for file in os.listdir(self.dependencies_directory):
            if file.endswith(".pdf"):
                self.device.push_file(os.path.join(self.dependencies_directory, file),
                                      os.path.join(self.reader_local_dir, file), timeout=300)

    def update_result(self, context):
        super(Reader, self).update_result(context)

        self.device.pull_file(self.output_file, context.output_directory)
        result_file = os.path.join(context.output_directory, self.instrumentation_log)

        with open(result_file, 'r') as wfh:
            regex = re.compile(r'(?P<key>\w+)\s+(?P<value1>\d+)\s+(?P<value2>\d+)\s+(?P<value3>\d+)')
            for line in wfh:
                match = regex.search(line)
                if match:
                    context.result.add_metric((match.group('key') + "_start"),
                                              match.group('value1'), units='ms')
                    context.result.add_metric((match.group('key') + "_finish"),
                                              match.group('value2'), units='ms')
                    context.result.add_metric((match.group('key') + "_duration"),
                                              match.group('value3'), units='ms')

    def teardown(self, context):
        super(Reader, self).teardown(context)
        for file in self.device.listdir(self.reader_local_dir):
            if file.endswith(".pdf"):
                self.device.delete_file(os.path.join(self.reader_local_dir, file))

        for file in self.device.listdir(self.device.working_directory):
            if file.endswith(".log"):
                self.device.pull_file(os.path.join(self.device.working_directory, file), context.output_directory)
                self.device.delete_file(os.path.join(self.device.working_directory, file))
