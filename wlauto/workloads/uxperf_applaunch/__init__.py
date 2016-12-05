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

from wlauto import Workload, AndroidBenchmark, UiAutomatorWorkload
from wlauto import Parameter
from wlauto import ExtensionLoader
from wlauto import File
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
    that inherit AndroidUxperfWorkload. The application that needs to be
    measured is passed as a parametre workload_name. The parametres required
    for that workload have to be passed as a dictionary which is captured by
    the parametre workload_params. This information can be obtained
    by inspecting the workload details of the specific workload.
    The corresponding java file of the uxperf workload associated with the
    application being measured is required to run this workload. Hence, this
    workload is currently supported only for the existing workloads in
    the uxperf.

    The workload allows to run multiple iterations of an application
    launch in two modes.
    1- Launch from background
    2- Launch from long-idle
    These modes are captured as a parameter applaunch_type.

    ---launch from background---
    Launches an application after the application is sent to background by
    pressing Home button.

    ---launch from long_idle---
    Launches an application after killing an application process and
    clearing all the caches.

    Test Description:
    1- During the initialization and setup, the application being launched is
    launched for the first time.
    2- Run phase has two sub phases.
        A. Applaunch Setup Run
        B. Applaunch Metric Run

    ---Applaunch Setup Run---
    During this phase, the welcome screens and dialogues during the first
    launch of an application are cleared. The application is then exited by
    pressing Home button if the application launch type is launch from
    background.

    ---Applaunch Metric Run---
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
        Parameter('workload_params', kind=dict, default=False, mandatory=True,
                  description="""
                  Parametres of the uxperf workload whose application launch
                  time is measured
                  """),
        Parameter('workload_name', kind=str,
                  description='Name of the application to launch',
                  mandatory=True),
        Parameter('applaunch_type', kind=str, default='launch_from_background',
                  description="""
                  Choose launch_from_long-idle for measuring launch time
                  from long-idle
                  """),
        Parameter('applaunch_iterations', kind=int, default=1,
                  description="""
                  Number of iterations of the application launch
                  """),
    ]

    def __init__(self, device, **kwargs):
        super(UxperfApplaunch, self).__init__(device, **kwargs)
        loader = ExtensionLoader()
        self.workload = loader.get_workload(self.workload_name, device,
                                            **self.workload_params)

    def validate(self):
        self.workload.validate()
        if self.applaunch_type != 'launch_from_long-idle' and \
                self.applaunch_type != 'launch_from_background':
            raise ConfigError("Applaunch type specified wrong")
        self.workload.uiauto_params['package'] = self.workload.package
        if self.workload.activity:
            self.workload.uiauto_params[
                'launch_activity'] = self.workload.activity
        else:
            self.workload.uiauto_params['launch_activity'] = "None"
        self.workload.uiauto_params[
            'markers_enabled'] = self.workload.markers_enabled
        self.workload.uiauto_params['applaunch_type'] = self.applaunch_type

    def init_resources(self, context):
        self.workload.init_resources(context)

    def setup(self, context):
        AndroidBenchmark.setup(self.workload, context)
        if self.workload.launch_main is False:  # Required for launching skype
            self.workload.launch_app()

    def stop_application(self):
        """kills the application process
        """
        self.device.execute('am force-stop {}'.format(self.workload.package))

    def drop_pagecache(self):
        """clears page cache
        """
        self.device.execute('sync')
        self.device.execute('echo 1 > /proc/sys/vm/drop_caches', as_root=True)

    def drop_inodecache(self):
        """clears inode cache
        """
        self.device.execute('sync')
        self.device.execute('echo 2 > /proc/sys/vm/drop_caches', as_root=True)

    def drop_inodepagecache(self):
        """clears inode and page caches
        """
        self.device.execute('sync')
        self.device.execute('echo 3 > /proc/sys/vm/drop_caches', as_root=True)

    def clean_application(self):
        """Kills the application and clears caches if required
        """
        self.stop_application()
        if(self.applaunch_type == 'launch_from_long-idle'):
            self.drop_inodepagecache()

    def update_iteration_result(self, context, i):
        """Creates subfolders for every iterations and respective log files
        """
        iteration_folder = "{0}_{1}_{2}".format(
            self.workload.name, i, self.applaunch_iterations)
        iteration_path = os.path.join(
            context.output_directory, iteration_folder)
        if not os.path.exists(iteration_path):
            os.makedirs(iteration_path)
        logcat_log = os.path.join(iteration_path, i + '_logcat.log')
        self.device.dump_logcat(logcat_log)

    def update_result(self, context):
        self.logcat_log = open(os.path.join(
            context.output_directory, 'logcat.log'), 'w')
        marker = 'UX_PERF'
        for iter_dir in os.listdir(context.output_directory):
            if self.workload.name in iter_dir:
                dir_path = os.path.join(context.output_directory, iter_dir)
                for log_file in os.listdir(dir_path):
                    if log_file.endswith('.log'):
                        log_number = "applaunch{}".format(
                            log_file.split("_")[0])
                        file_path = os.path.join(dir_path, log_file)
                        with open(file_path, 'r') as log_data:
                            for line in log_data.readlines():
                                if marker in line and log_number in line:
                                    self.logcat_log.write(line)
        self.logcat_log.close()
        context.add_iteration_artifact(name='logcat',
                                       path='logcat.log',
                                       kind='log',
                                       description='Logcat dump for the run.')

    def init_run(self, context):
        """Run the setup run for applaunch, clear first time dialogues
        """
        self.workload.uiauto_method = "runApplaunchSetup"
        UiAutomatorWorkload.setup(self.workload, context)
        UiAutomatorWorkload.run(self.workload, context)

    def metric_run(self, context):
        """ Run iterations of applaunch test
        """
        for iteration in xrange(self.applaunch_iterations):
            if self.applaunch_type != 'launch_from_background':
                self.clean_application()
            sleep(10)
            self.workload.uiauto_method = "runApplaunchIteration"
            self.workload.uiauto_params['iteration_count'] = iteration
            UiAutomatorWorkload.setup(self.workload, context)
            AndroidBenchmark.clean_process(self.workload, context)
            UiAutomatorWorkload.run(self.workload, context)
            self.update_iteration_result(context, str(iteration))

    def run(self, context):
        self.init_run(context)  # Applaunch setup run
        self.metric_run(context)  # Applaunch iterations

    def teardown(self, context):
        UiAutomatorWorkload.teardown(self.workload, context)
        AndroidBenchmark.teardown(self.workload, context)
