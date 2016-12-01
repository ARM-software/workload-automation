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


class Gmail(AndroidUxPerfWorkload):

    name = 'gmail'
    package = 'com.google.android.gm'
    min_apk_version = '6.7.128801648'
    activity = ''
    view = [package + '/com.google.android.gm.ConversationListActivityGmail',
            package + '/com.google.android.gm.ComposeActivityGmail']
    description = '''
    A workload to perform standard productivity tasks within Gmail.  The workload carries out
    various tasks, such as creating new emails, attaching images and sending them.

    Test description:
    1. Open Gmail application
    2. Click to create New mail
    3. Attach an image from the local images folder to the email
    4. Enter recipient details in the To field
    5. Enter text in the Subject field
    6. Enter text in the Compose field
    7. Click the Send mail button
    '''

    parameters = [
        Parameter('recipient', kind=str, default='wa-devnull@mailinator.com',
                  description='''
                  The email address of the recipient.  Setting a void address
                  will stop any mesage failures clogging up your device inbox
                  '''),
        Parameter('test_image', kind=str, default='uxperf_1600x1200.jpg',
                  description='''
                  An image to be copied onto the device that will be attached
                  to the email
                  '''),
    ]

    # This workload relies on the internet so check that there is a working
    # internet connection
    requires_network = True

    def __init__(self, device, **kwargs):
        super(Gmail, self).__init__(device, **kwargs)
        self.deployable_assets = [self.test_image]
        self.clean_assets = True

    def validate(self):
        super(Gmail, self).validate()
        self.uiauto_params['recipient'] = self.recipient
        # Only accept certain image formats
        if os.path.splitext(self.test_image.lower())[1] not in ['.jpg', '.jpeg', '.png']:
            raise ValidationError('{} must be a JPEG or PNG file'.format(self.test_image))
