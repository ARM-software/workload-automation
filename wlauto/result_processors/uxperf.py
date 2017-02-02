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
from distutils.version import LooseVersion

from wlauto import ResultProcessor, Parameter
from wlauto.instrumentation import instrument_is_enabled
from wlauto.exceptions import ResultProcessorError, ConfigError
from wlauto.utils.types import numeric, boolean
from wlauto.utils.uxperf import UxPerfParser

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
        # needed for uxperf parser
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
