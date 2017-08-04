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

from wlauto import AndroidUxPerfWorkload, Parameter, ExtensionLoader
from wlauto import AndroidUiAutoBenchmark, UiAutomatorWorkload
from wlauto.exceptions import ValidationError


class AppShare(AndroidUxPerfWorkload):

    name = 'appshare'
    package = []
    activity = None
    view = []
    description = '''
    Workload to test how responsive a device is when context switching between
    application tasks. It combines workflows from googlephotos, gmail and
    skype.

    ** Setup **
    Credentials for the user account used to log into the Skype app have to be provided
    in the agenda, as well as the display name of the contact to call.

    For reliable testing, this workload requires a good and stable internet connection,
    preferably on Wi-Fi.

    Although this workload attempts to be network independent it requires a
    network connection (ideally, wifi) to run. This is because the welcome
    screen UI is dependent on an existing connection.

    Test description:

    1. GooglePhotos is started in offline access mode
        1.1. The welcome screen is dismissed
        1.2. Any promotion popup is dismissed
        1.3. The provided ``test_image`` is selected and displayed
    2. The image is then shared across apps to Gmail
        2.1. The first run dialogue is dismissed
        2.2. Enter recipient details in the To field
        2.3. Enter text in the Subject field
        2.4. Enter text in the Body field
        2.5. Click the Send mail button
    3. Return to Googlephotos and login to Skype via share action
    4. Return to Googlephotos and share the ``test_image`` with Skype
        4.1. Search for the ``skype_contact_name`` from the Contacts list
        4.2. Dismiss any update popup that appears
        4.3. The image is posted in the Chat
    '''

    parameters = [
        Parameter('test_image', kind=str, default='uxperf_1600x1200.jpg',
                  description='''
                  An image to be copied onto the device that will be shared
                  across multiple apps
                  '''),
        Parameter('email_recipient', kind=str, default='wa-devnull@mailinator.com',
                  description='''
                  The email address of the recipient to recieve the shared image
                  '''),
        Parameter('skype_login_name', kind=str, mandatory=True,
                  description='''
                  Account to use when logging into skype from which to share the image
                  '''),
        Parameter('skype_login_pass', kind=str, mandatory=True,
                  description='''
                  Password associated with the skype account
                  '''),
        Parameter('skype_contact_name', kind=str, default='Echo / Sound Test Service',
                  description='''
                  This is the contact display name as it appears in the people list
                  '''),
    ]

    # This workload relies on the internet so check that there is a working
    # internet connection
    requires_network = True

    def __init__(self, device, **kwargs):
        super(AppShare, self).__init__(device, **kwargs)
        self.deployable_assets = [self.test_image]
        self.clean_assets = True
        loader = ExtensionLoader()

        # Initialise googlephotos
        args_googlephotos = dict(kwargs)
        del args_googlephotos['test_image']
        del args_googlephotos['email_recipient']
        del args_googlephotos['skype_login_name']
        del args_googlephotos['skype_login_pass']
        del args_googlephotos['skype_contact_name']
        args_googlephotos['markers_enabled'] = False
        self.wl_googlephotos = loader.get_workload('googlephotos', device, **args_googlephotos)
        self.view += self.wl_googlephotos.view
        self.package.append(self.wl_googlephotos.package)

        # Initialise gmail
        args_gmail = dict(kwargs)
        del args_gmail['test_image']
        args_gmail['recipient'] = args_gmail.pop('email_recipient')
        del args_gmail['skype_login_name']
        del args_gmail['skype_login_pass']
        del args_gmail['skype_contact_name']
        args_gmail['markers_enabled'] = False
        self.wl_gmail = loader.get_workload('gmail', device, **args_gmail)
        self.view += self.wl_gmail.view
        self.package.append(self.wl_gmail.package)

        # Initialise skype
        args_skype = dict(kwargs)
        del args_skype['test_image']
        del args_skype['email_recipient']
        args_skype['login_name'] = args_skype.pop('skype_login_name')
        args_skype['login_pass'] = args_skype.pop('skype_login_pass')
        args_skype['contact_name'] = args_skype.pop('skype_contact_name')
        args_skype['markers_enabled'] = False
        self.wl_skype = loader.get_workload('skype', device, **args_skype)
        self.view += self.wl_skype.view
        self.package.append(self.wl_skype.package)

    def validate(self):
        super(AppShare, self).validate()
        # Set package to None as it doesnt allow it to be a list,
        # and we are not using it in the java side, only in wa itself.
        self.uiauto_params['package_name'] = None
        self.uiauto_params['googlephotos_package'] = self.wl_googlephotos.package
        self.uiauto_params['gmail_package'] = self.wl_gmail.package
        self.uiauto_params['skype_package'] = self.wl_skype.package
        self.uiauto_params['recipient'] = self.email_recipient
        self.uiauto_params['my_id'] = self.skype_login_name
        self.uiauto_params['my_pwd'] = self.skype_login_pass
        self.uiauto_params['name'] = self.skype_contact_name
        # Only accept certain image formats
        if os.path.splitext(self.test_image.lower())[1] not in ['.jpg', '.jpeg', '.png']:
            raise ValidationError('{} must be a JPEG or PNG file'.format(self.test_image))

    def setup(self, context):
        self.logger.info('Checking dependency Skype')
        self.wl_skype.launch_main = False
        self.wl_skype.deployable_assets = []
        self.wl_skype.init_resources(context)
        # Bypass running skype through intent
        AndroidUxPerfWorkload.setup(self.wl_skype, context)

        self.logger.info('Checking dependency Gmail')
        self.wl_gmail.launch_main = False
        self.wl_gmail.deployable_assets = []
        self.wl_gmail.init_resources(context)
        self.wl_gmail.setup(context)

        self.logger.info('Checking dependency Googlephotos')
        self.wl_googlephotos.launch_main = True
        self.wl_googlephotos.deployable_assets = []
        self.wl_googlephotos.init_resources(context)
        # Bypass googlephoto's asset setup
        AndroidUxPerfWorkload.setup(self.wl_googlephotos, context)

        self.logger.info('Checking dependency AppShare')
        super(AppShare, self).init_resources(context)
        # Only setup uiautomator side, then push assets
        # This prevents the requirement that AppShare must have an APK
        UiAutomatorWorkload.setup(self, context)
        self.push_assets(context)

    def teardown(self, context):
        self.wl_skype.teardown(context)
        self.wl_gmail.teardown(context)
        # Bypass googlephoto's asset teardown
        AndroidUxPerfWorkload.teardown(self.wl_googlephotos, context)

        super(AppShare, self).teardown(context)
