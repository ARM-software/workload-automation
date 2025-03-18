#    Copyright 2020 ARM Limited
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
import time
from datetime import datetime, timedelta

import pandas as pd  # type: ignore

from wa import Instrument, Parameter, File, InstrumentError
from typing import List, TYPE_CHECKING, Optional, cast
if TYPE_CHECKING:
    from wa.framework.execution import ExecutionContext


class ProcStatCollector(Instrument):

    name: str = 'proc_stat'
    description: str = '''
    Collect CPU load information from /proc/stat.
    '''

    parameters: List[Parameter] = [
        Parameter('period', int, default=5,
                  constraint=lambda x: x > 0,
                  description='''
                  Time (in seconds) between collections.
                  '''),
    ]

    def initialize(self, context: 'ExecutionContext') -> None:  # pylint: disable=unused-argument
        """
        initialize proc stat collector
        """
        self.host_script: Optional[str] = context.get_resource(File(self, 'gather-load.sh'))
        self.target_script: Optional[str] = self.target.install(self.host_script)
        self.target_output: Optional[str] = self.target.get_workpath('proc-stat-raw.csv')
        self.stop_file: Optional[str] = self.target.get_workpath('proc-stat-stop.signal')

    def setup(self, context: 'ExecutionContext') -> None:  # pylint: disable=unused-argument
        """
        setup proc stat collector
        """
        self.command: str = '{} sh {} {} {} {} {}'.format(
            self.target.busybox,
            self.target_script,
            self.target.busybox,
            self.target_output,
            self.period,
            self.stop_file,
        )
        self.target.remove(self.target_output)
        self.target.remove(self.stop_file)

    def start(self, context: 'ExecutionContext') -> None:  # pylint: disable=unused-argument
        """
        start proc stat collector
        """
        self.target.kick_off(self.command)

    def stop(self, context: 'ExecutionContext') -> None:  # pylint: disable=unused-argument
        """
        stop proc stat collector
        """
        self.target.execute('{} touch {}'.format(self.target.busybox, self.stop_file))

    def update_output(self, context: 'ExecutionContext') -> None:
        """
        update output of proc stat collector
        """
        self.logger.debug('Waiting for collector script to terminate...')
        self._wait_for_script()
        self.logger.debug('Waiting for collector script to terminate...')
        host_output = os.path.join(context.output_directory, 'proc-stat-raw.csv')
        self.target.pull(self.target_output, host_output)
        context.add_artifact('proc-stat-raw', host_output, kind='raw')

        df = pd.read_csv(host_output)
        no_ts = df[df.columns[1:]]
        deltas = (no_ts - no_ts.shift())
        total = deltas.sum(axis=1)
        util = (total - deltas.idle) / total * 100
        out_df = pd.concat([df.timestamp, util], axis=1).dropna()
        out_df.columns = cast(pd.Index, ['timestamp', 'cpu_util'])

        util_file = os.path.join(context.output_directory, 'proc-stat.csv')
        out_df.to_csv(util_file, index=False)
        context.add_artifact('proc-stat', util_file, kind='data')

    def finalize(self, context: 'ExecutionContext') -> None:  # pylint: disable=unused-argument
        """
        finalize proc stat collector
        """
        if self.cleanup_assets and getattr(self, 'target_output'):
            self.target.remove(self.target_output)
            self.target.remove(self.target_script)

    def _wait_for_script(self) -> None:
        """
        wait for proc stat collector to terminate
        """
        start_time = datetime.utcnow()
        timeout = timedelta(seconds=300)
        while self.target.file_exists(self.stop_file):
            delta = datetime.utcnow() - start_time
            if delta > timeout:
                raise InstrumentError('Timed out wating for /proc/stat collector to terminate..')
