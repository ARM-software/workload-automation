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
import collections

try:
    import pandas as pd
except ImportError:
    pd = None

SurfaceFlingerFrame = collections.namedtuple('SurfaceFlingerFrame', 'desired_present_time actual_present_time frame_ready_time')
GfxInfoFrame = collections.namedtuple('GfxInfoFrame', 'Flags IntendedVsync Vsync OldestInputEvent NewestInputEvent HandleInputStart AnimationStart PerformTraversalsStart DrawStart SyncQueued SyncStart IssueDrawCommandsStart SwapBuffers FrameCompleted')
# https://android.googlesource.com/platform/frameworks/base/+/marshmallow-release/libs/hwui/JankTracker.cpp
# Frames that are exempt from jank metrics.
# First-draw frames, for example, are expected to be slow,
# this is hidden from the user with window animations and other tricks
# Similarly, we don't track direct-drawing via Surface:lockHardwareCanvas() for now
# Android M: WindowLayoutChanged | SurfaceCanvas
GFXINFO_EXEMPT = 1 | 4


class FpsProcessor(object):
    """
    Provides common object for processing surfaceFlinger output for frame
    statistics.

    This processor returns the four frame statistics below:

        :FPS: Frames Per Second. This is the frame rate of the workload.
        :frame_count: The total number of frames rendered during the execution of
                 the workload.
        :janks: The number of "janks" that occurred during execution of the
                workload. Janks are sudden shifts in frame rate. They result
                in a "stuttery" UI. See http://jankfree.org/jank-busters-io
        :not_at_vsync: The number of frames that did not render in a single
                       vsync cycle.
    """

    def __init__(self, data, action=None, extra_data=None):
        """
        data         - a pandas.DataFrame object with frame data (e.g. frames.csv)
        action       - output metrics names with additional action specifier
        extra_data   - extra data given to use for calculations of metrics
        """
        self.data = data
        self.action = action
        self.extra_data = extra_data

    def process(self, refresh_period, drop_threshold):  # pylint: disable=too-many-locals
        """
        Generate frame per second (fps) and associated metrics for workload.

        refresh_period - the vsync interval
        drop_threshold - data points below this fps will be dropped
        """
        fps = float('nan')
        frame_count, janks, not_at_vsync = 0, 0, 0
        vsync_interval = refresh_period
        per_frame_fps = pd.Series()

        # SurfaceFlinger Algorithm
        if self.data.columns.tolist() == list(SurfaceFlingerFrame._fields):
            # fiter out bogus frames.
            bogus_frames_filter = self.data.actual_present_time != 0x7fffffffffffffff
            actual_present_times = self.data.actual_present_time[bogus_frames_filter]
            actual_present_time_deltas = actual_present_times.diff().dropna()

            vsyncs_to_compose = actual_present_time_deltas.div(vsync_interval)
            vsyncs_to_compose.apply(lambda x: int(round(x, 0)))

            # drop values lower than drop_threshold FPS as real in-game frame
            # rate is unlikely to drop below that (except on loading screens
            # etc, which should not be factored in frame rate calculation).
            per_frame_fps = (1.0 / (vsyncs_to_compose.multiply(vsync_interval / 1e9)))
            keep_filter = per_frame_fps > drop_threshold
            filtered_vsyncs_to_compose = vsyncs_to_compose[keep_filter]
            per_frame_fps.name = 'fps'

            if not filtered_vsyncs_to_compose.empty:
                total_vsyncs = filtered_vsyncs_to_compose.sum()
                frame_count = filtered_vsyncs_to_compose.size

                if total_vsyncs:
                    fps = 1e9 * frame_count / (vsync_interval * total_vsyncs)

                janks = self._calc_janks(filtered_vsyncs_to_compose)
                not_at_vsync = self._calc_not_at_vsync(vsyncs_to_compose)

        # GfxInfo Algorithm
        elif self.data.columns.tolist() == list(GfxInfoFrame._fields):
            frame_time = self.data.FrameCompleted - self.data.IntendedVsync
            per_frame_fps = (1e9 / frame_time)
            keep_filter = per_frame_fps > drop_threshold
            per_frame_fps = per_frame_fps[keep_filter]
            per_frame_fps.name = 'fps'

            frame_count = self.data.index.size
            if frame_count:
                janks = frame_time[frame_time >= vsync_interval].count()
                not_at_vsync = self.data.IntendedVsync - self.data.Vsync
                not_at_vsync = not_at_vsync[not_at_vsync != 0].count()

                if frame_count > 1:
                    duration = self.data.Vsync.iloc[-1] - self.data.Vsync.iloc[0]
                    fps = (1e9 * frame_count) / float(duration)

            # If gfxinfocsv is provided, get stats from that instead
            if self.extra_data:
                series = pd.read_csv(self.extra_data, header=None, index_col=0, squeeze=True)
                if not series.empty:  # pylint: disable=maybe-no-member
                    frame_count = series['Total frames rendered']
                    janks = series['Janky frames']
                    not_at_vsync = series['Number Missed Vsync']

        metrics = (fps, frame_count, janks, not_at_vsync)
        return per_frame_fps, metrics

    def percentiles(self):
        # SurfaceFlinger Algorithm
        if self.data.columns.tolist() == list(SurfaceFlingerFrame._fields):
            frame_time = self.data.frame_ready_time.diff()
        # GfxInfo Algorithm
        elif self.data.columns.tolist() == list(GfxInfoFrame._fields):
            frame_time = self.data.FrameCompleted - self.data.IntendedVsync

        data = frame_time.dropna().quantile([0.90, 0.95, 0.99])
        # Convert to ms, round to nearest, cast to int
        data = data.div(1e6).round()
        try:
            data = data.astype('int')
        except ValueError:
            pass

        # If gfxinfocsv is provided, get stats from that instead
        if self.extra_data:
            series = pd.read_csv(self.extra_data, header=None, index_col=0, squeeze=True)
            if not series.empty:  # pylint: disable=maybe-no-member
                data = series[series.index.str.contains('th percentile')]  # pylint: disable=maybe-no-member

        return list(data.get_values())

    @staticmethod
    def _calc_janks(filtered_vsyncs_to_compose):
        """
        Internal method for calculating jank frames.
        """
        pause_latency = 20
        vtc_deltas = filtered_vsyncs_to_compose.diff().dropna()
        vtc_deltas = vtc_deltas.abs()
        janks = vtc_deltas.apply(lambda x: (pause_latency > x > 1.5) and 1 or 0).sum()

        return janks

    @staticmethod
    def _calc_not_at_vsync(vsyncs_to_compose):
        """
        Internal method for calculating the number of frames that did not
        render in a single vsync cycle.
        """
        epsilon = 0.0001
        func = lambda x: (abs(x - 1.0) > epsilon) and 1 or 0
        not_at_vsync = vsyncs_to_compose.apply(func).sum()

        return not_at_vsync
