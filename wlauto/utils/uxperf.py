import os
import re
import logging
from collections import defaultdict

from wlauto.utils.fps import FpsProcessor, SurfaceFlingerFrame, GfxInfoFrame, VSYNC_INTERVAL

try:
    import pandas as pd
except ImportError:
    pd = None


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
    def __init__(self, context, prefix=''):
        self.context = context
        self.prefix = prefix
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

            self.context.result.add_metric(self.prefix + action + '_FPS', fps)
            self.context.result.add_metric(self.prefix + action + '_frame_count', frame_count)
            self.context.result.add_metric(self.prefix + action + '_janks', janks, lower_is_better=True)
            self.context.result.add_metric(self.prefix + action + '_not_at_vsync', not_at_vsync, lower_is_better=True)
            self.context.result.add_metric(self.prefix + action + '_frame_time_90percentile', p90, 'ms', lower_is_better=True)
            self.context.result.add_metric(self.prefix + action + '_frame_time_95percentile', p95, 'ms', lower_is_better=True)
            self.context.result.add_metric(self.prefix + action + '_frame_time_99percentile', p99, 'ms', lower_is_better=True)

    def add_action_timings(self):
        '''
        Add simple action timings in millisecond resolution to metrics
        '''
        for action, timestamps in self.actions.iteritems():
            # nanosecond precision, but not necessarily nanosecond resolution
            # truncate to guarantee millisecond precision
            ts_ms = tuple(int(int(ts) / 1e6) for ts in timestamps)
            if len(ts_ms) == 2:
                start, finish = ts_ms
                duration = finish - start
                result = self.context.result

                result.add_metric(self.prefix + action + "_start", start, units='ms')
                result.add_metric(self.prefix + action + "_finish", finish, units='ms')
                result.add_metric(self.prefix + action + "_duration", duration, units='ms', lower_is_better=True)
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
