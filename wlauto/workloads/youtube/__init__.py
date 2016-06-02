import os
import logging
import re
import time

from wlauto import AndroidUiAutoBenchmark, Parameter


class Youtube(AndroidUiAutoBenchmark):

    name = 'youtube'
    package = 'com.google.android.youtube'
    activity = ''
    description = '''
    A workload to perform standard productivity tasks within YouTube.

    The workload plays a pre-defined video from the Watch Later playlist in different video
    quality bitrates.  It also seeks to a pre-defined position, pauses and restarts playback.
    '''

    parameters = [
        Parameter('dumpsys_enabled', kind=bool, default=True,
                  description='''
                  If ``True``, dumpsys captures will be carried out during the
                  test run.  The output is piped to log files which are then
                  pulled from the phone.
                  '''),
        Parameter('video_source', kind=str, default='trending',
                  allowed_values=['my_videos', 'search', 'trending'],
                  description='''
                  Determines where to play the video from. This can either be in
                  from the 'my videos' section in the YouTube account, or from the
                  top trending videos on the homepage, or one found in search.
                  '''),
    ]

    instrumentation_log = '{}_instrumentation.log'.format(name)

    def validate(self):
        super(Youtube, self).validate()
        self.output_file = os.path.join(self.device.working_directory, self.instrumentation_log)
        self.uiauto_params['package'] = self.package
        self.uiauto_params['output_dir'] = self.device.working_directory
        self.uiauto_params['output_file'] = self.output_file
        self.uiauto_params['dumpsys_enabled'] = self.dumpsys_enabled
        self.uiauto_params['video_source'] = self.video_source

    def update_result(self, context):
        super(Youtube, self).update_result(context)

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
        super(Youtube, self).teardown(context)

        for file in self.device.listdir(self.device.working_directory):
            if file.startswith (self.name) and file.endswith(".log"):
                self.device.pull_file(os.path.join(self.device.working_directory, file), context.output_directory)
                self.device.delete_file(os.path.join(self.device.working_directory, file))
