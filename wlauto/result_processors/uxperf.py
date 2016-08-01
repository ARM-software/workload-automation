#    Copyright 2016 ARM Limited
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
import logging

from collections import defaultdict
from distutils.version import LooseVersion
from wlauto import ResultProcessor, Parameter
from wlauto.exceptions import ResultProcessorError
from wlauto.utils.fps import FpsProcessor
from wlauto.utils.types import numeric, boolean

try:
    import pandas as pd
except ImportError:
    pd = None


class UxPerfResultProcessor(ResultProcessor):

    name = 'uxperf'
    description = '''
    Parse logcat for UX_PERF markers to produce performance metrics for
    workload actions using specified instrumentation.

    An action represents a series of UI interactions to capture.

    NOTE: The UX_PERF markers are turned off by default and must be enabled in
    a agenda file by setting dumpsys_enabled for the workload to true.
    '''

    parameters = [
        Parameter('add_timings', kind=boolean, default=True,
                  description='''
                  If set to ``True``, add per-action timings to result metrics.'
                  '''),
        Parameter('add_frames', kind=boolean, default=False,
                  description='''
                  If set to ``True``, add per-action frame statistics to result
                  metrics. i.e. fps, frame_count, jank and not_at_vsync.

                  NOTE: This option requires the fps instrument to be enabled.
                  '''),
        Parameter('drop_threshold', kind=numeric, default=5,
                  description='''
                  Data points below this FPS will be dropped as they do not
                  constitute "real" gameplay. The assumption being that while
                  actually running, the FPS in the game will not drop below X
                  frames per second, except on loading screens, menus, etc,
                  which should not contribute to FPS calculation.
                  '''),
        Parameter('generate_csv', kind=boolean, default=True,
                  description='''
                  If set to ``True``, this will produce temporal per-action fps
                  data in the results directory, in a file named <action>_fps.csv.

                  Note: per-action fps data will appear as discrete step-like
                  values in order to produce a more meainingfull representation,
                  a rolling mean can be applied.
                  '''),
    ]

    def initialize(self, context):
        if not pd or LooseVersion(pd.__version__) < LooseVersion('0.13.1'):
            message = ('uxperf result processor requires pandas Python package '
                       '(version 0.13.1 or higher) to be installed.\n'
                       'You can install it with pip, e.g. "sudo pip install pandas"')
            raise ResultProcessorError(message)

    def export_iteration_result(self, result, context):
        parser = UxPerfParser(context)

        logfile = os.path.join(context.output_directory, 'logcat.log')
        framelog = os.path.join(context.output_directory, 'frames.csv')

        self.logger.debug('Parsing logcat.log for UX_PERF markers')
        parser.parse(logfile)

        if self.add_timings:
            self.logger.debug('Adding per-action timings')
            parser.add_action_timings()

        if self.add_frames:
            self.logger.debug('Adding per-action frame metrics')
            parser.add_action_frames(framelog, self.drop_threshold, self.generate_csv)


class UxPerfParser(object):
    '''
    Parses logcat messages for UX Performance markers.

    UX Performance markers are output from logcat under a debug priority. The
    logcat tag for the marker messages is UX_PERF. The messages associated with
    this tag consist of a name for the action to be recorded and a timestamp.
    These fields are delimited by a single space. e.g.

    <TAG>   : <MESSAGE>
    UX_PERF : gestures_swipe_left_start 861975087367
    ...
    ...
    UX_PERF : gestures_swipe_left_end 862132085804

    Timestamps are produced using the running Java Virtual Machine's
    high-resolution time source, in nanoseconds.
    '''
    def __init__(self, context):
        self.context = context
        self.actions = defaultdict(list)
        self.logger = logging.getLogger('UxPerfParser')

        # regex for matching logcat message format:
        self.regex = re.compile(r'UX_PERF.*?:\s*(?P<message>.*\d+$)')

    def parse(self, log):
        '''
        Opens log file and parses UX_PERF markers.

        Actions delimited by markers are captured in a dictionary with
        actions mapped to timestamps.
        '''
        loglines = self._read(log)
        timestamps = self._gen_action_timestamps(loglines)
        self._group_timestamps(timestamps)

    def add_action_frames(self, frames, drop_threshold, generate_csv):  # pylint: disable=too-many-locals
        '''
        Uses FpsProcessor to parse frame.csv extracting fps, frame count, jank
        and vsync metrics on a per action basis. Adds results to metrics.
        '''
        refresh_period = self._parse_refresh_peroid()

        for action in self.actions:
            # default values
            fps = float('nan')
            frame_count, janks, not_at_vsync = 0, 0, 0
            metrics = fps, frame_count, janks, not_at_vsync

            df = self._create_data_dict(action, frames)
            fp = FpsProcessor(pd.DataFrame(df), action=action)
            try:
                per_frame_fps, metrics = fp.process(refresh_period, drop_threshold)

                if generate_csv:
                    name = action + '_fps'
                    filename = name + '.csv'
                    fps_outfile = os.path.join(self.context.output_directory, filename)
                    per_frame_fps.to_csv(fps_outfile, index=False, header=True)
                    self.context.add_artifact(name, path=filename, kind='data')
            except AttributeError:
                self.logger.warning('Non-matched timestamps in dumpsys output: action={}'
                                    .format(action))

            fps, frame_count, janks, not_at_vsync = metrics
            result = self.context.result

            result.add_metric(action + '_FPS', fps)
            result.add_metric(action + '_frame_count', frame_count)
            result.add_metric(action + '_janks', janks)
            result.add_metric(action + '_not_at_vsync', not_at_vsync)

    def add_action_timings(self):
        '''
        Add simple action timings in millisecond resolution to metrics
        '''
        for action, timestamps in self.actions.iteritems():
            # nanosecond precision, but not necessarily nanosecond resolution
            # truncate to guarantee millisecond precision
            start, finish = tuple(int(ts[:-6]) for ts in timestamps)
            duration = finish - start
            result = self.context.result

            result.add_metric(action + "_start", start, units='ms')
            result.add_metric(action + "_finish", finish, units='ms')
            result.add_metric(action + "_duration", duration, units='ms')

    def _gen_action_timestamps(self, lines):
        '''
        Parses lines and matches against logcat tag.
        Yields tuple containing action and timestamp.
        '''
        for line in lines:
            match = self.regex.search(line)

            if match:
                message = match.group('message')
                action_with_suffix, timestamp = message.rsplit(' ', 1)
                action, _ = action_with_suffix.rsplit('_', 1)
                yield action, timestamp

    def _group_timestamps(self, markers):
        '''
        Groups timestamps by action name.
        Creates a dictionary of lists with actions mapped to timestamps.
        '''
        for action, timestamp in markers:
            self.actions[action].append(timestamp)

    def _parse_refresh_peroid(self):
        '''
        Reads the first line of the raw dumpsys output for the refresh period.
        '''
        raw_path = os.path.join(self.context.output_directory, 'surfaceflinger.raw')
        raw_lines = self._read(raw_path)
        refresh_period = raw_lines.next()

        return int(refresh_period)

    def _create_data_dict(self, action, frames):
        '''
        Creates a data dict containing surface flinger metrics for a captured
        action. Used to create a DataFrame for use with the pandas library.
        '''
        loglines = self._read(frames)
        loglines.next()  # skip csv header

        d = defaultdict(list)
        timestamps = self.actions[action]

        for row in self._matched_rows(loglines, timestamps):
            dpt, apt, frt = tuple(map(int, row.split(',')))
            d["desired_present_time"].append(dpt)
            d["actual_present_time"].append(apt)
            d["frame_ready_time"].append(frt)

        return d

    def _read(self, log):
        '''
        Opens a file a yields the lines with whitespace stripped.
        '''
        try:
            with open(log, 'r') as rfh:
                for line in rfh:
                    yield line.strip()
        except IOError:
            self.logger.error('Could not open {}'.format(log))

    @staticmethod
    def _matched_rows(rows, timestamps):
        '''
        Helper method for matching timestamps within rows.
        '''
        start, finish = tuple(timestamps)
        for row in rows:
            _, apt, _ = row.split(',')
            if apt >= start and apt <= finish:
                yield row
