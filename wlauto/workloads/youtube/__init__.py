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

    This workload requires a stable internet connection, preferably Wi-Fi.

    Test description:
    1. The workload has 4 test scenarios, determined by the ``video_source`` parameter in
       the agenda file. These are ``home``, ``my_videos``, ``search``, and ``trending``.
       - A. home - The first video from the youtube home page is played
       - B. my_videos - A video is played from the user's account page. The user must have at
            least one uploaded video for this to work.
       - C. search - A search for a specific term is performed in the app. The first video in
            the search results is played. A parameter ``search_term`` must also be provided
            in the agenda for this to work.
       - D. trending - The first video in the trending videos list is played
    2. For each scenario, the following actions are performed:
       - seeking forward in the video
       - changing the video quality
       - checking the info card (that shows video metadata)
       - scrolling the list of related videos and/or comments
       - minimising the player, then expanding it again
       - playing the video in full screen
    '''

    parameters = [
        Parameter('dumpsys_enabled', kind=bool, default=True,
                  description='''
                  If ``True``, dumpsys captures will be carried out during the
                  test run.  The output is piped to log files which are then
                  pulled from the phone.
                  '''),
        Parameter('video_source', kind=str, default='home',
                  allowed_values=['home', 'my_videos', 'search', 'trending'],
                  description='''
                  Determines where to play the video from. This can either be from the
                  YouTube home, my videos section, trending videos or found in search.
                  '''),
        Parameter('search_term', kind=str, default='YouTube',
                  description='''
                  The search term to use when ``video_source`` is set to ``search``.
                  Not applicable otherwise.
                  '''),
    ]

    view = package + '/com.google.android.apps.youtube.app.WatchWhileActivity'

    instrumentation_log = '{}_instrumentation.log'.format(name)

    def __init__(self, device, **kwargs):
        super(Youtube, self).__init__(device, **kwargs)
        self.run_timeout = 300
        self.output_file = os.path.join(self.device.working_directory, self.instrumentation_log)

    def validate(self):
        super(Youtube, self).validate()
        self.uiauto_params['package'] = self.package
        self.uiauto_params['output_dir'] = self.device.working_directory
        self.uiauto_params['output_file'] = self.output_file
        self.uiauto_params['dumpsys_enabled'] = self.dumpsys_enabled
        self.uiauto_params['video_source'] = self.video_source
        if self.video_source == 'search':
            if self.search_term:
                self.uiauto_params['search_term'] = self.search_term.replace(' ', '_')
            else:
                raise WorkloadError("Param 'search_term' must be specified when video source is 'search'")

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
                                                  match.group('value1'), units='ms')
                        context.result.add_metric((match.group('key') + "_finish"),
                                                  match.group('value2'), units='ms')
                        context.result.add_metric((match.group('key') + "_duration"),
                                                  match.group('value3'), units='ms')

    def teardown(self, context):
        super(Youtube, self).teardown(context)
        for entry in self.device.listdir(self.device.working_directory):
            if entry.startswith(self.name) and entry.endswith(".log"):
                self.logger.info("Pulling file '{}'".format(entry))
                self.device.pull_file(os.path.join(self.device.working_directory, entry), context.output_directory)
                self.device.delete_file(os.path.join(self.device.working_directory, entry))
