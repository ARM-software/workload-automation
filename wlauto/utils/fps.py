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


class FpsProcessor(object):
    """
    Provide common object for processing surfaceFlinger output for frame
    statistics.

    This processor adds four metrics to the results:

        :FPS: Frames Per Second. This is the frame rate of the workload.
        :frames: The total number of frames rendered during the execution of
                 the workload.
        :janks: The number of "janks" that occurred during execution of the
                workload. Janks are sudden shifts in frame rate. They result
                in a "stuttery" UI. See http://jankfree.org/jank-busters-io
        :not_at_vsync: The number of frames that did not render in a single
                       vsync cycle.
    """

    def __init__(self, data, action=None):
        """
        data         - a pandas.DataFrame object with frame data (e.g. frames.csv)
        action       - output metrics names with additional action specifier
        """
        self.data = data
        self.action = action

    def process(self, refresh_period, drop_threshold):  # pylint: disable=too-many-locals
        """
        Generate frame per second (fps) and associated metrics for workload.

        refresh_period - the vsync interval
        drop_threshold - data points below this fps will be dropped
        """
        fps = float('nan')
        frame_count, janks, not_at_vsync = 0, 0, 0
        vsync_interval = refresh_period

        # fiter out bogus frames.
        bogus_frames_filter = self.data.actual_present_time != 0x7fffffffffffffff
        actual_present_times = self.data.actual_present_time[bogus_frames_filter]

        actual_present_time_deltas = actual_present_times - actual_present_times.shift()
        actual_present_time_deltas = actual_present_time_deltas.drop(0)

        vsyncs_to_compose = actual_present_time_deltas / vsync_interval
        vsyncs_to_compose.apply(lambda x: int(round(x, 0)))

        # drop values lower than drop_threshold FPS as real in-game frame
        # rate is unlikely to drop below that (except on loading screens
        # etc, which should not be factored in frame rate calculation).
        per_frame_fps = (1.0 / (vsyncs_to_compose * (vsync_interval / 1e9)))
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
        metrics = (fps, frame_count, janks, not_at_vsync)

        return per_frame_fps, metrics

    @staticmethod
    def _calc_janks(filtered_vsyncs_to_compose):
        """
        Internal method for calculating jank frames.
        """
        pause_latency = 20
        vtc_deltas = filtered_vsyncs_to_compose - filtered_vsyncs_to_compose.shift()
        vtc_deltas.index = range(0, vtc_deltas.size)
        vtc_deltas = vtc_deltas.drop(0).abs()
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
