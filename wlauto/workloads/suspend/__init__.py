# 
# Author: arnoldlu@qq.com
#
# Depends on android.sh from 
# https://github.com/01org/pm-graph.git .

import os
import time
from wlauto import Workload, Parameter, File
import logging
from wlauto.utils.android import (adb_shell, adb_background_shell, adb_list_devices,
                                  adb_command)

logger = logging.getLogger('suspend')

class Suspend(Workload):
    '''
    1. sh android.sh capture-start ------Start ftrace capturing.
    2. sh android.sh suspend mem 15----Suspend, then resume after 15s by RTC alarm.
    3. sh android.sh capture-end-------Stop ftrace capturing, and save logs.
    '''

    name = 'suspend'
    description = "Suspend workload for analyzing suspend/resume flow."

    parameters = [
        # Workload parameters go here e.g.
        Parameter('mode', default='mem', allowed_values=['mem', 'freeze'],
                  description="""Supported modes."""),
        Parameter('waketime', kind=int, default=15,
                  description='The duration of suspend.')
    ]

    result_files = ['ftrace.txt', 'dmesg.txt', 'log.txt']

    def setup(self, context):
        self.android_host = context.resolver.get(File(self, "scripts/android.sh"))
        self.android_target = self.device.install(self.android_host)

        self.capture_end = 'cd {} && sh {} capture-end'.format(self.device.binaries_directory, 'android.sh', self.mode, self.waketime)
        self.capture_start = 'cd {} && sh {} capture-start'.format(self.device.binaries_directory, 'android.sh', self.mode, self.waketime)
        self.suspend = 'cd {} && sh {} suspend {} {}'.format(self.device.binaries_directory, 'android.sh', self.mode, self.waketime)

        self.device.execute(self.capture_end, timeout=5, as_root=True)
        self.device.execute(self.capture_start, timeout=5, as_root=True)

    def run(self, context):
        adb_shell(self.device.adb_name, self.suspend, timeout=5, as_root=True)
        time.sleep(1)
        self.wait_for_boot()
        

    def update_result(self, context):
        self.device.execute(self.capture_end, timeout=5)

        for result_file in self.result_files:
            device_path = self.device.path.join(self.device.binaries_directory, result_file)
            host_path = os.path.join(context.output_directory, result_file)
            self.device.pull_file(device_path, host_path, timeout=10)


    def teardown(self, context):
        for result_file in self.result_files:
            device_path = self.device.path.join(self.device.binaries_directory, result_file)
            self.device.delete_file(device_path)

    def validate(self):
        pass

    def wait_for_boot(self):
        """
        Wait for the system to boot

        We monitor the sys.boot_completed and service.bootanim.exit system
        properties to determine when the system has finished booting. In the
        event that we cannot coerce the result of service.bootanim.exit to an
        integer, we assume that the boot animation was disabled and do not wait
        for it to finish.

        """
        self.logger.info("Waiting for Android to boot...")
        while True:
            booted = False
            anim_finished = True  # Assume boot animation was disabled on except
            try:
                booted = (int('0' + self.device.execute('getprop sys.boot_completed', check_exit_code=False).strip()) == 1)
                anim_finished = (int(self.device.execute('getprop service.bootanim.exit', check_exit_code=False).strip()) == 1)
            except ValueError:
                pass
            if booted and anim_finished:
                break
            time.sleep(5)

        self.logger.info("Android booted")

