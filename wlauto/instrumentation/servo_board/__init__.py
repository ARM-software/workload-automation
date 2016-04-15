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
import time
import subprocess
import sys
import xmlrpclib
from subprocess import Popen, PIPE
from threading  import Thread

from wlauto import Instrument, Executable, Parameter
from wlauto.exceptions import ConfigError
from wlauto.utils.misc import ensure_file_directory_exists as _f
from wlauto.utils.types import arguments, list_of_strs

from Queue import Queue, Empty

class ServoInstrument(Instrument):
    """ 
    Measure power consumption with chromium servo board
    """

    name = 'servo'
    description = 'chromium servo board'

    parameters = [
        Parameter('servod_host', kind=str, default='localhost',
                  global_alias='servo_servod_host',
                  description="""hostname of the servod running"""),
        Parameter('servod_port', kind=str, default='9999',
                  global_alias='servo_servod_port',
                  description="""port number of the servod running"""),
        Parameter('delay', kind=float, default=0.2,
                  global_alias='servo_delay',
                  description="""delay before getting values"""),
        Parameter('power_for_little', kind=list_of_strs,
                  default=['dvfs2_mw', 'sram15_mw'],
                  global_alias='servo_power_for_little',
                  description="""names of power meters for little cluster"""),
        Parameter('power_for_big', kind=list_of_strs,
                  default=['dvfs1_mw', 'sram7_mw'],
                  global_alias='servo_power_for_big',
                  description="""names of power meters for big cluster"""),
    ]

    def initialize(self, context):
        self.start_time = None
        self.end_time = None
        self.proxy = xmlrpclib.ServerProxy("http://" +
		self.servod_host + ":" + self.servod_port + "/")

    def setup(self, context):
        pass

    def enqueue_output(self, queue):
        little_p = big_p = 0
        time.sleep(self.delay)

        for l in self.power_for_little:
            little_p += float(self.proxy.get(l))

        for b in self.power_for_big:
            big_p += float(self.proxy.get(b))

        queue.put(little_p)
        queue.put(big_p)

    def get_power(self):
        q = Queue()
        t = Thread(target=self.enqueue_output, args=[q])
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
        self.start_a53_power = self.q.get_nowait()
        self.start_a72_power = self.q.get_nowait()

    def update_result(self, context):
        power_consumed = self.end_time - self.start_time
        context.result.add_metric('a53_power', self.start_a53_power, 'milliwatts')
        context.result.add_metric('a72_power', self.start_a72_power, 'milliwatts')

    def teardown(self, context):
        pass

    def finalize(self, context):
        pass
