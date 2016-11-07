#    Copyright 2013-2015 ARM Limited
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


# pylint: disable=W0613,E1101
from __future__ import division
import os
import sys
import time
import csv
import shutil
import threading
import errno
import tempfile
import collections
import re

from distutils.version import LooseVersion

try:
    import pandas as pd
except ImportError:
    pd = None

from wlauto import Instrument, Parameter, IterationResult
from wlauto.instrumentation import instrument_is_installed
from wlauto.exceptions import (InstrumentError, WorkerThreadError, ConfigError,
                               DeviceNotRespondingError, TimeoutError)
from wlauto.utils.types import boolean, numeric
from wlauto.utils.fps import FpsProcessor, SurfaceFlingerFrame, GfxInfoFrame, GFXINFO_EXEMPT


VSYNC_INTERVAL = 16666667
PAUSE_LATENCY = 20
EPSYLON = 0.0001


class FpsInstrument(Instrument):

    name = 'fps'
    description = """
    Measures Frames Per Second (FPS) and associated metrics for a workload.

    .. note:: This instrument depends on pandas Python library (which is not part of standard
              WA dependencies), so you will need to install that first, before you can use it.

    Android L and below use SurfaceFlinger to calculate the FPS data.
    Android M and above use gfxinfo to calculate the FPS data.

    SurfaceFlinger:
    The view is specified by the workload as ``view`` attribute. This defaults
    to ``'SurfaceView'`` for game workloads, and ``None`` for non-game
    workloads (as for them FPS mesurement usually doesn't make sense).
    Individual workloads may override this.

    gfxinfo:
    The view is specified by the workload as ``package`` attribute.
    This is because gfxinfo already processes for all views in a package.

    This instrument adds four metrics to the results:

        :FPS: Frames Per Second. This is the frame rate of the workload.
        :frame_count: The total number of frames rendered during the execution of
                 the workload.
        :janks: The number of "janks" that occured during execution of the
                workload. Janks are sudden shifts in frame rate. They result
                in a "stuttery" UI. See http://jankfree.org/jank-busters-io
        :not_at_vsync: The number of frames that did not render in a single
                       vsync cycle.

    """
    supported_platforms = ['android']

    parameters = [
        Parameter('drop_threshold', kind=numeric, default=5,
                  description='Data points below this FPS will be dropped as they '
                              'do not constitute "real" gameplay. The assumption '
                              'being that while actually running, the FPS in the '
                              'game will not drop below X frames per second, '
                              'except on loading screens, menus, etc, which '
                              'should not contribute to FPS calculation. '),
        Parameter('keep_raw', kind=boolean, default=False,
                  description='If set to ``True``, this will keep the raw dumpsys output '
                              'in the results directory (this is maily used for debugging) '
                              'Note: frames.csv with collected frames data will always be '
                              'generated regardless of this setting.'),
        Parameter('generate_csv', kind=boolean, default=True,
                  description='If set to ``True``, this will produce temporal fps data '
                              'in the results directory, in a file named fps.csv '
                              'Note: fps data will appear as discrete step-like values '
                              'in order to produce a more meainingfull representation,'
                              'a rolling mean can be applied.'),
        Parameter('crash_check', kind=boolean, default=True,
                  description="""
                  Specifies wither the instrument should check for crashed content by examining
                  frame data. If this is set, ``execution_time`` instrument must also be installed.
                  The check is performed by using the measured FPS and exection time to estimate the expected
                  frames cound and comparing that against the measured frames count. The the ratio of
                  measured/expected is too low, then it is assumed that the content has crashed part way
                  during the run. What is "too low" is determined by ``crash_threshold``.

                  .. note:: This is not 100\% fool-proof. If the crash occurs sufficiently close to
                            workload's termination,  it may not be detected. If this is expected, the
                            threshold may be adjusted up to compensate.
                  """),
        Parameter('crash_threshold', kind=float, default=0.7,
                  description="""
                  Specifies the threshold used to decided whether a measured/expected frames ration indicates
                  a content crash. E.g. a value of ``0.75`` means the number of actual frames counted is a
                  quarter lower than expected, it will treated as a content crash.
                  """),
        Parameter('dumpsys_period', kind=float, default=2, constraint=lambda x: x > 0,
                  description="""
                  Specifies the time period between calls to ``dumpsys SurfaceFlinger --latency`` in
                  seconds when collecting frame data. Using a lower value improves the granularity
                  of timings when recording actions that take a short time to complete. Note, this
                  will produce duplicate frame data in the raw dumpsys output, however, this is
                  filtered out in frames.csv. It may also affect the overall load on the system.

                  The default value of 2 seconds corresponds with the NUM_FRAME_RECORDS in
                  android/services/surfaceflinger/FrameTracker.h (as of the time of writing
                  currently 128) and a frame rate of 60 fps that is applicable to most devices.
                  """),
    ]

    def __init__(self, device, **kwargs):
        super(FpsInstrument, self).__init__(device, **kwargs)
        self.collector = None
        self.outfile = None
        self.fps_outfile = None
        self.is_enabled = True
        self.fps_method = ''

    def validate(self):
        if not pd or LooseVersion(pd.__version__) < LooseVersion('0.13.1'):
            message = ('fps instrument requires pandas Python package (version 0.13.1 or higher) to be installed.\n'
                       'You can install it with pip, e.g. "sudo pip install pandas"')
            raise InstrumentError(message)
        if self.crash_check and not instrument_is_installed('execution_time'):
            raise ConfigError('execution_time instrument must be installed in order to check for content crash.')

    def setup(self, context):
        workload = context.workload
        if hasattr(workload, 'view'):
            self.fps_outfile = os.path.join(context.output_directory, 'fps.csv')
            self.outfile = os.path.join(context.output_directory, 'frames.csv')
            # Android M brings a new method of collecting FPS data
            if self.device.get_sdk_version() >= 23:
                # gfxinfo takes in the package name rather than a single view/activity
                # so there is no 'list_command' to run and compare against a list of
                # views/activities. Additionally, clearing the stats requires the package
                # so we need to clear for every package in the workload.
                # Usually there is only one package, but some workloads may run multiple
                # packages so each one must be reset before continuing
                self.fps_method = 'gfxinfo'
                runcmd = 'dumpsys gfxinfo {} framestats'
                lstcmd = None
                params = workload.package
                params = [params] if isinstance(params, basestring) else params
                for pkg in params:
                    self.device.execute('dumpsys gfxinfo {} reset'.format(pkg))
            else:
                self.fps_method = 'surfaceflinger'
                runcmd = 'dumpsys SurfaceFlinger --latency {}'
                lstcmd = 'dumpsys SurfaceFlinger --list'
                params = workload.view
                self.device.execute('dumpsys SurfaceFlinger --latency-clear ')

            self.collector = LatencyCollector(self.outfile, self.device, params or '',
                                              self.keep_raw, self.logger, self.dumpsys_period,
                                              runcmd, lstcmd, self.fps_method)
        else:
            self.logger.debug('Workload does not contain a view; disabling...')
            self.is_enabled = False

    def start(self, context):
        if self.is_enabled:
            self.logger.debug('Starting Frame Statistics collection...')
            self.collector.start()

    def stop(self, context):
        if self.is_enabled and self.collector.is_alive():
            self.logger.debug('Stopping Frame Statistics collection...')
            self.collector.stop()

    def update_result(self, context):
        if self.is_enabled:
            fps, frame_count, janks, not_at_vsync = float('nan'), 0, 0, 0
            p90, p95, p99 = [float('nan')] * 3
            data = pd.read_csv(self.outfile)
            if not data.empty:  # pylint: disable=maybe-no-member
                # gfxinfo method has an additional file generated that contains statistics
                stats_file = None
                if self.fps_method == 'gfxinfo':
                    stats_file = os.path.join(os.path.dirname(self.outfile), 'gfxinfo.csv')
                fp = FpsProcessor(data, extra_data=stats_file)
                per_frame_fps, metrics = fp.process(self.collector.refresh_period, self.drop_threshold)
                fps, frame_count, janks, not_at_vsync = metrics

                if self.generate_csv:
                    per_frame_fps.to_csv(self.fps_outfile, index=False, header=True)
                    context.add_artifact('fps', path='fps.csv', kind='data')

                p90, p95, p99 = fp.percentiles()

            context.result.add_metric('FPS', fps)
            context.result.add_metric('frame_count', frame_count)
            context.result.add_metric('janks', janks, lower_is_better=True)
            context.result.add_metric('not_at_vsync', not_at_vsync, lower_is_better=True)
            context.result.add_metric('frame_time_90percentile', p90, 'ms', lower_is_better=True)
            context.result.add_metric('frame_time_95percentile', p95, 'ms', lower_is_better=True)
            context.result.add_metric('frame_time_99percentile', p99, 'ms', lower_is_better=True)

    def slow_update_result(self, context):
        result = context.result
        if self.crash_check and result.has_metric('execution_time'):
            self.logger.debug('Checking for crashed content.')
            exec_time = result['execution_time'].value
            fps = result['FPS'].value
            frames = result['frame_count'].value
            if all([exec_time, fps, frames]):
                expected_frames = fps * exec_time
                ratio = frames / expected_frames
                self.logger.debug('actual/expected frames: {:.2}'.format(ratio))
                if ratio < self.crash_threshold:
                    self.logger.error('Content for {} appears to have crashed.'.format(context.spec.label))
                    result.status = IterationResult.FAILED
                    result.add_event('Content crash detected (actual/expected frames: {:.2}).'.format(ratio))


class LatencyCollector(threading.Thread):
    # Note: the size of the frames buffer for a particular surface is defined
    #       by NUM_FRAME_RECORDS inside android/services/surfaceflinger/FrameTracker.h.
    #       At the time of writing, this was hard-coded to 128. So at 60 fps
    #       (and there is no reason to go above that, as it matches vsync rate
    #       on pretty much all phones), there is just over 2 seconds' worth of
    #       frames in there. Hence the default sleep time of 2 seconds between dumps.

    def __init__(self, outfile, device, activities, keep_raw, logger, dumpsys_period,
                 run_command, list_command, fps_method):
        super(LatencyCollector, self).__init__()
        self.outfile = outfile
        self.device = device
        self.keep_raw = keep_raw
        self.logger = logger
        self.dumpsys_period = dumpsys_period
        self.stop_signal = threading.Event()
        self.frames = []
        self.last_ready_time = 0
        self.refresh_period = VSYNC_INTERVAL
        self.drop_threshold = self.refresh_period * 1000
        self.exc = None
        self.unresponsive_count = 0
        if isinstance(activities, basestring):
            activities = [activities]
        self.activities = activities
        self.command_template = run_command
        self.list_command = list_command
        self.fps_method = fps_method
        # Based on the fps_method, setup the header for the csv,
        # and set the process_trace_line function accordingly
        if fps_method == 'surfaceflinger':
            self.header = SurfaceFlingerFrame._fields
            self.process_trace_line = self._process_surfaceflinger_line
        else:
            self.header = GfxInfoFrame._fields
            self.process_trace_line = self._process_gfxinfo_line
            self.re_frame = re.compile('([0-9]+,)+')
            self.re_stats = re.compile('.*(percentile|frames|Number).*')
            # Create a template summary text block that matches what gfxinfo gives after a reset
            # - 133 is the default ms value for percentiles after reset
            self.summary = collections.OrderedDict((('Total frames rendered', 0),
                                                    ('Janky frames', 0),
                                                    ('90th percentile', 133),
                                                    ('95th percentile', 133),
                                                    ('99th percentile', 133),
                                                    ('Number Missed Vsync', 0),
                                                    ('Number High input latency', 0),
                                                    ('Number Slow UI thread', 0),
                                                    ('Number Slow bitmap uploads', 0),
                                                    ('Number Slow issue draw commands', 0)))

    def run(self):
        try:
            self.logger.debug('Frame Statistics collection started. Method: ' + self.fps_method)
            self.stop_signal.clear()
            fd, temp_file = tempfile.mkstemp()
            self.logger.debug('temp file: {}'.format(temp_file))
            wfh = os.fdopen(fd, 'wb')
            try:
                view_list = self.activities
                while not self.stop_signal.is_set():
                    # If a list_command is provided, set the view_list to be its output
                    # Then check for each activity in this list and if there is a match,
                    # process the output. If no command is provided, then always process.
                    if self.list_command:
                        view_list = self.device.execute(self.list_command).split()
                    for activity in self.activities:
                        if activity in view_list:
                            wfh.write(self.device.execute(self.command_template.format(activity)))
                    time.sleep(self.dumpsys_period)
            finally:
                wfh.close()
            # TODO: this can happen after the run during results processing
            with open(temp_file) as fh:
                text = fh.read().replace('\r\n', '\n').replace('\r', '\n')
                for line in text.split('\n'):
                    line = line.strip()
                    if line:
                        self.process_trace_line(line)
            if self.keep_raw:
                raw_file = os.path.join(os.path.dirname(self.outfile), self.fps_method + '.raw')
                shutil.copy(temp_file, raw_file)
            os.unlink(temp_file)
        except (DeviceNotRespondingError, TimeoutError):  # pylint: disable=W0703
            raise
        except Exception, e:  # pylint: disable=W0703
            self.logger.warning('Exception on collector thread: {}({})'.format(e.__class__.__name__, e))
            self.exc = WorkerThreadError(self.name, sys.exc_info())
        self.logger.debug('Frame Statistics collection stopped.')

        with open(self.outfile, 'w') as wfh:
            writer = csv.writer(wfh)
            writer.writerow(self.header)
            writer.writerows(self.frames)
        self.logger.debug('Frames data written.')

        # gfxinfo outputs its own summary statistics for the run.
        # No point calculating those from the raw data, so store in its own file for later use.
        if self.fps_method == 'gfxinfo':
            stats_file = os.path.join(os.path.dirname(self.outfile), 'gfxinfo.csv')
            with open(stats_file, 'w') as wfh:
                writer = csv.writer(wfh)
                writer.writerows(zip(self.summary.keys(), self.summary.values()))
            self.logger.debug('Gfxinfo summary data written.')

    def stop(self):
        self.stop_signal.set()
        self.join()
        if self.unresponsive_count:
            message = 'LatencyCollector was unrepsonsive {} times.'.format(self.unresponsive_count)
            if self.unresponsive_count > 10:
                self.logger.warning(message)
            else:
                self.logger.debug(message)
        if self.exc:
            raise self.exc  # pylint: disable=E0702
        self.logger.debug('Frame Statistics complete.')

    def _process_surfaceflinger_line(self, line):
        parts = line.split()
        if len(parts) == 3:
            frame = SurfaceFlingerFrame(*map(int, parts))
            if frame.frame_ready_time <= self.last_ready_time:
                return  # duplicate frame
            if (frame.frame_ready_time - frame.desired_present_time) > self.drop_threshold:
                self.logger.debug('Dropping bogus frame {}.'.format(line))
                return  # bogus data
            self.last_ready_time = frame.frame_ready_time
            self.frames.append(frame)
        elif len(parts) == 1:
            self.refresh_period = int(parts[0])
            self.drop_threshold = self.refresh_period * 1000
        elif 'SurfaceFlinger appears to be unresponsive, dumping anyways' in line:
            self.unresponsive_count += 1
        else:
            self.logger.warning('Unexpected SurfaceFlinger dump output: {}'.format(line))

    def _process_gfxinfo_line(self, line):
        if 'No process found for' in line:
            self.unresponsive_count += 1
            return
        # Process lines related to the frame data
        match = self.re_frame.match(line)
        if match:
            data = match.group(0)[:-1]
            data = map(int, data.split(','))
            frame = GfxInfoFrame(*data)
            if frame not in self.frames:
                if frame.Flags & GFXINFO_EXEMPT:
                    self.logger.debug('Dropping exempt frame {}.'.format(line))
                else:
                    self.frames.append(frame)
            return
        # Process lines related to the summary statistics
        match = self.re_stats.match(line)
        if match:
            data = match.group(0)
            title, value = data.split(':', 1)
            title = title.strip()
            value = value.strip()
            if title in self.summary:
                if 'ms' in value:
                    value = value.strip('ms')
                if '%' in value:
                    value = value.split()[0]
                self.summary[title] = int(value)
