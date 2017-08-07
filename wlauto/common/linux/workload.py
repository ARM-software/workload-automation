#    Copyright 2017 ARM Limited
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
from math import ceil

from wlauto.core.extension import Parameter
from wlauto.core.workload import Workload
from wlauto.core.resource import NO_ONE
from wlauto.common.resources import Executable
from wlauto.common.android.resources import ReventFile
from wlauto.exceptions import WorkloadError
from wlauto.utils.revent import ReventRecording

class ReventWorkload(Workload):
    # pylint: disable=attribute-defined-outside-init

    description = """
    A workload for playing back revent recordings. You can supply three
    different files:
    
    1. {device_model}.setup.revent
    2. {device_model}.run.revent
    3. {device_model}.teardown.revent

    You may generate these files using the wa record command using the -s flag
    to specify the stage (``setup``, ``run``, ``teardown``)

    You may also supply an 'idle_time' in seconds in place of the run file.
    The ``run`` file may only be omitted if you choose to run this way, but
    while running idle may supply ``setup`` and ``teardown`` files.

    To use a ``setup`` or ``teardown`` file set the setup_required and/or
    teardown_required class attributes to True (default: False).

    N.B. This is the default description. You may overwrite this for your
    workload to include more specific information.

    """

    setup_required = False
    teardown_required = False

    parameters = [
        Parameter(
            'idle_time', kind=int, default=None,
             description='''
             The time you wish the device to remain idle for (if a value is
             given then this overrides any .run revent file).
             '''),
    ]

    def __init__(self, device, _call_super=True, **kwargs):
        if _call_super:
            Workload.__init__(self, device, **kwargs)
        self.setup_timeout = kwargs.get('setup_timeout', None)
        self.run_timeout = kwargs.get('run_timeout', None)
        self.teardown_timeout = kwargs.get('teardown_timeout', None)
        self.revent_setup_file = None
        self.revent_run_file = None
        self.revent_teardown_file = None
        self.on_device_setup_revent = None
        self.on_device_run_revent = None
        self.on_device_teardown_revent = None
        self.statedefs_dir = None

    def initialize(self, context):
        devpath = self.device.path
        self.on_device_revent_binary = devpath.join(self.device.binaries_directory, 'revent')

    def setup(self, context):
        devpath = self.device.path
        if self.setup_required:
            self.revent_setup_file = context.resolver.get(ReventFile(self, 'setup'))
            if self.revent_setup_file:
                self.on_device_setup_revent = devpath.join(self.device.working_directory,
                                                 os.path.split(self.revent_setup_file)[-1])
                duration = ReventRecording(self.revent_setup_file).duration
                self.default_setup_timeout = ceil(duration) + 30
        if not self.idle_time:
            self.revent_run_file = context.resolver.get(ReventFile(self, 'run'))
            if self.revent_run_file:
                self.on_device_run_revent = devpath.join(self.device.working_directory,
                                                 os.path.split(self.revent_run_file)[-1])
                self.default_run_timeout = ceil(ReventRecording(self.revent_run_file).duration) + 30
        if self.teardown_required:
            self.revent_teardown_file = context.resolver.get(ReventFile(self, 'teardown'))
            if self.revent_teardown_file:
                self.on_device_teardown_revent = devpath.join(self.device.working_directory,
                                                 os.path.split(self.revent_teardown_file)[-1])
                duration = ReventRecording(self.revent_teardown_file).duration
                self.default_teardown_timeout = ceil(duration) + 30
        self._check_revent_files(context)

        Workload.setup(self, context)

        if self.revent_setup_file is not None:
            self.setup_timeout = self.setup_timeout or self.default_setup_timeout
            self.device.killall('revent')
            command = '{} replay {}'.format(self.on_device_revent_binary, self.on_device_setup_revent)
            self.device.execute(command, timeout=self.setup_timeout)
            self.logger.debug('Revent setup completed.')

    def run(self, context):
        if not self.idle_time:
            self.run_timeout = self.run_timeout or self.default_run_timeout
            command = '{} replay {}'.format(self.on_device_revent_binary, self.on_device_run_revent)
            self.logger.debug('Replaying {}'.format(os.path.basename(self.on_device_run_revent)))
            self.device.execute(command, timeout=self.run_timeout)
            self.logger.debug('Replay completed.')
        else:
            self.logger.info('Idling for ' + str(self.idle_time) + ' seconds.')
            self.device.sleep(self.idle_time)
            self.logger.info('Successfully did nothing for ' + str(self.idle_time) + ' seconds!')

    def update_result(self, context):
        pass

    def teardown(self, context):
        if self.revent_teardown_file is not None:
            self.teardown_timeout = self.teardown_timeout or self.default_teardown_timeout
            command = '{} replay {}'.format(self.on_device_revent_binary,
                                            self.on_device_teardown_revent)
            self.device.execute(command, timeout=self.teardown_timeout)
            self.logger.debug('Replay completed.')
            self.device.killall('revent')
        if self.revent_setup_file is not None:
            self.device.delete_file(self.on_device_setup_revent)
        if not self.idle_time:
            self.device.delete_file(self.on_device_run_revent)
        if self.revent_teardown_file is not None:
            self.device.delete_file(self.on_device_teardown_revent)

    def _check_revent_files(self, context):
        # check the revent binary
        revent_binary = context.resolver.get(Executable(NO_ONE, self.device.abi, 'revent'))
        if not os.path.isfile(revent_binary):
            message = '{} does not exist. '.format(revent_binary)
            message += 'Please build revent for your system and place it in that location'
            raise WorkloadError(message)
        if not self.revent_run_file and not self.idle_time:
            # pylint: disable=too-few-format-args
            message = 'It seems a {0}.run.revent file does not exist, '\
                      'Please provide one for your device: {0}.'
            raise WorkloadError(message.format(self.device.name))

        self.on_device_revent_binary = self.device.install_executable(revent_binary)
        if self.revent_setup_file is not None:
            self.device.push_file(self.revent_setup_file, self.on_device_setup_revent)
        if not self.idle_time:
            self.device.push_file(self.revent_run_file, self.on_device_run_revent)
        if self.revent_teardown_file is not None:
            self.device.push_file(self.revent_teardown_file, self.on_device_teardown_revent)
