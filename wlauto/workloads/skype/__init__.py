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

import os.path as op
import re
import time

from wlauto import AndroidUiAutoBenchmark, Parameter


SKYPE_ACTION_URIS = {
    'call': 'call',
    'video': 'call&video=true',
}


class Skype(AndroidUiAutoBenchmark):

    name = 'skype'
    description = '''
    A workload to perform standard productivity tasks within Skype.  The workload logs in to the
    Skype application, selects a recipient from the contacts list and then initiates a 5 second
    call.

    Test description:
    
    1. Open Skype application
    2. Log in to a pre-defined account
    3. Select a recipient from the Contacts list
    4. Initiate a 5 second video Call
    '''
    package = 'com.skype.raider'
    view = [package+'/com.skype.android.app.calling.CallActivity',
            package+'/com.skype.android.app.calling.PreCallActivity',
            package+'/com.skype.android.app.chat.ChatActivity',
            package+'/com.skype.android.app.main.HubActivity',
            package+'/com.skype.android.app.main.SplashActivity',
            package+'/com.skype.android.app.signin.SignInActivity',
            package+'/com.skype.android.app.signin.UnifiedLandingPageActivity']
    activity = ''
    # Skype has no default 'main' activity
    launch_main = False # overrides extended class

    instrumentation_log = '{}_instrumentation.log'.format(name)

    parameters = [
        Parameter('login_name', kind=str, mandatory=True,
                  description='''
                  Account to use when logging into the device from which the call will be made
                  '''),
        Parameter('login_pass', kind=str, mandatory=True,
                  description='Password associated with the account to log into the device'),
        Parameter('contact_name', kind=str, mandatory=True,
                  description='This is the contact display name as it appears in the people list'),
        Parameter('duration', kind=int, default=60,
                  description='This is the duration of the call in seconds'),
        Parameter('action', kind=str, allowed_values=['voice', 'video'], default='video',
                  description='Action to take - either video (default) or voice call'),
        Parameter('dumpsys_enabled', kind=bool, default=True,
                  description='''
                  If ``True``, dumpsys captures will be carried out during the test run.
                  The output is piped to log files which are then pulled from the phone.
                  '''),
    ]

    def __init__(self, device, **kwargs):
        super(Skype, self).__init__(device, **kwargs)
        self.output_file = op.join(self.device.working_directory, self.instrumentation_log)
        self.run_timeout = self.duration + 60

    def validate(self):
        super(Skype, self).validate()
        self.uiauto_params['results_file'] = self.output_file
        self.uiauto_params['dumpsys_enabled'] = self.dumpsys_enabled
        self.uiauto_params['output_dir'] = self.device.working_directory
        self.uiauto_params['my_id'] = self.login_name
        self.uiauto_params['my_pwd'] = self.login_pass
        self.uiauto_params['name'] = self.contact_name.replace(' ', '_')
        self.uiauto_params['duration'] = self.duration
        self.uiauto_params['action'] = self.action

    def setup(self, context):
        self.logger.info('===== setup() ======')
        super(Skype, self).setup(context)
        self.device.execute('am force-stop {}'.format(self.package))
        self.device.execute('am start -W -a android.intent.action.VIEW -d skype:dummy?dummy')
        time.sleep(1)

    def run(self, context):
        self.logger.info('===== run() ======')
        super(Skype, self).run(context)

    def update_result(self, context):
        self.logger.info('===== update_result() ======')
        super(Skype, self).update_result(context)

        self.device.pull_file(self.output_file, context.output_directory)
        results_file = op.join(context.output_directory, self.instrumentation_log)

        # process results and add them using
        # context.result.add_metric
        self.device.pull_file(self.output_file, context.output_directory)
        result_file = op.join(context.output_directory, self.instrumentation_log)

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
        self.logger.info('===== teardown() ======')
        super(Skype, self).teardown(context)
        # Pull log files
        wd = self.device.working_directory
        for entry in self.device.listdir(wd):
            if entry.startswith(self.name) and entry.endswith(".log"):
                self.device.pull_file(op.join(wd, entry), context.output_directory)
                self.device.delete_file(op.join(wd, entry))
