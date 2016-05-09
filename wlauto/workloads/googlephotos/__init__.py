import os
import re

from wlauto import AndroidUiAutoBenchmark, Parameter


class Googlephotos(AndroidUiAutoBenchmark):

    name = 'googlephotos'
    package = 'com.google.android.apps.photos'
    activity = 'com.google.android.apps.photos.home.HomeActivity'

    description = """
    A workload to perform standard productivity tasks with googlephotos.

    The workload carries out various tasks, such as browsing images, performing
    zooms, post-processing and saving a selected image to file.

    gesture test - browsing through the wa-working gallery using swipe
                   gestures and performing pinch gestures for zooming
    color test   - selects a photograph, increments, resets and decrements color balance
    crop test    - uses image straightener facility to simultaneously rotate and
                   crop a selected photograph
    rotate tests - selects a photograph and performs 90 degree rotations

    NOTE: This workload requires four jpeg files to be placed in the
    dependencies directory to run.

    Although this workload attempts to be network independent it requires a
    network connection (ideally, wifi) to run. This is because the welcome
    screen UI is dependent on an existing connection.
    """

    parameters = [
        Parameter('dumpsys_enabled', kind=bool, default=True,
                  description="""
                  If ``True``, dumpsys captures will be carried out during the
                  test run.  The output is piped to log files which are then
                  pulled from the phone.
                  """),
    ]

    instrumentation_log = ''.join([name, '_instrumentation.log'])
    file_prefix = 'wa_test_'

    def __init__(self, device, **kwargs):
        super(Googlephotos, self).__init__(device, **kwargs)
        self.output_file = os.path.join(self.device.working_directory, self.instrumentation_log)

    def validate(self):
        super(Googlephotos, self).validate()
        self.uiauto_params['package'] = self.package
        self.uiauto_params['output_dir'] = self.device.working_directory
        self.uiauto_params['output_file'] = self.output_file
        self.uiauto_params['dumpsys_enabled'] = self.dumpsys_enabled

    def setup(self, context):
        super(Googlephotos, self).setup(context)

        for entry in os.listdir(self.dependencies_directory):
            wa_file = ''.join([self.file_prefix, entry])
            if entry.endswith(".jpg"):
                self.device.push_file(os.path.join(self.dependencies_directory, entry),
                                      os.path.join(self.device.working_directory, wa_file),
                                      timeout=300)

        # Force a re-index of the mediaserver cache to pick up new files
        self.device.execute('am broadcast -a android.intent.action.MEDIA_MOUNTED -d file:///sdcard')

    def update_result(self, context):
        super(Googlephotos, self).update_result(context)

        if self.dumpsys_enabled:
            self.device.pull_file(self.output_file, context.output_directory)
            result_file = os.path.join(context.output_directory, self.instrumentation_log)

            with open(result_file, 'r') as wfh:
                pattern = r'(?P<key>\w+)\s+(?P<value1>\d+)\s+(?P<value2>\d+)\s+(?P<value3>\d+)'
                regex = re.compile(pattern)
                for line in wfh:
                    match = regex.search(line)
                    if match:
                        context.result.add_metric((match.group('key') + "_start"), match.group('value1'))
                        context.result.add_metric((match.group('key') + "_finish"), match.group('value2'))
                        context.result.add_metric((match.group('key') + "_duration"), match.group('value3'))

    def teardown(self, context):
        super(Googlephotos, self).teardown(context)

        for entry in self.device.listdir(self.device.working_directory):
            if entry.endswith(".log"):
                self.device.pull_file(os.path.join(self.device.working_directory, entry),
                                      context.output_directory)
                self.device.delete_file(os.path.join(self.device.working_directory, entry))

            if entry.startswith(self.file_prefix) and entry.endswith(".jpg"):
                self.device.delete_file(os.path.join(self.device.working_directory, entry))

        # Force a re-index of the mediaserver cache to removed cached files
        self.device.execute('am broadcast -a android.intent.action.MEDIA_MOUNTED -d file:///sdcard')
