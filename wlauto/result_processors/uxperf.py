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
from wlauto.instrumentation import instrument_is_enabled
from wlauto.instrumentation.fps import VSYNC_INTERVAL
from wlauto.exceptions import ResultProcessorError, ConfigError
from wlauto.utils.fps import FpsProcessor, SurfaceFlingerFrame, GfxInfoFrame
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
    a agenda file by setting ``markers_enabled`` for the workload to ``True``.
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
        if self.add_frames and not instrument_is_enabled('fps'):
            raise ConfigError('fps instrument must be enabled in order to add frames.')

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
        self._gen_action_timestamps(loglines)

    def add_action_frames(self, frames, drop_threshold, generate_csv):  # pylint: disable=too-many-locals
        '''
        Uses FpsProcessor to parse frame.csv extracting fps, frame count, jank
        and vsync metrics on a per action basis. Adds results to metrics.
        '''
        refresh_period = self._parse_refresh_peroid()

        for action in self.actions:
            # default values
            fps, frame_count, janks, not_at_vsync = float('nan'), 0, 0, 0
            p90, p95, p99 = [float('nan')] * 3
            metrics = (fps, frame_count, janks, not_at_vsync)

            df = self._create_sub_df(self.actions[action], frames)
            if not df.empty:  # pylint: disable=maybe-no-member
                fp = FpsProcessor(df, action=action)
                try:
                    per_frame_fps, metrics = fp.process(refresh_period, drop_threshold)
                    fps, frame_count, janks, not_at_vsync = metrics

                    if generate_csv:
                        name = action + '_fps'
                        filename = name + '.csv'
                        fps_outfile = os.path.join(self.context.output_directory, filename)
                        per_frame_fps.to_csv(fps_outfile, index=False, header=True)
                        self.context.add_artifact(name, path=filename, kind='data')

                    p90, p95, p99 = fp.percentiles()
                except AttributeError:
                    self.logger.warning('Non-matched timestamps in dumpsys output: action={}'
                                        .format(action))

            self.context.result.add_metric(action + '_FPS', fps)
            self.context.result.add_metric(action + '_frame_count', frame_count)
            self.context.result.add_metric(action + '_janks', janks, lower_is_better=True)
            self.context.result.add_metric(action + '_not_at_vsync', not_at_vsync, lower_is_better=True)
            self.context.result.add_metric(action + '_frame_time_90percentile', p90, 'ms', lower_is_better=True)
            self.context.result.add_metric(action + '_frame_time_95percentile', p95, 'ms', lower_is_better=True)
            self.context.result.add_metric(action + '_frame_time_99percentile', p99, 'ms', lower_is_better=True)

    def add_action_timings(self):
        '''
        Add simple action timings in millisecond resolution to metrics
        '''
        for action, timestamps in self.actions.iteritems():
            # nanosecond precision, but not necessarily nanosecond resolution
            # truncate to guarantee millisecond precision
            ts_ms = tuple(int(ts[:-6]) for ts in timestamps)
            if len(ts_ms) == 2:
                start, finish = ts_ms
                duration = finish - start
                result = self.context.result

                result.add_metric(action + "_start", start, units='ms')
                result.add_metric(action + "_finish", finish, units='ms')
                result.add_metric(action + "_duration", duration, units='ms', lower_is_better=True)
            else:
                self.logger.warning('Expected two timestamps. Received {}'.format(ts_ms))

    def _gen_action_timestamps(self, lines):
        '''
        Parses lines and matches against logcat tag.
        Groups timestamps by action name.
        Creates a dictionary of lists with actions mapped to timestamps.
        '''
        for line in lines:
            match = self.regex.search(line)

            if match:
                message = match.group('message')
                action_with_suffix, timestamp = message.rsplit(' ', 1)
                action, _ = action_with_suffix.rsplit('_', 1)
                self.actions[action].append(timestamp)

    def _parse_refresh_peroid(self):
        '''
        Reads the first line of the raw dumpsys output for the refresh period.
        '''
        raw_path = os.path.join(self.context.output_directory, 'surfaceflinger.raw')
        if os.path.isfile(raw_path):
            raw_lines = self._read(raw_path)
            refresh_period = int(raw_lines.next())
        else:
            refresh_period = VSYNC_INTERVAL

        return refresh_period

    def _create_sub_df(self, action, frames):
        '''
        Creates a data frame containing fps metrics for a captured action.
        '''
        if len(action) == 2:
            start, end = map(int, action)
            df = pd.read_csv(frames)
            # SurfaceFlinger Algorithm
            if df.columns.tolist() == list(SurfaceFlingerFrame._fields):  # pylint: disable=maybe-no-member
                field = 'actual_present_time'
            # GfxInfo Algorithm
            elif df.columns.tolist() == list(GfxInfoFrame._fields):  # pylint: disable=maybe-no-member
                field = 'FrameCompleted'
            else:
                field = ''
                self.logger.error('frames.csv not in a recognised format. Cannot parse.')
            if field:
                df = df[start < df[field]]
                df = df[df[field] <= end]
        else:
            self.logger.warning('Discarding action. Expected 2 timestamps, got {}!'.format(len(action)))
            df = pd.DataFrame()
        return df

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
