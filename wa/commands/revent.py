#    Copyright 2014-2018 ARM Limited
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
from time import sleep

from wa import Command
from wa.framework import pluginloader
from wa.framework.exception import ConfigError
from wa.framework.resource import ResourceResolver, Resource
from wa.framework.target.manager import TargetManager
from wa.utils.revent import ReventRecorder
from devlib.target import Target
from argparse import _MutuallyExclusiveGroup, Namespace
from typing import (cast, Optional, TYPE_CHECKING, Dict,
                    Tuple, Callable)
if TYPE_CHECKING:
    from wa.framework.pluginloader import __LoaderWrapper
    from wa.framework.execution import ExecutionContext, ConfigManager
    from wa.framework.configuration.core import ConfigurationPoint, RunConfigurationProtocol
    from wa.framework.workload import Workload, ApkWorkload


class RecordCommand(Command):

    name: str = 'record'
    description: str = '''
    Performs a revent recording

    This command helps making revent recordings. It will automatically
    deploy revent and has options to automatically open apps and record
    specified stages of a workload.

    Revent allows you to record raw inputs such as screen swipes or button presses.
    This can be useful for recording inputs for workloads such as games that don't
    have XML UI layouts that can be used with UIAutomator. As a drawback from this,
    revent recordings are specific to the device type they were recorded on.

    WA uses two parts to the names of revent recordings in the format,
    {device_name}.{suffix}.revent.

     - device_name can either be specified manually with the ``-d`` argument or
       it can be automatically determined. On Android device it will be obtained
       from ``build.prop``, on Linux devices it is obtained from ``/proc/device-tree/model``.
     - suffix is used by WA to determine which part of the app execution the
       recording is for, currently these are either ``setup``, ``run``, ``extract_results``
       or ``teardown``. All stages are optional for recording and these should
       be specified with the ``-s``, ``-r``, ``-e`` or ``-t`` arguments respectively,
       or optionally ``-a`` to indicate all stages should be recorded.
    '''

    def __init__(self, **kwargs) -> None:
        super(RecordCommand, self).__init__(**kwargs)
        self.tm: Optional[TargetManager] = None
        self.target: Optional[Target] = None
        self.revent_recorder: Optional[ReventRecorder] = None

    def initialize(self, context: Optional['ExecutionContext']) -> None:
        self.parser.add_argument('-d', '--device', metavar='DEVICE',
                                 help='''
                                 Specify the device on which to run. This will
                                 take precedence over the device (if any)
                                 specified in configuration.
                                 ''')
        self.parser.add_argument('-o', '--output', help='Specify the output file', metavar='FILE')
        self.parser.add_argument('-s', '--setup', help='Record a recording for setup stage',
                                 action='store_true')
        self.parser.add_argument('-r', '--run', help='Record a recording for run stage',
                                 action='store_true')
        self.parser.add_argument('-e', '--extract_results', help='Record a recording for extract_results stage',
                                 action='store_true')
        self.parser.add_argument('-t', '--teardown', help='Record a recording for teardown stage',
                                 action='store_true')
        self.parser.add_argument('-a', '--all', help='Record recordings for available stages',
                                 action='store_true')

        # Need validation
        self.parser.add_argument('-C', '--clear', help='Clear app cache before launching it',
                                 action='store_true')
        group: _MutuallyExclusiveGroup = self.parser.add_mutually_exclusive_group(required=False)
        group.add_argument('-p', '--package', help='Android package to launch before recording')
        group.add_argument('-w', '--workload', help='Name of a revent workload (mostly games)')

    def validate_args(self, args: Namespace) -> None:
        """
        validate arguments
        """
        if args.clear and not (args.package or args.workload):
            self.logger.error("Package/Workload must be specified if you want to clear cache")
            sys.exit()
        if args.workload and args.output:
            self.logger.error("Output file cannot be specified with Workload")
            sys.exit()
        if not args.workload and (args.setup or args.extract_results
                                  or args.teardown or args.all):
            self.logger.error("Cannot specify a recording stage without a Workload")
            sys.exit()
        if args.workload and not any([args.all, args.teardown, args.extract_results, args.run, args.setup]):
            self.logger.error("Please specify which workload stages you wish to record")
            sys.exit()

    def execute(self, state: 'ConfigManager', args: Namespace) -> None:
        self.validate_args(args)
        state.run_config.merge_device_config(state.plugin_cache)
        if args.device:
            device = args.device
            device_config: Dict[str, 'ConfigurationPoint'] = {}
        else:
            device = cast('RunConfigurationProtocol', state.run_config).device
            device_config = cast(Dict[str, 'ConfigurationPoint'], state.run_config.device_config) or {}

        if args.output:
            outdir = os.path.basename(args.output)
        else:
            outdir = os.getcwd()

        self.tm = TargetManager(device, device_config, outdir)
        self.tm.initialize()
        self.target = self.tm.target
        if self.target:
            self.revent_recorder = ReventRecorder(self.target)
            self.revent_recorder.deploy()

        if args.workload:
            self.workload_record(args)
        elif args.package:
            self.package_record(args)
        else:
            self.manual_record(args)
        if self.revent_recorder:
            self.revent_recorder.remove()

    def record(self, revent_file: Optional[str], name: str, output_path: str) -> None:
        """
        record commands
        """
        msg: str = 'Press Enter when you are ready to record {}...'
        self.logger.info(msg.format(name))
        input('')
        if self.revent_recorder:
            self.revent_recorder.start_record(revent_file)
        msg = 'Press Enter when you have finished recording {}...'
        self.logger.info(msg.format(name))
        input('')
        if self.revent_recorder:
            self.revent_recorder.stop_record()

        if not os.path.isdir(output_path):
            os.makedirs(output_path)

        revent_file_name: str = self.target.path.basename(revent_file) if self.target and self.target.path else ''
        host_path: str = os.path.join(output_path, revent_file_name)
        if os.path.exists(host_path):
            msg = 'Revent file \'{}\' already exists, overwrite? [y/n]'
            self.logger.info(msg.format(revent_file_name))
            if input('') == 'y':
                os.remove(host_path)
            else:
                msg = 'Did not pull and overwrite \'{}\''
                self.logger.warning(msg.format(revent_file_name))
                return
        msg = 'Pulling \'{}\' from device'
        self.logger.info(msg.format(self.target.path.basename(revent_file) if self.target and self.target.path else ''))
        if self.target:
            self.target.pull(revent_file, output_path, as_root=self.target.is_rooted)

    def manual_record(self, args: Namespace) -> None:
        """
        record manually
        """
        output_path, file_name = self._split_revent_location(args.output)
        revent_file = self.target.get_workpath(file_name) if self.target else ''
        self.record(revent_file, '', output_path)
        msg = 'Recording is available at: \'{}\''
        self.logger.info(msg.format(os.path.join(output_path, file_name)))

    def package_record(self, args: Namespace) -> None:
        """
        record package execution on android
        """
        if self.target is None:
            raise ConfigError('Target is None')
        if self.target.os != 'android' and self.target.os != 'chromeos':
            raise ConfigError('Target does not appear to be running Android')
        if self.target.os == 'chromeos' and not self.target.supports_android:
            raise ConfigError('Target does not appear to support Android')
        if args.clear:
            self.target.execute('pm clear {}'.format(args.package))
        self.logger.info('Starting {}'.format(args.package))
        cmd: str = 'monkey -p {} -c android.intent.category.LAUNCHER 1'
        self.target.execute(cmd.format(args.package))

        output_path, file_name = self._split_revent_location(args.output)
        revent_file: Optional[str] = self.target.get_workpath(file_name)
        self.record(revent_file, '', output_path)
        msg = 'Recording is available at: \'{}\''
        self.logger.info(msg.format(os.path.join(output_path, file_name)))

    def workload_record(self, args: Namespace) -> None:
        """
        record workload execution
        """
        context = LightContext(self.tm)
        setup_revent: str = '{}.setup.revent'.format(self.target.model if self.target else '')
        run_revent: str = '{}.run.revent'.format(self.target.model if self.target else '')
        extract_results_revent: str = '{}.extract_results.revent'.format(self.target.model if self.target else '')
        teardown_file_revent: str = '{}.teardown.revent'.format(self.target.model if self.target else '')
        setup_file: Optional[str] = self.target.get_workpath(setup_revent) if self.target else ''
        run_file: Optional[str] = self.target.get_workpath(run_revent) if self.target else ''
        extract_results_file: Optional[str] = self.target.get_workpath(extract_results_revent) if self.target else ''
        teardown_file: Optional[str] = self.target.get_workpath(teardown_file_revent) if self.target else ''

        self.logger.info('Deploying {}'.format(args.workload))
        workload: 'Workload' = cast('__LoaderWrapper', pluginloader).get_workload(args.workload, self.target)
        # Setup apk if android workload
        if hasattr(workload, 'apk'):
            cast('ApkWorkload', workload).apk.initialize(cast('ExecutionContext', context))
            cast('ApkWorkload', workload).apk.setup(cast('ExecutionContext', context))
            sleep(cast('ApkWorkload', workload).loading_time)

        output_path: str = os.path.join(workload.dependencies_directory,
                                        'revent_files')
        if args.setup or args.all:
            self.record(setup_file, 'SETUP', output_path)
        if args.run or args.all:
            self.record(run_file, 'RUN', output_path)
        if args.extract_results or args.all:
            self.record(extract_results_file, 'EXTRACT_RESULTS', output_path)
        if args.teardown or args.all:
            self.record(teardown_file, 'TEARDOWN', output_path)
        self.logger.info('Tearing down {}'.format(args.workload))
        workload.teardown(cast('ExecutionContext', context))
        self.logger.info('Recording(s) are available at: \'{}\''.format(output_path))

    def _split_revent_location(self, output: str) -> Tuple[str, str]:
        """
        split the output location string into path and file name
        """
        output_path: Optional[str] = None
        file_name: Optional[str] = None
        if output:
            output_path, file_name, = os.path.split(output)

        if not file_name:
            file_name = '{}.revent'.format(self.target.model if self.target else '')
        if not output_path:
            output_path = os.getcwd()

        return output_path, file_name


class ReplayCommand(Command):

    name: str = 'replay'
    description: str = '''
    Replay a revent recording

    Revent allows you to record raw inputs such as screen swipes or button presses.
    See ``wa show record`` to see how to make an revent recording.
    '''

    def initialize(self, context: Optional['ExecutionContext']) -> None:
        self.parser.add_argument('recording', help='The name of the file to replay',
                                 metavar='FILE')
        self.parser.add_argument('-d', '--device', help='The name of the device')
        self.parser.add_argument('-p', '--package', help='Package to launch before recording')
        self.parser.add_argument('-C', '--clear', help='Clear app cache before launching it',
                                 action="store_true")

    # pylint: disable=W0201
    def execute(self, state: 'ConfigManager', args: Namespace) -> None:
        state.run_config.merge_device_config(state.plugin_cache)
        if args.device:
            device = args.device
            device_config: Dict[str, 'ConfigurationPoint'] = {}
        else:
            device = cast('RunConfigurationProtocol', state.run_config).device
            device_config = cast(Dict[str, 'ConfigurationPoint'], state.run_config.device_config) or {}

        target_manager = TargetManager(device, device_config, None)
        target_manager.initialize()
        self.target = target_manager.target
        revent_file: str = self.target.path.join(self.target.working_directory,
                                                 os.path.split(args.recording)[1]) if self.target and self.target.path else ''

        self.logger.info("Pushing file to target")
        self.target.push(args.recording, self.target.working_directory) if self.target else ''
        if target_manager.target:
            revent_recorder = ReventRecorder(target_manager.target)
            revent_recorder.deploy()

        if args.clear:
            if self.target:
                self.target.execute('pm clear {}'.format(args.package))

        if args.package:
            self.logger.info('Starting {}'.format(args.package))
            cmd = 'monkey -p {} -c android.intent.category.LAUNCHER 1'
            if self.target:
                self.target.execute(cmd.format(args.package))

        self.logger.info("Starting replay")
        revent_recorder.replay(revent_file)
        self.logger.info("Finished replay")
        revent_recorder.remove()


# Used to satisfy the workload API
class LightContext(object):
    """
    light execution context for satisfying workload api
    """
    def __init__(self, tm):
        self.tm = tm
        self.resolver = ResourceResolver()
        self.resolver.load()

    def get_resource(self, resource: Resource, strict: bool = True) -> Optional[str]:
        """
        get path to the resource
        """
        return self.resolver.get(resource, strict)

    def update_metadata(self, key: str, *args):
        """
        update metadata
        """
        pass

    get: Callable[..., Optional[str]] = get_resource
