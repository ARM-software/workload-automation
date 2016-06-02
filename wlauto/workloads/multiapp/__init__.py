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

from wlauto import AndroidUiAutoBenchmark, Parameter, File
from wlauto.exceptions import DeviceError
from wlauto.exceptions import NotFoundError

__version__ = '0.1.0'


class Multiapp(AndroidUiAutoBenchmark):

    name = 'multiapp'
    googlephotos_package = 'com.google.android.apps.photos'
    gmail_package = 'com.google.android.gm'
    skype_package = 'com.skype.raider'

    # Set default package and activity
    package = googlephotos_package
    activity = 'com.google.android.apps.photos.home.HomeActivity'

    view = [googlephotos_package + '/com.google.android.apps.photos.home.HomeActivity',
            googlephotos_package + '/com.google.android.apps.photos.localmedia.ui.LocalPhotosActivity',
            googlephotos_package + '/com.google.android.apps.photos.onboarding.AccountPickerActivity',
            googlephotos_package + '/com.google.android.apps.photos.onboarding.IntroActivity',
            googlephotos_package + '/com.google.android.apps.photos/.share.ShareActivity',

            gmail_package + '/com.google.android.gm.ComposeActivityGmail',

            skype_package + '/com.skype.android.app.main.SplashActivity',
            skype_package + '/com.skype.android.app.signin.SignInActivity',
            skype_package + '/com.skype.android.app.signin.UnifiedLandingPageActivity',
            skype_package + '/com.skype.raider/com.skype.android.app.contacts.PickerActivity',
            skype_package + '/com.skype.android.app.chat.ChatActivity']

    instrumentation_log = '{}_instrumentation.log'.format(name)

    description = """
    Workload to test how responsive a device is when context switching between
    appplication tasks. It combines workflows from googlephotos, gmail and
    skype.

    Credentials for the user account used to log into the Skype app have to be provided
    in the agenda, as well as the display name of the contact to call.

    For reliable testing, this workload requires a good and stable internet connection,
    preferably on Wi-Fi.

    NOTE: This workload requires two jpeg files to be placed in the
    dependencies directory to run.

    WARNING: This workload timings are dependent on the time it takes to sync the Gmail.

    Although this workload attempts to be network independent it requires a
    network connection (ideally, wifi) to run. This is because the welcome
    screen UI is dependent on an existing connection.

    Test description:
     1. Two images are copied to the device
     2. Googlephotos is started in offline access mode
     3. The first image is selected and shared with Gmail
     4. Enter recipient details in the To: field
     5. Enter text in the Subject edit box
     6. Enter text in the Compose edit box
     7. Attach the shared image from Googlephotos to the email
     8. Click the Send mail button
     9. Return to Googlephotos and login to Skype via share action
    10. Return to Googlephotos and share the second image with Skype
    11. Select a recipient from the Contacts list
    12. The second image is posted to recipient
    """

    parameters = [
        Parameter('recipient', default='armuxperf@gmail.com', mandatory=False,
                  description=""""
                  The email address of the recipient.  Setting a void address
                  will stop any mesage failures clogging up your device inbox
                  """),
        Parameter('login_name', kind=str, mandatory=True,
                  description='''
                  Skype account to use when logging into the device
                  '''),
        Parameter('login_pass', kind=str, mandatory=True,
                  description='Skype password associated with the account to log into the device'),
        Parameter('contact_name', kind=str, mandatory=True,
                  description='This is the contact display name as it appears in the people list in Skype'),
        Parameter('dumpsys_enabled', kind=bool, default=True,
                  description='''
                  If ``True``, dumpsys captures will be carried out during the test run.
                  The output is piped to log files which are then pulled from the phone.
                  '''),
    ]

    def __init__(self, device, **kwargs):
        super(Multiapp, self).__init__(device, **kwargs)
        self.output_file = os.path.join(self.device.working_directory, self.instrumentation_log)

    def validate(self):
        super(Multiapp, self).validate()

        self.uiauto_params['recipient'] = self.recipient
        self.uiauto_params['dumpsys_enabled'] = self.dumpsys_enabled
        self.uiauto_params['output_dir'] = self.device.working_directory
        self.uiauto_params['my_id'] = self.login_name
        self.uiauto_params['my_pwd'] = self.login_pass
        self.uiauto_params['name'] = self.contact_name.replace(' ', '_')
        self.uiauto_params['output_file'] = self.output_file

    def initialize(self, context):
        super(Multiapp, self).initialize(context)

        # Check for workload dependencies before proceeding
        jpeg_files = [entry for entry in os.listdir(self.dependencies_directory) if entry.endswith(".jpg")]

        if len(jpeg_files) < 4:
            raise NotFoundError("This workload requires a minimum of four {} files in {}".format('jpg',
                                self.dependencies_directory))
        else:
            for entry in jpeg_files:
                self.device.push_file(os.path.join(self.dependencies_directory, entry),
                                      os.path.join(self.device.working_directory, entry),
                                      timeout=300)

        # Force a re-index of the mediaserver cache to pick up new files
        self.device.execute('am broadcast -a android.intent.action.MEDIA_MOUNTED -d file:///sdcard')

    def setup(self, context):
        super(Multiapp, self).setup(context)

        self.launch_main = False

        # Use superclass for setup of gmail dependency
        self.version = 'Gmail'
        self.package = self.gmail_package
        self.logger.info('Checking dependency Gmail')
        super(Multiapp, self).init_resources(context)
        super(Multiapp, self).setup(context)

        # Use superclass for setup of skype dependency
        self.version = 'Skype'
        self.package = self.skype_package
        self.logger.info('Checking dependency Skype')
        super(Multiapp, self).init_resources(context)
        super(Multiapp, self).setup(context)

        # Restore default settings
        self.package = self.googlephotos_package
        self.launch_main = True
        super(Multiapp, self).init_resources(context)

    def update_result(self, context):
        super(Multiapp, self).update_result(context)

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
        super(Multiapp, self).teardown(context)

        # Use superclass for teardown of gmail dependency
        self.package = self.gmail_package
        super(Multiapp, self).teardown(context)

        # Use superclass for teardown of skype dependency
        self.package = self.skype_package
        super(Multiapp, self).teardown(context)

        # Restore default package
        self.package = self.googlephotos_package

        for entry in self.device.listdir(self.device.working_directory):
            if entry.endswith(".log"):
                self.device.pull_file(os.path.join(self.device.working_directory, entry), context.output_directory)
                self.device.delete_file(os.path.join(self.device.working_directory, entry))

    def finalize(self, context):
        super(Multiapp, self).finalize(context)

        for entry in self.device.listdir(self.device.working_directory):
            if entry.endswith(".jpg"):
                self.device.delete_file(os.path.join(self.device.working_directory, entry))

        # Force a re-index of the mediaserver cache to remove cached files
        self.device.execute('am broadcast -a android.intent.action.MEDIA_MOUNTED -d file:///sdcard')
