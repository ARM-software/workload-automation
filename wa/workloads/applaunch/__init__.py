#    Copyright 2015-2017 ARM Limited
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

from wa import ApkUiautoWorkload, Parameter, TargetError
from wa.framework import pluginloader


class Applaunch(ApkUiautoWorkload):

    name = 'applaunch'
    description = '''
    This workload launches and measures the launch time of applications for supporting workloads.

    Currently supported workloads are the ones that implement ``ApplaunchInterface``. For any
    workload to support this workload, it should implement the ``ApplaunchInterface``.
    The corresponding java file of the workload associated with the application being measured
    is executed during the run. The application that needs to be
    measured is passed as a parameter ``workload_name``. The parameters required for that workload
    have to be passed as a dictionary which is captured by the parameter ``workload_params``.
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
                    the iteration number specified by the parameter ``applaunch_iterations``.
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
                  from long-idle. These two types are described in the workload
                  description.
                  """),
        Parameter('applaunch_iterations', kind=int, default=1,
                  description="""
                  Number of iterations of the application launch
                  """),
    ]

    def __init__(self, target, **kwargs):
        super(Applaunch, self).__init__(target, **kwargs)
        # Android doesn't allow to writable dex files starting 14 version and
        # default location (/sdcard/devlib-target) doesn't support readonly files
        # so we use /data/local/tmp as asset directory for this workload.
        self.asset_directory = '/data/local/tmp'
        self._su_has_command_option = None

    def workload_apk(self):
        return self.deployed_assets[-1]

    def initialize(self, context):
        super(Applaunch, self).initialize(context)

        worload_apk = self.workload_apk()
        self.gui.uiauto_params['workload_apk'] = worload_apk

        # Make workload apk readonly to comply with Android >= 14.
        if self.target.get_sdk_version() >= 34:
            self.target.execute(f'chmod -w {worload_apk}')

    # Check installed su version and return whether it supports -c argument.
    #
    # Targets can have different versions of su
    # - Targets with engineering Android version have su with following usage:
    #   su [WHO [COMMAND...]]
    # - Targets with rooted user Android version have su that supports passing
    #   command via -c argument.
    def su_has_command_option(self):
        if self._su_has_command_option is None:
            try:
                self.target.execute('su -c id')
                self._su_has_command_option = True
            except TargetError:
                self._su_has_command_option = False

            if self._su_has_command_option is False:
                try:
                    self.target.execute('su root id')
                except TargetError:
                    raise WorkloadError(
                        'su must be installed and support passing command '
                        'via -c argument (su -c <command>) or as positional '
                        'argument after user (su <user> <command>)'
                    )

        return self._su_has_command_option

    def init_resources(self, context):
        super(Applaunch, self).init_resources(context)
        self.workload_params['markers_enabled'] = True
        # pylint: disable=no-member
        self.workload = pluginloader.get_workload(self.workload_name, self.target,
                                                  **self.workload_params)
        self.workload.init_resources(context)
        self.workload.initialize(context)
        self.package_names = self.workload.package_names
        self.pass_parameters()
        # Deploy test workload uiauto apk
        self.asset_files.append(self.workload.gui.uiauto_file)

    def pass_parameters(self):
        self.gui.uiauto_params['workload'] = self.workload.name
        self.gui.uiauto_params['package_name'] = self.workload.package
        self.gui.uiauto_params.update(self.workload.gui.uiauto_params)
        if self.workload.apk.activity:
            self.gui.uiauto_params['launch_activity'] = self.workload.apk.activity
        else:
            self.gui.uiauto_params['launch_activity'] = "None"
        self.gui.uiauto_params['applaunch_type'] = self.applaunch_type
        self.gui.uiauto_params['applaunch_iterations'] = self.applaunch_iterations
        self.gui.uiauto_params['su_has_command_option'] = self.su_has_command_option()

    def setup(self, context):
        self.workload.gui.uiauto_params['package_name'] = self.workload.apk.apk_info.package
        self.workload.gui.init_commands()
        self.workload.gui.deploy()
        super(Applaunch, self).setup(context)

    def finalize(self, context):
        super(Applaunch, self).finalize(context)
        self.workload.finalize(context)
