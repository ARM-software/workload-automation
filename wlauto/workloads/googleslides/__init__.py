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
import os.path as path
import re
from wlauto import AndroidUiAutoBenchmark, Parameter


def not_implemented(workload, text):
    workload.logger.info('## ++ NOT IMPLEMENTED ++ ##\n## {}\n## -- NOT IMPLEMENTED -- ##'.format(text))

def log_method(workload, name):
    workload.logger.info('===== {}() ======'.format(name))

class GoogleSlides(AndroidUiAutoBenchmark):

    name = 'googleslides'
    package = 'com.google.android.apps.docs.editors.slides'
    description = 'Creates a Google Slides presentation with some commonly used features'
    activity = ''

    # Views for FPS instrumentation
    view = [
        "com.google.android.apps.docs.editors.slides/com.google.android.apps.docs.app.DocListActivity",
        "com.google.android.apps.docs.editors.slides/com.google.android.apps.docs.welcome.warmwelcome.TrackingWelcomeActivity",
    ]

    parameters = [
        Parameter('dumpsys_enabled', kind=bool, default=True,
                  description='''
                  If ``True``, dumpsys captures will be carried out during the test run.
                  The output is piped to log files which are then pulled from the phone.
                  '''),
        Parameter('local_files', kind=bool, default=True,
                  description='''
                  If ``True``, the workload will push PowerPoint files to be used for testing on
                  the device. Otherwise, the files will be created from template inside the app.
                  '''),
    ]

    instrumentation_log = '{}_instrumentation.log'.format(name)
    file_prefix = 'wa_test_'
    local_dir = '.' # self.dependencies_directory
    device_dir = '/sdcard/Download' # self.device.working_directory

    def __init__(self, device, **kwargs):
        super(GoogleSlides, self).__init__(device, **kwargs)
        self.output_file = path.join(self.device.working_directory, self.instrumentation_log)
        self.run_timeout = 60

    def validate(self):
        log_method(self, 'validate')
        super(GoogleSlides, self).validate()
        self.uiauto_params['dumpsys_enabled'] = self.dumpsys_enabled
        self.uiauto_params['output_dir'] = self.device.working_directory
        self.uiauto_params['results_file'] = self.output_file

    def initialize(self, context):
        log_method(self, 'initialize')
        super(GoogleSlides, self).initialize(context)
        if self.local_files:
            # push local PPT files
            for entry in os.listdir(self.local_dir):
                wa_file = self.file_prefix + entry
                if entry.endswith(".pptx"):
                    self.device.push_file(path.join(self.local_dir, entry),
                                          path.join(self.device_dir, wa_file),
                                          timeout=60)
            # Force a re-index of the mediaserver cache to pick up new files
            self.device.execute('am broadcast -a android.intent.action.MEDIA_MOUNTED -d file:///sdcard')

    def setup(self, context):
        log_method(self, 'setup')
        super(GoogleSlides, self).setup(context)

    def run(self, context):
        log_method(self, 'run')
        super(GoogleSlides, self).run(context)

    def update_result(self, context):
        log_method(self, 'update_result')
        super(GoogleSlides, self).update_result(context)
        if self.dumpsys_enabled:
            not_implemented(self, 'get_metrics(context)')

    def teardown(self, context):
        log_method(self, 'teardown')
        super(GoogleSlides, self).teardown(context)
        not_implemented(self, 'pull_logs(context)')

    def finalize(self, context):
        log_method(self, 'finalize')
        super(GoogleSlides, self).finalize(context)
        if self.local_files:
            # delete pushed PPT files
            for entry in os.listdir(self.local_dir):
                wa_file = self.file_prefix + entry
                if entry.endswith(".pptx"):
                    self.device.delete_file(path.join(self.device_dir, wa_file))
            # Force a re-index of the mediaserver cache to pick up new files
            self.device.execute('am broadcast -a android.intent.action.MEDIA_MOUNTED -d file:///sdcard')

    def get_metrics(self, context):
        self.device.pull_file(self.output_file, context.output_directory)
        metrics_file = path.join(context.output_directory, self.instrumentation_log)
        with open(metrics_file, 'r') as wfh:
            regex = re.compile(r'(\w+)\s+(\d+)\s+(\d+)\s+(\d+)')
            for line in wfh:
                match = regex.search(line)
                if match:
                    context.result.add_metric((match.group(1) + '_start'), match.group(2))
                    context.result.add_metric((match.group(1) + '_finish'), match.group(3))
                    context.result.add_metric((match.group(1) + '_duration'), match.group(4))

    def pull_logs(self, context):
        wd = self.device.working_directory
        for entry in self.device.listdir(wd):
            if entry.startswith(self.name) and entry.endswith('.log'):
                self.device.pull_file(path.join(wd, entry), context.output_directory)
                self.device.delete_file(path.join(wd, entry))
