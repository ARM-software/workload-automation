#    Copyright 2014-2015 ARM Limited
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
import signal
from math import ceil

from wlauto import ExtensionLoader, Command, settings
from wlauto.common.resources import Executable
from wlauto.core.resource import NO_ONE
from wlauto.core.resolver import ResourceResolver
from wlauto.core.configuration import RunConfiguration
from wlauto.core.agenda import Agenda
from wlauto.utils.revent import ReventRecording, GAMEPAD_MODE


class ReventCommand(Command):

    # Validate command options
    def validate_args(self, args):
        if args.clear and not args.package:
            print "Package must be specified if you want to clear cache\n"
            self.parser.print_help()
            sys.exit()

    # pylint: disable=W0201
    def execute(self, args):
        self.validate_args(args)
        self.logger.info("Connecting to device...")

        ext_loader = ExtensionLoader(packages=settings.extension_packages,
                                     paths=settings.extension_paths)

        # Setup config
        self.config = RunConfiguration(ext_loader)
        for filepath in settings.get_config_paths():
            self.config.load_config(filepath)
        self.config.set_agenda(Agenda())
        self.config.finalize()

        context = LightContext(self.config)

        # Setup device
        self.device = ext_loader.get_device(settings.device, **settings.device_config)
        self.device.validate()
        self.device.dynamic_modules = []
        self.device.connect()
        self.device.initialize(context)

        host_binary = context.resolver.get(Executable(NO_ONE, self.device.abi, 'revent'))
        self.target_binary = self.device.install_executable(host_binary)

        self.run(args)

    def run(self, args):
        raise NotImplementedError()


class RecordCommand(ReventCommand):

    name = 'record'
    description = '''Performs a revent recording

    This command helps making revent recordings. It will automatically
    deploy revent and even has the option of automatically opening apps.

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
       recording is for, currently these are either ``setup`` or ``run``. This
       should be specified with the ``-s`` argument.


    **gamepad recording**

    revent supports an alternative recording mode, where it will record events
    from a single gamepad device. In this mode, revent will store the
    description of this device as a part of the recording. When replaying such
    a recording, revent will first create a virtual gamepad using the
    description, and will replay the events into it, so a physical controller
    does not need to be connected on replay. Unlike standard revent recordings,
    recordings generated in this mode should be (to an extent) portable across
    different devices.

    note:

      - The device on which a recording is being made in gamepad mode, must have
        exactly one gamepad connected to it.
      - The device on which a gamepad recording is being replayed must have
        /dev/uinput enabled in the kernel (this interface is necessary to create
        virtual gamepad).

    '''

    def initialize(self, context):
        self.context = context
        self.parser.add_argument('-d', '--device', help='The name of the device')
        self.parser.add_argument('-s', '--suffix', help='The suffix of the revent file, e.g. ``setup``')
        self.parser.add_argument('-o', '--output', help='Directory to save the recording in')
        self.parser.add_argument('-p', '--package', help='Package to launch before recording')
        self.parser.add_argument('-g', '--gamepad', help='Record from a gamepad rather than all devices.',
                                 action="store_true")
        self.parser.add_argument('-C', '--clear', help='Clear app cache before launching it',
                                 action="store_true")
        self.parser.add_argument('-S', '--capture-screen', help='Record a screen capture after recording',
                                 action="store_true")

    def run(self, args):
        if args.device:
            device_name = args.device
        else:
            device_name = self.device.get_device_model()

        if args.suffix:
            args.suffix += "."

        revent_file = self.device.path.join(self.device.working_directory,
                                            '{}.{}revent'.format(device_name, args.suffix or ""))

        if args.clear:
            self.device.execute("pm clear {}".format(args.package))

        if args.package:
            self.logger.info("Starting {}".format(args.package))
            self.device.execute('monkey -p {} -c android.intent.category.LAUNCHER 1'.format(args.package))

        self.logger.info("Press Enter when you are ready to record...")
        raw_input("")
        gamepad_flag = '-g ' if args.gamepad else ''
        command = "{} record {}-s {}".format(self.target_binary, gamepad_flag, revent_file)
        self.device.kick_off(command)

        self.logger.info("Press Enter when you have finished recording...")
        raw_input("")
        if args.capture_screen:
            self.logger.info("Recording screen capture")
            self.device.capture_screen(args.output or os.getcwdu())
        self.device.killall("revent", signal.SIGINT)
        self.logger.info("Waiting for revent to finish")
        while self.device.get_pids_of("revent"):
            pass
        self.logger.info("Pulling files from device")
        self.device.pull_file(revent_file, args.output or os.getcwdu())


class ReplayCommand(ReventCommand):

    name = 'replay'
    description = '''Replay a revent recording

    Revent allows you to record raw inputs such as screen swipes or button presses.
    See ``wa show record`` to see how to make an revent recording.
    '''

    def initialize(self, context):
        self.context = context
        self.parser.add_argument('revent', help='The name of the file to replay')
        self.parser.add_argument('-p', '--package', help='Package to launch before recording')
        self.parser.add_argument('-C', '--clear', help='Clear app cache before launching it',
                                 action="store_true")

    # pylint: disable=W0201
    def run(self, args):
        self.logger.info("Pushing file to device")
        self.device.push_file(args.revent, self.device.working_directory)
        revent_file = self.device.path.join(self.device.working_directory, os.path.split(args.revent)[1])

        if args.clear:
            self.device.execute("pm clear {}".format(args.package))

        if args.package:
            self.logger.info("Starting {}".format(args.package))
            self.device.execute('monkey -p {} -c android.intent.category.LAUNCHER 1'.format(args.package))

        self.logger.info("Replaying recording")
        command = "{} replay {}".format(self.target_binary, revent_file)
        recording = ReventRecording(args.revent)
        timeout = ceil(recording.duration) + 30
        recording.close()
        self.device.execute(command, timeout=timeout,
                            as_root=(recording.mode == GAMEPAD_MODE))
        self.logger.info("Finished replay")


# Used to satisfy the API
class LightContext(object):
    def __init__(self, config):
        self.resolver = ResourceResolver(config)
        self.resolver.load()
