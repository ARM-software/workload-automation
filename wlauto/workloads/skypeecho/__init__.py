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
import time

from wlauto import AndroidUiAutoBenchmark, Parameter


SKYPE_ACTION_URIS = {
    'call': 'call',
    'video': 'call&video=true',
}


class SkypeEcho(AndroidUiAutoBenchmark):

    name = 'skypeecho'
    description = 'Workload that makes a Skype test call'
    package = 'com.skype.raider'
    activity = ''
    # Skype has no default 'main' activity
    launch_main = False # overrides extended class

    instrumentation_log = '{}_instrumentation.log'.format(name)

    parameters = [
        # Workload parameters go here e.g.
        # Parameter('example_parameter', kind=int, allowed_values=[1,2,3], default=1, override=True, mandatory=False,
        #           description='This is an example parameter')
        Parameter('login_name', kind=str, mandatory=True,
                  description='''
                  Account to use when logging into the device from which the call will be made
                  '''),
        Parameter('login_pass', kind=str, mandatory=True,
                  description='Password associated with the account to log into the device'),
        Parameter('contact_skypeid', kind=str, mandatory=True,
                  description='This is the Skype ID of the contact to call from the device'),
        Parameter('contact_name', kind=str, mandatory=True,
                  description='This is the contact display name as it appears in the people list'),
        Parameter('duration', kind=int, default=60,
                  description='This is the duration of the call in seconds'),
        Parameter('action', kind=str, allowed_values=['voice', 'video'], default='voice',
                  description='Action to take - either voice (default) or video call'),
        Parameter('use_gui', kind=bool, default=True,
                  description='Specifies whether to use GUI or direct Skype URI'),
    ]

    def __init__(self, device, **kwargs):
        super(SkypeEcho, self).__init__(device, **kwargs)
        self.output_file = os.path.join(self.device.working_directory, self.instrumentation_log)
        self.uiauto_params['results_file'] = self.output_file
        if self.use_gui:
            self.uiauto_params['my_id'] = self.login_name
            self.uiauto_params['my_pwd'] = self.login_pass
            self.uiauto_params['skypeid'] = self.contact_skypeid
            self.uiauto_params['name'] = self.contact_name.replace(' ', '_')
            self.uiauto_params['duration'] = self.duration
            self.uiauto_params['action'] = self.action
        self.run_timeout = self.duration + 30

    def setup(self, context):
        self.logger.info('===== setup() ======')
        if self.use_gui:
            super(SkypeEcho, self).setup(context)
            self.device.execute('am force-stop {}'.format(self.package))
            self.device.execute('am start -W -a android.intent.action.VIEW -d skype:dummy?dummy')
            time.sleep(1)
        else:
            self.device.execute('am force-stop {}'.format(self.package))

    def run(self, context):
        self.logger.info('===== run() ======')
        if self.use_gui:
            super(SkypeEcho, self).run(context)
        else:
            data_uri = 'skype:{}?{}'.format(self.contact_skypeid, SKYPE_ACTION_URIS[self.action])
            command = 'am start -W -a android.intent.action.VIEW -d "{}"'.format(data_uri)
            self.logger.debug(self.device.execute(command))
            self.logger.debug('Call started; waiting for {} seconds...'.format(self.duration))
            time.sleep(self.duration)
            self.device.execute('am force-stop {}'.format(self.package))

    def update_result(self, context):
        self.logger.info('===== update_result() ======')
        super(SkypeEcho, self).update_result(context)
        # if not self.dumpsys_enabled:
        #     return

        self.device.pull_file(self.output_file, context.output_directory)
        results_file = os.path.join(context.output_directory, self.instrumentation_log)

        # process results and add them using
        # context.result.add_metric
        with open(results_file, 'r') as lines:
            pattern = r'(?P<key>\w+)\s+(?P<value1>\d+)\s+(?P<value2>\d+)\s+(?P<value3>\d+)'
            regex = re.compile(pattern)
            for line in lines:
                match = regex.search(line)
                if match:
                    context.result.add_metric((match.group('key') + "_start"), match.group('value1'))
                    context.result.add_metric((match.group('key') + "_finish"), match.group('value2'))
                    context.result.add_metric((match.group('key') + "_duration"), match.group('value3'))

    def teardown(self, context):
        self.logger.info('===== teardown() ======')
        super(SkypeEcho, self).teardown(context)
        # Pull log files
        for entry in self.device.listdir(self.device.working_directory):
            if entry.startswith(self.name) and entry.endswith(".log"):
                self.device.pull_file(os.path.join(self.device.working_directory, entry),
                                      context.output_directory)
                self.device.delete_file(os.path.join(self.device.working_directory, entry))
        # self.device.execute('am force-stop {}'.format(self.package))
