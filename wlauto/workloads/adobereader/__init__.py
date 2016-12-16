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

from wlauto import AndroidUxPerfWorkload, Parameter
from wlauto.exceptions import ValidationError
from wlauto.utils.types import list_of_strings


class AdobeReader(AndroidUxPerfWorkload):

    name = 'adobereader'
    package = 'com.adobe.reader'
    min_apk_version = '16.1'
    activity = 'com.adobe.reader.AdobeReader'
    view = [package + '/com.adobe.reader.help.AROnboardingHelpActivity',
            package + '/com.adobe.reader.viewer.ARSplitPaneActivity',
            package + '/com.adobe.reader.viewer.ARViewerActivity']
    description = '''
    The Adobe Reader workflow carries out the following typical productivity tasks.

    Test description:

    1. Open a local file on the device
    2. Gestures test:
        2.1. Swipe down across the central 50% of the screen in 200 x 5ms steps
        2.2. Swipe up across the central 50% of the screen in 200 x 5ms steps
        2.3. Swipe right from the edge of the screen in 50 x 5ms steps
        2.4. Swipe left from the edge of the screen  in 50 x 5ms steps
        2.5. Pinch out 50% in 100 x 5ms steps
        2.6. Pinch In 50% in 100 x 5ms steps
    3. Search test:
        Search ``document_name`` for each string in the ``search_string_list``
    4. Close the document
    '''

    default_search_strings = [
        'The quick brown fox jumps over the lazy dog',
        'TEST_SEARCH_STRING',
    ]

    parameters = [
        Parameter('document_name', kind=str, default="uxperf_test_doc.pdf",
                  description='''
                  The document name to use for the Gesture and Search test.
                  '''),
        Parameter('search_string_list', kind=list_of_strings, default=default_search_strings,
                  constraint=lambda x: len(x) > 0,
                  description='''
                  For each string in the list, a document search is performed
                  using the string as the search term. At least one must be
                  provided.
                  '''),
    ]

    def __init__(self, device, **kwargs):
        super(AdobeReader, self).__init__(device, **kwargs)
        self.deployable_assets = [self.document_name]
        # Adobe only looks for local files in a specific path
        self.adobe_path = self.device.path.join(self.device.external_storage_directory,
                                                'Android', 'data', 'com.adobe.reader', 'files')

    def validate(self):
        super(AdobeReader, self).validate()
        self.uiauto_params['filename'] = self.document_name.replace(' ', '0space0')
        self.uiauto_params['search_string_list'] = '0newline0'.join([x.replace(' ', '0space0') for x in self.search_string_list])
        # Only accept certain file formats
        if os.path.splitext(self.document_name.lower())[1] not in ['.pdf']:
            raise ValidationError('{} must be a PDF file'.format(self.document_name))

    def setup(self, context):
        super(AdobeReader, self).setup(context)
        # Create the adobe path if it doesnt exist yet, and move the asset to this location
        self.device.execute('mkdir -p {}'.format(self.adobe_path))
        self.device.execute('mv {0}/{1} {2}/{1}'.format(self.device.working_directory, self.document_name, self.adobe_path))

    def teardown(self, context):
        super(AdobeReader, self).teardown(context)
        # Remove the asset from the adobe location
        self.device.execute('rm -rf {0}/{1}'.format(self.adobe_path, self.document_name))
