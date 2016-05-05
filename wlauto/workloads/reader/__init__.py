import os
import logging
import re
import time

from wlauto import AndroidUiAutoBenchmark, Parameter


class Reader(AndroidUiAutoBenchmark):

    activity = 'com.adobe.reader.AdobeReader'
    name = 'reader'
    package = 'com.adobe.reader'
    view = [package+'/com.adobe.reader.help.AROnboardingHelpActivity',
            package+'/com.adobe.reader.viewer.ARSplitPaneActivity',
            package+'/com.adobe.reader.viewer.ARViewerActivity']
    description = """
    A workload to perform standard productivity tasks within Adobe Reader.

    The workload carries out various tasks, such as opening PDF documents,
    scrolling and searching through them, whilst also producing metrics for
    action completion times.
    """

    parameters = [
        Parameter('dumpsys_enabled', kind=bool, default=True,
                  description="""
                  If ``True``, dumpsys captures will be carried out during the
                  test run.  The output is piped to log files which are then
                  pulled from the phone.
                  """),
        Parameter('email', kind=str, default="email@gmail.com",
                  description="""
                  Email account used to register with Adobe online services.
                  """),
        Parameter('password', kind=str, default="password",
                  description="""
                  Password for Adobe online services.
                  """),
    ]

    instrumentation_log = ''.join([name, '_instrumentation.log'])

    def validate(self):
        super(Reader, self).validate()
        self.output_file = os.path.join(self.device.working_directory, self.instrumentation_log)
        self.uiauto_params['package'] = self.package
        self.uiauto_params['output_dir'] = self.device.working_directory
        self.uiauto_params['output_file'] = self.output_file
        self.uiauto_params['email'] = self.email
        self.uiauto_params['password'] = self.password
        self.uiauto_params['dumpsys_enabled'] = self.dumpsys_enabled

    def setup(self, context):
        super(Reader, self).setup(context)

        self.reader_local_dir = self.device.path.join(self.device.external_storage_directory,
                                                      'Android/data/com.adobe.reader/files/')

        for file in os.listdir(self.dependencies_directory):
            if file.endswith(".pdf"):
                self.device.push_file(os.path.join(self.dependencies_directory, file),
                                      os.path.join(self.reader_local_dir, file), timeout=300)

    def update_result(self, context):
        super(Reader, self).update_result(context)

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
        super(Reader, self).teardown(context)
        for file in self.device.listdir(self.reader_local_dir):
            if file.endswith(".pdf"):
                self.device.delete_file(os.path.join(self.reader_local_dir, file))

        for file in self.device.listdir(self.device.working_directory):
            if file.endswith(".log"):
                self.device.pull_file(os.path.join(self.device.working_directory, file), context.output_directory)
                self.device.delete_file(os.path.join(self.device.working_directory, file))
