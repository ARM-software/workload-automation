#    Copyright 2015 ARM Limited
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# pylint: disable=attribute-defined-outside-init
import os

from time import sleep

from wlauto import Workload, AndroidBenchmark, AndroidUxPerfWorkload, UiAutomatorWorkload
from wlauto import Parameter
from wlauto import ExtensionLoader
from wlauto import File
from wlauto import settings
from wlauto.exceptions import ConfigError
from wlauto.utils.android import ApkInfo


class UxperfApplaunch(Workload):
    """
    A workload that helps to launch other workloads and measure the application
    launch time
    """

    name = 'uxperfapplaunch'
    description = '''
    This workload helps to capture the applaunch time for all workloads
    that inherit *AndroidUxperfWorkload*. The application that needs to be
    measured is passed as a parametre *workload_name*. The parameters required
    for that workload have to be passed as a dictionary which is captured by
    the parametre *workload_params*. This information can be obtained
    by inspecting the workload details of the specific workload.
    The corresponding java file of the uxperf workload associated with the
    application being measured is required to run this workload. Hence, this
    workload is currently supported only for the existing workloads in
    the uxperf.

    The workload allows to run multiple iterations of an application
    launch in two modes:

    1. Launch from background
    2. Launch from long-idle

    These modes are captured as a parameter applaunch_type.

    *Launch from background*
        Launches an application after the application is sent to background by
        pressing Home button.

    *Launch from long_idle*
        Launches an application after killing an application process and
        clearing all the caches.

    **Test Description:**

    1. During the initialization and setup, the application being launched is
    launched for the first time.
    
    2. Run phase has two sub phases. 
        A. Applaunch Setup Run 
        B. Applaunch Metric Run

    *Applaunch Setup Run*
        During this phase, the welcome screens and dialogues during the first
    launch of an application are cleared. The application is then exited by
    pressing Home button if the application launch type is launch from
    background.

    *Applaunch Metric Run*
        During this phase, the application is launched multiple times determined by
    the iteration number specified by the parametre applaunch_iterations.
    Each of these iterations are instrumented to capture the launch time taken
    and the values are recorded as UXPERF marker values in logfiles. After
    every iteration, resulting logcat file is dumped into a subfolder that
    marks the iteration number. If the applaunch type is launch from long-idle,
    the application process is killed and caches are cleared between multiple
    iterations as well.

    '''
    supported_platforms = ['android']

    parameters = [
        Parameter('workload_name', kind=str,
                  description='Name of the uxperf workload to launch',
                  mandatory=True),
        Parameter('workload_params', kind=dict, default={},
                  description="""
                  parameters of the uxperf workload whose application launch
                  time is measured
                  """),
        Parameter('applaunch_type', kind=str, default='launch_from_background',
                  allowed_values=['launch_from_background', 'launch_from_long-idle'],
                  description="""
                  Choose launch_from_long-idle for measuring launch time
                  from long-idle. These two types are described in the class
                  description.
                  """),
        Parameter('applaunch_iterations', kind=int, default=1,
                  description="""
                  Number of iterations of the application launch
                  """),
        Parameter('markers_enabled', kind=bool, default=False,
                  description="""
                  If ``True``, UX_PERF action markers will be emitted to
                  logcat during the test run.
                  """),
    ]

    def __init__(self, device, **kwargs):
        super(UxperfApplaunch, self).__init__(device, **kwargs)
        loader = ExtensionLoader(packages=settings.extension_packages, paths=settings.extension_paths)
        self.workload_params['markers_enabled'] = self.markers_enabled
        self.workload = loader.get_workload(self.workload_name, device,
                                            **self.workload_params)

    def validate(self):
        self.workload.validate()
        self.workload.uiauto_params['package'] = self.workload.package
        if self.workload.activity:
            self.workload.uiauto_params[
                'launch_activity'] = self.workload.activity
        else:
            self.workload.uiauto_params['launch_activity'] = "None"
        self.workload.uiauto_params['applaunch_type'] = self.applaunch_type
        self.workload.uiauto_params['applaunch_iterations'] = self.applaunch_iterations

    def init_resources(self, context):
        self.workload.init_resources(context)
        self.logfile_path_list=[]

    def update_result(self, context):
        AndroidBenchmark.update_result(self.workload, context)

    def setup(self, context):
        AndroidBenchmark.setup(self.workload, context)
        if not self.workload.launch_main:  # Required for launching skype
            self.workload.launch_app()
        self.workload.uiauto_method = "runUxperfApplaunch"
        UiAutomatorWorkload.setup(self.workload, context)

    def run(self, context):
        UiAutomatorWorkload.run(self.workload, context)

    def teardown(self, context):
        UiAutomatorWorkload.teardown(self.workload, context)
        AndroidBenchmark.teardown(self.workload, context)
