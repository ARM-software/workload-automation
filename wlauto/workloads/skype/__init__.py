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

from wlauto import AndroidUxPerfWorkload, Parameter


class Skype(AndroidUxPerfWorkload):

    name = 'skype'
    package = 'com.skype.raider'
    min_apk_version = '7.01.0.669'
    activity = ''  # Skype has no default 'main' activity
    view = [package + '/com.skype.android.app.calling.CallActivity',
            package + '/com.skype.android.app.calling.PreCallActivity',
            package + '/com.skype.android.app.chat.ChatActivity',
            package + '/com.skype.android.app.main.HubActivity',
            package + '/com.skype.android.app.main.SplashActivity',
            package + '/com.skype.android.app.signin.SignInActivity',
            package + '/com.skype.android.app.signin.UnifiedLandingPageActivity']
    description = '''
    A workload to perform standard productivity tasks within Skype. The
    workload logs in to the Skype application, selects a recipient from the
    contacts list and then initiates either a voice or video call.

    Test description:

    1. Open Skype application
    2. Log in to a pre-defined account
    3. Select a recipient from the Contacts list
    4. Initiate either a ``voice`` or ``video`` call for ``duration`` time (in seconds)
       Note: The actual duration of the call may not match exactly the intended duration
       due to the uiautomation overhead.

    **Skype Setup**

       - You must have a Skype account set up and its credentials passed
         as parameters into this workload
       - The contact to be called must be added (and has accepted) to the
         account. It's possible to have multiple contacts in the list, however
         the contact to be called *must* be visible on initial navigation to the
         list.
       - For video calls the contact must be able to received the call. This
         means that there must be a Skype client running (somewhere) with the
         contact logged in and that client must have been configured to
         auto-accept calls from the account on the device (how to set this
         varies between different versions of Skype and between platforms --
         please search online for specific instructions).
         https://support.skype.com/en/faq/FA3751/can-i-automatically-answer-all-my-calls-with-video-in-skype-for-windows-desktop
    '''

    launch_main = False  # overrides extended class

    parameters = [
        Parameter('login_name', kind=str, mandatory=True,
                  description='''
                  Account to use when logging into the device from which the call will be made
                  '''),
        Parameter('login_pass', kind=str, mandatory=True,
                  description='Password associated with the account to log into the device'),
        Parameter('contact_name', kind=str, default='Echo / Sound Test Service',
                  description='This is the contact display name as it appears in the people list'),
        Parameter('duration', kind=int, default=10,
                  description='This is the target duration of the call in seconds'),
        Parameter('action', kind=str, allowed_values=['voice', 'video'], default='voice',
                  description='Action to take - either voice call (default) or video'),
    ]

    # This workload relies on the internet so check that there is a working
    # internet connection
    requires_network = True

    def __init__(self, device, **kwargs):
        super(Skype, self).__init__(device, **kwargs)
        self.run_timeout = self.duration + 240

    def validate(self):
        super(Skype, self).validate()
        self.uiauto_params['my_id'] = self.login_name
        self.uiauto_params['my_pwd'] = self.login_pass
        self.uiauto_params['name'] = self.contact_name.replace(' ', '0space0')
        self.uiauto_params['duration'] = self.duration
        self.uiauto_params['action'] = self.action

    def setup(self, context):
        super(Skype, self).setup(context)
        self.device.execute('am start -W -a android.intent.action.VIEW -d skype:dummy?dummy')
