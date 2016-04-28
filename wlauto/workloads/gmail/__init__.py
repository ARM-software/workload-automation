import os
import logging
import re
import time

from wlauto import AndroidUiAutoBenchmark, Parameter


class Gmail(AndroidUiAutoBenchmark):

    name = 'gmail'
    package = 'com.google.android.gm'
    activity = ''
    view = [package+'/com.google.android.gm.ConversationListActivityGmail',
            package+'/com.google.android.gm.ComposeActivityGmail']
    description = """
    A workload to perform standard productivity tasks within Gmail.

    The workload carries out various tasks, such as creatign new emails and
    sending them, whilst also producing metrics for action completion times.
    """

    regex = re.compile(r'uxperf_gmail.*: (?P<key>\w+) (?P<value>\d+)')

    parameters = [
        Parameter('recipient', default='armuxperf@gmail.com', mandatory=False,
                  description=""""
                  The email address of the recipient.  Setting a void address
                  will stop any mesage failures clogging up your device inbox
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
        super(Gmail, self).__init__(device, **kwargs)
        self.uiauto_params['recipient'] = self.recipient

    def setup(self, context):
        super(Gmail, self).setup(context)

        self.camera_dir = self.device.path.join(self.device.external_storage_directory,
                                                      'DCIM/Camera/')

        for file in os.listdir(self.dependencies_directory):
            if file.endswith(".jpg"):
                self.device.push_file(os.path.join(self.dependencies_directory, file),
                                      os.path.join(self.camera_dir, file), timeout=300)

        # Force a re-index of the mediaserver cache to pick up new files
        self.device.execute('am broadcast -a android.intent.action.MEDIA_MOUNTED -d file:///sdcard')

    def validate(self):
        super(Gmail, self).validate()
        self.output_file = os.path.join(self.device.working_directory, self.instrumentation_log)
        self.uiauto_params['package'] = self.package
        self.uiauto_params['output_dir'] = self.device.working_directory
        self.uiauto_params['output_file'] = self.output_file
        self.uiauto_params['dumpsys_enabled'] = self.dumpsys_enabled

    def update_result(self, context):
        super(Gmail, self).update_result(context)

        if self.dumpsys_enabled:
            self.device.pull_file(self.output_file, context.output_directory)
            result_file = os.path.join(context.output_directory, self.instrumentation_log)

            with open(result_file, 'r') as wfh:
                regex = re.compile(r'(?P<key>\w+)\s+(?P<value1>\d+)\s+(?P<value2>\d+)\s+(?P<value3>\d+)')
                for line in wfh:
                    match = regex.search(line)
                    if match:
                        context.result.add_metric((match.group('key') + "_start"),
                                                  match.group('value1'))
                        context.result.add_metric((match.group('key') + "_finish"),
                                                  match.group('value2'))
                        context.result.add_metric((match.group('key') + "_duration"),
                                                  match.group('value3'))

    def teardown(self, context):
        super(Gmail, self).teardown(context)

        for file in self.device.listdir(self.device.working_directory):
            if file.startswith (self.name) and file.endswith(".log"):
                self.device.pull_file(os.path.join(self.device.working_directory, file), context.output_directory)
                self.device.delete_file(os.path.join(self.device.working_directory, file))
