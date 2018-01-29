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

    result_files = ['ftrace.txt', 'dmesg.txt']
    HOSTNAME = []
    KVERSION = []
    HEADER = []

    def setup(self, context):
        self.suspend_init()
        self.suspend_prepare()

    def run(self, context):
        self.force_suspend()

    def update_result(self, context):
        self.suspend_complete()

        for result_file in self.result_files:
            device_path = self.device.path.join(self.device.binaries_directory, result_file)
            host_path = os.path.join(context.output_directory, result_file)
            self.device.pull_file(device_path, host_path, timeout=10)

    def teardown(self, context):
        for result_file in self.result_files:
            device_path = self.device.path.join(self.device.binaries_directory, result_file)
            self.device.delete_file(device_path)
        pass

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

    def suspend_init(self):
        self.wait_for_boot()
        HOSTNAME = self.device.execute('hostname').replace('\n', '')
        KVERSION = self.device.execute('cat /proc/version').split()[2]
        STAMP = os.popen('date "+suspend-%m%d%y-%H%M%S"').read().replace('\n', '')

        self.HEADER = '# ' + STAMP + ' ' + HOSTNAME + ' ' + self.mode + ' ' + KVERSION

    def suspend_prepare(self):
        self.wait_for_boot()
        self.device.execute('input keyevent 26')	#Assure the Screen is on
        self.device.set_sysfile_value('/sys/kernel/debug/tracing/tracing_on', 0)
        self.device.set_sysfile_value('/sys/kernel/debug/tracing/trace_clock', 'global', verify=False)
        self.device.set_sysfile_value('/sys/kernel/debug/tracing/current_tracer', 'nop', verify=False)
        self.device.set_sysfile_value('/sys/kernel/debug/tracing/buffer_size_kb', 12345, verify=False)
        self.device.set_sysfile_value('/sys/kernel/debug/tracing/events/power/suspend_resume/enable', 1, verify=False)
        self.device.set_sysfile_value('/sys/kernel/debug/tracing/events/power/device_pm_callback_start/enable', 1, verify=False)
        self.device.set_sysfile_value('/sys/kernel/debug/tracing/events/power/device_pm_callback_end/enable', 1, verify=False)
        self.device.set_sysfile_value('/sys/kernel/debug/tracing/trace', '', verify=False)
        self.wait_for_boot()
        self.device.execute('dmesg -c')	#Clear dmesg buffer
        self.device.set_sysfile_value('/sys/kernel/debug/tracing/tracing_on', 1)

    def force_suspend(self):
        self.device.set_sysfile_value('/sys/class/rtc/rtc0/wakealarm', 0, verify=False)
        NOW=self.device.get_sysfile_value('/sys/class/rtc/rtc0/since_epoch', int)
        FUTURE = int(NOW) + self.waketime
        self.device.set_sysfile_value('/sys/class/rtc/rtc0/wakealarm', FUTURE, verify=False)

        #self.device.set_sysfile_value('/sys/kernel/debug/tracing/trace_marker', 'SUSPEND START', verify=False)
        # execution will pause here
        self.device.set_sysfile_value('/sys/power/state', self.mode, verify=False)
        #self.device.set_sysfile_value('/sys/kernel/debug/tracing/trace_marker', 'RESUME COMPLETE', verify=False)
        self.wait_for_boot()

    def suspend_complete(self):
        self.device.set_sysfile_value('/sys/kernel/debug/tracing/tracing_on', 0, verify=False)

        ftrace_file = self.device.path.join(self.device.binaries_directory, 'ftrace.txt')
        self.wait_for_boot()
        self.device.execute('echo \"{}\" > {}'.format(self.HEADER, ftrace_file))
        self.device.execute('cat /sys/kernel/debug/tracing/trace >> {}'.format(ftrace_file))

        dmesg_file = self.device.path.join(self.device.binaries_directory, 'dmesg.txt')
        self.wait_for_boot()
        self.device.execute('echo \"{}\" > {}'.format(self.HEADER, dmesg_file))
        self.device.execute('dmesg -c  >> {}'.format(dmesg_file))

