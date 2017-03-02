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

from wlauto import Workload, AndroidBenchmark, AndroidUxPerfWorkload, UiAutomatorWorkload
from wlauto import Parameter
from wlauto import ExtensionLoader
from wlauto import File
from wlauto import settings
from wlauto.exceptions import ConfigError
from wlauto.exceptions import ResourceError
from wlauto.utils.android import ApkInfo
from wlauto.utils.uxperf import UxPerfParser

import wlauto.common.android.resources


class Applaunch(AndroidUxPerfWorkload):

    name = 'applaunch'
    description = '''
    This workload launches and measures the launch time of applications for supporting workloads.

    Currently supported workloads are the ones that implement ``ApplaunchInterface``. For any
    workload to support this workload, it should implement the ``ApplaunchInterface``.
    The corresponding java file of the workload associated with the application being measured
    is executed during the run. The application that needs to be
    measured is passed as a parametre ``workload_name``. The parameters required for that workload
    have to be passed as a dictionary which is captured by the parametre ``workload_params``.
    This information can be obtained by inspecting the workload details of the specific workload.

    The workload allows to run multiple iterations of an application
    launch in two modes:

    1. Launch from background
    2. Launch from long-idle

    These modes are captured as a parameter applaunch_type.

    ``launch_from_background``
        Launches an application after the application is sent to background by
        pressing Home button.

    ``launch_from_long-idle``
        Launches an application after killing an application process and
        clearing all the caches.

    **Test Description:**

    -   During the initialization and setup, the application being launched is launched
        for the first time. The jar file of the workload of the application
        is moved to device at the location ``workdir`` which further implements the methods
        needed to measure the application launch time.

    -   Run phase calls the UiAutomator of the applaunch which runs in two subphases.
            A.  Applaunch Setup Run:
                    During this phase, welcome screens and dialogues during the first launch
                    of the instrumented application are cleared.
            B.  Applaunch Metric Run:
                    During this phase, the application is launched multiple times determined by
                    the iteration number specified by the parametre ``applaunch_iterations``.
                    Each of these iterations are instrumented to capture the launch time taken
                    and the values are recorded as UXPERF marker values in logfile.
    '''
    supported_platforms = ['android']

    parameters = [
        Parameter('workload_name', kind=str,
                  description='Name of the uxperf workload to launch',
                  default='gmail'),
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
        Parameter('report_results', kind=bool, default=True,
                  description="""
                  Choose to report results of the application launch time.
                  """),
    ]

    def __init__(self, device, **kwargs):
        super(Applaunch, self).__init__(device, **kwargs)

    def init_resources(self, context):
        super(Applaunch, self).init_resources(context)
        loader = ExtensionLoader(packages=settings.extension_packages, paths=settings.extension_paths)
        self.workload_params['markers_enabled'] = True
        self.workload = loader.get_workload(self.workload_name, self.device,
                                            **self.workload_params)
        self.init_workload_resources(context)
        self.package = self.workload.package

    def init_workload_resources(self, context):
        self.workload.uiauto_file = context.resolver.get(wlauto.common.android.resources.JarFile(self.workload))
        if not self.workload.uiauto_file:
            raise ResourceError('No UI automation JAR file found for workload {}.'.format(self.workload.name))
        self.workload.device_uiauto_file = self.device.path.join(self.device.working_directory, os.path.basename(self.workload.uiauto_file))
        if not self.workload.uiauto_package:
            self.workload.uiauto_package = os.path.splitext(os.path.basename(self.workload.uiauto_file))[0]

    def validate(self):
        super(Applaunch, self).validate()
        self.workload.validate()
        self.pass_parameters()

    def pass_parameters(self):
        self.uiauto_params['workload'] = self.workload.name
        self.uiauto_params['package'] = self.workload.package
        self.uiauto_params['binaries_directory'] = self.device.binaries_directory
        self.uiauto_params.update(self.workload.uiauto_params)
        if self.workload.activity:
            self.uiauto_params['launch_activity'] = self.workload.activity
        else:
            self.uiauto_params['launch_activity'] = "None"
        self.uiauto_params['applaunch_type'] = self.applaunch_type
        self.uiauto_params['applaunch_iterations'] = self.applaunch_iterations

    def setup(self, context):
        AndroidBenchmark.setup(self.workload, context)
        if not self.workload.launch_main:
            self.workload.launch_app()
        UiAutomatorWorkload.setup(self, context)
        self.workload.device.push_file(self.workload.uiauto_file, self.workload.device_uiauto_file)

    def run(self, context):
        UiAutomatorWorkload.run(self, context)

    def update_result(self, context):
        super(Applaunch, self).update_result(context)
        if self.report_results:
            parser = UxPerfParser(context, prefix='applaunch_')
            logfile = os.path.join(context.output_directory, 'logcat.log')
            parser.parse(logfile)
            parser.add_action_timings()

    def teardown(self, context):
        super(Applaunch, self).teardown(context)
        AndroidBenchmark.teardown(self.workload, context)
        UiAutomatorWorkload.teardown(self.workload, context)
        #Workload uses Dexclass loader while loading the jar file of the instrumented workload.
        #Dexclassloader unzips and generates .dex file in the .jar directory during the run.
        device_uiauto_dex_file = self.workload.device_uiauto_file.replace(".jar", ".dex")
        self.workload.device.delete_file(self.device.path.join(self.device.binaries_directory, device_uiauto_dex_file))
