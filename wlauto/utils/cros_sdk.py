#    Copyright 2016 ARM Limited
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


import sys
import time
import os
import logging

from Queue import Queue, Empty
from threading import Thread
from subprocess import Popen, PIPE
from wlauto.utils.misc import which
from wlauto.exceptions import HostError


class OutputPollingThread(Thread):

    def __init__(self, out, queue, name):
        super(OutputPollingThread, self).__init__()
        self.out = out
        self.queue = queue
        self.stop_signal = False
        self.name = name

    def run(self):
        for line in iter(self.out.readline, ''):
            if self.stop_signal:
                break
            self.queue.put(line)

    def set_stop(self):
        self.stop_signal = True


class CrosSdkSession(object):

    def __init__(self, cros_path, password=''):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.in_chroot = True if which('dut-control') else False
        ON_POSIX = 'posix' in sys.builtin_module_names
        if self.in_chroot:
            self.cros_sdk_session = Popen(['/bin/sh'], bufsize=1, stdin=PIPE, stdout=PIPE, stderr=PIPE,
                                          cwd=cros_path, close_fds=ON_POSIX, shell=True)
        else:
            cros_sdk_bin_path = which('cros_sdk')
            potential_path = os.path.join("cros_path", "chromium/tools/depot_tools/cros_sdk")
            if not cros_sdk_bin_path and os.path.isfile(potential_path):
                cros_sdk_bin_path = potential_path
            if not cros_sdk_bin_path:
                raise HostError("Failed to locate 'cros_sdk' make sure it is in your PATH")
            self.cros_sdk_session = Popen(['sudo -Sk {}'.format(cros_sdk_bin_path)], bufsize=1, stdin=PIPE,
                                          stdout=PIPE, stderr=PIPE, cwd=cros_path, close_fds=ON_POSIX, shell=True)
            self.cros_sdk_session.stdin.write(password)
            self.cros_sdk_session.stdin.write('\n')
        self.stdout_queue = Queue()
        self.stdout_thread = OutputPollingThread(self.cros_sdk_session.stdout, self.stdout_queue, 'stdout')
        self.stdout_thread.daemon = True
        self.stdout_thread.start()
        self.stderr_queue = Queue()
        self.stderr_thread = OutputPollingThread(self.cros_sdk_session.stderr, self.stderr_queue, 'stderr')
        self.stderr_thread.daemon = True
        self.stderr_thread.start()

    def kill_session(self):
        self.stdout_thread.set_stop()
        self.stderr_thread.set_stop()
        self.send_command('echo TERMINATE >&1')  # send something into stdout to unblock it and close it properly
        self.send_command('echo TERMINATE 1>&2')  # ditto for stderr
        self.stdout_thread.join()
        self.stderr_thread.join()
        self.cros_sdk_session.kill()

    def send_command(self, cmd, flush=True):
        if not cmd.endswith('\n'):
            cmd = cmd + '\n'
        self.logger.debug(cmd.strip())
        self.cros_sdk_session.stdin.write(cmd)
        if flush:
            self.cros_sdk_session.stdin.flush()

    def read_line(self, timeout=0):
        return _read_line_from_queue(self.stdout_queue, timeout=timeout, logger=self.logger)

    def read_stderr_line(self, timeout=0):
        return _read_line_from_queue(self.stderr_queue, timeout=timeout, logger=self.logger)

    def get_lines(self, timeout=0, timeout_only_for_first_line=True, from_stderr=False):
        lines = []
        line = True
        while line is not None:
            if from_stderr:
                line = self.read_stderr_line(timeout)
            else:
                line = self.read_line(timeout)
            if line:
                lines.append(line)
                if timeout and timeout_only_for_first_line:
                    timeout = 0  # after a line has been read, no further delay is required
        return lines


def _read_line_from_queue(queue, timeout=0, logger=None):
    try:
        line = queue.get_nowait()
    except Empty:
        line = None
    if line is None and timeout:
        sleep_time = timeout
        time.sleep(sleep_time)
        try:
            line = queue.get_nowait()
        except Empty:
            line = None
    if line is not None:
        line = line.strip('\n')
    if logger and line:
        logger.debug(line)
    return line
