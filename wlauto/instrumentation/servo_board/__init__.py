#    Copyright 2015 MediaTek Inc
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
import sys
import time
import re
import subprocess
from subprocess import Popen, PIPE
from threading  import Thread

from wlauto import Instrument, Executable, Parameter
from wlauto.exceptions import ConfigError
from wlauto.utils.misc import ensure_file_directory_exists as _f
from wlauto.utils.types import arguments, list_of_strs


from Queue import Queue, Empty

ON_POSIX = 'posix' in sys.builtin_module_names

class ServoInstrument(Instrument):
    """ 
    Measure power consumption with chromium servo board
    """

    name = 'servo'
    description = 'chromium servo board'

    parameters = [
        Parameter('cros_root', kind=str, default='/home/cros',
                  global_alias='servo_cros_root',
                  description="""root of ChromeOS source code"""),
    ]

    # get dvfs2_mw dvfs1_mw for now, should be able to choose sensors later
    dut_control = "chromite/bin/cros_sdk dut-control dvfs2_mw dvfs1_mw"

    def initialize(self, context):
        self.start_time = None
        self.end_time = None
        self.full_dut_control = self.cros_root + self.dut_control

    def setup(self, context):
        pass

    def enqueue_output(self, out, queue):
        for line in iter(out.readline, b''):
            queue.put(line)
        out.close()

    def get_power(self):
        p = Popen(self.full_dut_control, shell=True, stdout=PIPE, close_fds=ON_POSIX)
        q = Queue()
        t = Thread(target=self.enqueue_output, args=(p.stdout, q))
        t.daemon = True # thread dies with the program
        t.start()
        return q

    def fast_start(self, context):
        self.start_time = time.time()
        self.q = self.get_power()
        self.start_a53_power = 0
        self.start_a72_power = 0

    def fast_stop(self, context):
        self.end_time = time.time()
        results = self.q.get_nowait()
        sensors = re.split('[\n:]+', results)
        self.start_a72_power = sensors[1];
        results = self.q.get_nowait()
        sensors = re.split('[\n:]+', results)
        self.start_a53_power = sensors[1];

    def update_result(self, context):
        power_consumed = self.end_time - self.start_time
        context.result.add_metric('a53_power', self.start_a53_power, 'milliwatts')
        context.result.add_metric('a72_power', self.start_a72_power, 'milliwatts')

    def teardown(self, context):
        pass

    def finalize(self, context):
        pass
