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
import re

from wlauto import AndroidUiAutoBenchmark, Parameter
from wlauto.exceptions import DeviceError

__version__ = '0.1.0'


class Googleplaybooks(AndroidUiAutoBenchmark):

    name = 'googleplaybooks'
    package = 'com.google.android.apps.books'
    activity = 'com.google.android.apps.books.app.BooksActivity'
    view = [package + '/com.google.android.apps.books.app.HomeActivity',
            package + '/com.android.vending/com.google.android.finsky.activities.MainActivity',
            package + '/com.google.android.apps.books.app.ReadingActivity',
            package + '/com.google.android.apps.books.app.TableOfContentsActivityLight']
    description = """
    A workload to perform standard productivity tasks with googleplaybooks.
    This workload performs various tasks, such as searching for a book title
    online, browsing through a book, adding and removing notes, word searching,
    and querying information about the book.

    Test description:
    1. Open Google Play Books application
    2. Dismisses sync operation (if applicable)
    3. Searches for a book title
    4. Gestures are performed to swipe between pages and pinch zoom in and out of a page
    5. Selects a random chapter from the navigation view
    6. Selects a word in the centre of screen and adds a test note to the page
    7. Removes the test note from the page (clean up)
    8. Searches for the number of occurrences of a common word throughout the book
    9. Uses the 'About this book' facility on the currently selected book

    NOTE: This workload requires a network connection (ideally, wifi) to run.
    """

    parameters = [
        Parameter('search_book_title', kind=str, mandatory=False, default='Shakespeare',
                  description="""
                  The book title to search for within Google Play Books archive.
                  Note: spaces must be replaced with underscores in the book title.
                  """),
        Parameter('search_word', kind=str, mandatory=False, default='the',
                  description="""
                  The word to search for within a selected book.
                  Note: Accepts single words only.
                  """),
        Parameter('dumpsys_enabled', kind=bool, default=True,
                  description="""
                  If ``True``, dumpsys captures will be carried out during the
                  test run.  The output is piped to log files which are then
                  pulled from the phone.
                  """),
    ]

    instrumentation_log = ''.join([name, '_instrumentation.log'])

    def __init__(self, device, **kwargs):
        super(Googleplaybooks, self).__init__(device, **kwargs)
        self.output_file = os.path.join(self.device.working_directory, self.instrumentation_log)

    def validate(self):
        super(Googleplaybooks, self).validate()
        self.uiauto_params['package'] = self.package
        self.uiauto_params['output_dir'] = self.device.working_directory
        self.uiauto_params['output_file'] = self.output_file
        self.uiauto_params['dumpsys_enabled'] = self.dumpsys_enabled
        self.uiauto_params['book_title'] = self.search_book_title
        self.uiauto_params['search_word'] = self.search_word

    def initialize(self, context):
        super(Googleplaybooks, self).initialize(context)

        if not self.device.is_network_connected():
            raise DeviceError('Network is not connected for device {}'.format(self.device.name))

    def update_result(self, context):
        super(Googleplaybooks, self).update_result(context)

        self.device.pull_file(self.output_file, context.output_directory)
        result_file = os.path.join(context.output_directory, self.instrumentation_log)

        with open(result_file, 'r') as wfh:
            pattern = r'(?P<key>\w+)\s+(?P<value1>\d+)\s+(?P<value2>\d+)\s+(?P<value3>\d+)'
            regex = re.compile(pattern)
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
        super(Googleplaybooks, self).teardown(context)

        for entry in self.device.listdir(self.device.working_directory):
            if entry.endswith(".log"):
                self.device.pull_file(os.path.join(self.device.working_directory, entry),
                                      context.output_directory)
                self.device.delete_file(os.path.join(self.device.working_directory, entry))
