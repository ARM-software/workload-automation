#    Copyright 2018 ARM Limited
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

import logging
import os
import shutil
import sys
import tempfile
import threading
import time

from wa.framework.exception import WorkerThreadError
from wa.framework.plugin import Parameter
from wa.utils.android import LogcatParser
from wa.utils.misc import touch
import wa.framework.signal as signal
from typing import List, Optional, TYPE_CHECKING
from devlib.target import LinuxTarget, AndroidTarget, ChromeOsTarget
if TYPE_CHECKING:
    from wa.framework.execution import ExecutionContext


class LinuxAssistant(object):
    """
    assistant to connect to a linux target
    """
    parameters: List[Parameter] = []

    def __init__(self, target: LinuxTarget):
        self.target = target

    def initialize(self):
        """
        initialize the target
        """
        pass

    def start(self):
        """
        start the target
        """
        pass

    def extract_results(self, context: 'ExecutionContext'):
        """
        extract results of execution from the target
        """
        pass

    def stop(self):
        """
        stop the target
        """
        pass

    def finalize(self):
        """
        finalize the target
        """
        pass


class AndroidAssistant(object):
    """
    assistant to connect to an android target
    """
    parameters: List[Parameter] = [
        Parameter('disable_selinux', kind=bool, default=True,
                  description="""
                  If ``True``, the default, and the target is rooted, an attempt will
                  be made to disable SELinux by running ``setenforce 0`` on the target
                  at the beginning of the run.
                  """),
        Parameter('logcat_poll_period', kind=int,
                  constraint=lambda x: x > 0,
                  description="""
                  Polling period for logcat in seconds. If not specified,
                  no polling will be used.

                  Logcat buffer on android is of limited size and it cannot be
                  adjusted at run time. Depending on the amount of logging activity,
                  the buffer may not be enought to capture comlete trace for a
                  workload execution. For those situations, logcat may be polled
                  periodically during the course of the run and stored in a
                  temporary locaiton on the host. Setting the value of the poll
                  period enables this behavior.
                  """),
        Parameter('stay_on_mode', kind=int,
                  constraint=lambda x: 0 <= x <= 7,
                  description="""
                  Specify whether the screen should stay on while the device is
                  charging:

                    0: never stay on
                    1: with AC charger
                    2: with USB charger
                    4: with wireless charger

                  Values can be OR-ed together to produce combinations, for
                  instance ``7`` will cause the screen to stay on when charging
                  under any method.
                  """),
    ]

    def __init__(self, target: AndroidTarget, logcat_poll_period: Optional[int] = None,
                 disable_selinux: bool = True, stay_on_mode: Optional[int] = None):
        self.target = target
        self.logcat_poll_period = logcat_poll_period
        self.disable_selinux = disable_selinux
        self.stay_on_mode = stay_on_mode
        self.orig_stay_on_mode: Optional[int] = self.target.get_stay_on_mode() if stay_on_mode is not None else None
        self.logcat_poller: Optional[LogcatPoller] = None
        self.logger: logging.Logger = logging.getLogger('logcat')
        self._logcat_marker_msg: Optional[str] = None
        self._logcat_marker_tag: Optional[str] = None
        signal.connect(self._before_workload, signal.BEFORE_WORKLOAD_EXECUTION)
        if self.logcat_poll_period:
            signal.connect(self._after_workload, signal.AFTER_WORKLOAD_EXECUTION)

    def initialize(self) -> None:
        """
        initialize the android target
        """
        if self.target.is_rooted and self.disable_selinux:
            self.do_disable_selinux()
        if self.stay_on_mode is not None:
            self.target.set_stay_on_mode(self.stay_on_mode)

    def start(self) -> None:
        """
        start the android target
        """
        if self.logcat_poll_period:
            self.logcat_poller = LogcatPoller(self.target, self.logcat_poll_period)
            self.logcat_poller.start()
        else:
            if not self._logcat_marker_msg:
                self._logcat_marker_msg = 'WA logcat marker for wrap detection'
                self._logcat_marker_tag = 'WAlog'

    def stop(self) -> None:
        """
        stop the android target
        """
        if self.logcat_poller:
            self.logcat_poller.stop()

    def finalize(self):
        """
        finalize the android target
        """
        if self.stay_on_mode is not None:
            self.target.set_stay_on_mode(self.orig_stay_on_mode)

    def extract_results(self, context: 'ExecutionContext'):
        """
        extract execution results from android target
        """
        logcat_file = os.path.join(context.output_directory, 'logcat.log')
        self.dump_logcat(logcat_file)
        context.add_artifact('logcat', logcat_file, kind='log')
        self.clear_logcat()
        if not self._check_logcat_nowrap(logcat_file):
            self.logger.warning('The main logcat buffer wrapped and lost data;'
                                ' results that rely on this buffer may be'
                                ' inaccurate or incomplete.'
                                )

    def dump_logcat(self, outfile: str) -> None:
        """
        dump logcat buffer into output file
        """
        if self.logcat_poller:
            self.logcat_poller.write_log(outfile)
        else:
            self.target.dump_logcat(outfile, logcat_format='threadtime')

    def clear_logcat(self) -> None:
        """
        clear the logcat buffer
        """
        if self.logcat_poller:
            self.logcat_poller.clear_buffer()
        else:
            self.target.clear_logcat()

    def _before_workload(self, _) -> None:
        """
        things to do before start of workload
        """
        if self.logcat_poller:
            self.logcat_poller.start_logcat_wrap_detect()
        else:
            self.insert_logcat_marker()

    def _after_workload(self, _) -> None:
        """
        things to do after the end of workload run
        """
        if self.logcat_poller:
            self.logcat_poller.stop_logcat_wrap_detect()

    def _check_logcat_nowrap(self, outfile: str) -> bool:
        """
        check whether the logcat buffer is wrapping around or not
        """
        if self.logcat_poller:
            return self.logcat_poller.check_logcat_nowrap(outfile)
        else:
            parser = LogcatParser()
            for event in parser.parse(outfile):
                if (event.tag == self._logcat_marker_tag
                        and event.message == self._logcat_marker_msg):
                    return True

            return False

    def insert_logcat_marker(self) -> None:
        """
        insert logcat marker for wrap detection
        """
        self.logger.debug('Inserting logcat marker')
        self.target.execute(
            'log -t "{}" "{}"'.format(
                self._logcat_marker_tag, self._logcat_marker_msg
            )
        )

    def do_disable_selinux(self) -> None:
        """
        disable SELinux
        """
        # SELinux was added in Android 4.3 (API level 18). Trying to
        # 'getenforce' in earlier versions will produce an error.
        if self.target.get_sdk_version() >= 18:
            se_status = self.target.execute('getenforce', as_root=True).strip()
            if se_status == 'Enforcing':
                self.target.execute('setenforce 0', as_root=True, check_exit_code=False)


class LogcatPoller(threading.Thread):
    """
    to poll logcat periodically and store the buffer
    """
    def __init__(self, target: AndroidTarget, period: int = 60,
                 timeout: int = 30):
        super(LogcatPoller, self).__init__()
        self.target = target
        self.logger: logging.Logger = logging.getLogger('logcat')
        self.period = period
        self.timeout = timeout
        self.stop_signal = threading.Event()
        self.lock = threading.RLock()
        self.buffer_file = tempfile.mktemp()
        self.last_poll: float = 0
        self.daemon: bool = True
        self.exc: Optional[Exception] = None
        self._logcat_marker_tag = 'WALog'
        self._logcat_marker_msg = 'WA logcat marker for wrap detection:{}'
        self._marker_count = 0
        self._start_marker: Optional[int] = None
        self._end_marker: Optional[int] = None

    def run(self) -> None:
        """
        start polling logcat
        """
        self.logger.debug('Starting polling')
        try:
            self.insert_logcat_marker()
            while True:
                if self.stop_signal.is_set():
                    break
                with self.lock:
                    current_time = time.time()
                    if (current_time - self.last_poll) >= self.period:
                        self.poll()
                        self.insert_logcat_marker()
                time.sleep(0.5)
        except Exception:  # pylint: disable=W0703
            self.exc = WorkerThreadError(self.name, sys.exc_info())
        self.logger.debug('Polling stopped')

    def stop(self) -> None:
        """
        stop logcat polling
        """
        self.logger.debug('Stopping logcat polling')
        self.stop_signal.set()
        self.join(self.timeout)
        if self.is_alive():
            self.logger.error('Could not join logcat poller thread.')
        if self.exc:
            raise self.exc  # pylint: disable=E0702

    def clear_buffer(self) -> None:
        """
        clear logcat buffer
        """
        self.logger.debug('Clearing logcat buffer')
        with self.lock:
            self.target.clear_logcat()
            touch(self.buffer_file)

    def write_log(self, outfile: str) -> None:
        """
        write log into output file
        """
        with self.lock:
            self.poll()
            if os.path.isfile(self.buffer_file):
                shutil.copy(self.buffer_file, outfile)
            else:  # there was no logcat trace at this time
                touch(outfile)

    def close(self) -> None:
        """
        close the logcat poller and remove the temp log file
        """
        self.logger.debug('Closing poller')
        if os.path.isfile(self.buffer_file):
            os.remove(self.buffer_file)

    def poll(self) -> None:
        """
        poll logcat buffer and dump it to the log file
        """
        self.last_poll = time.time()
        self.target.dump_logcat(self.buffer_file, append=True, timeout=self.timeout, logcat_format='threadtime')
        self.target.clear_logcat()

    def insert_logcat_marker(self) -> None:
        """
        insert logcat marker for wrap detection
        """
        self.logger.debug('Inserting logcat marker')
        with self.lock:
            self.target.execute(
                'log -t "{}" "{}"'.format(
                    self._logcat_marker_tag,
                    self._logcat_marker_msg.format(self._marker_count)
                )
            )
            self._marker_count += 1

    def check_logcat_nowrap(self, outfile: str) -> bool:
        """
        check whether the logcat buffer is wrapping around or not
        """
        parser = LogcatParser()
        counter: Optional[int] = self._start_marker
        if not counter:
            return False
        for event in parser.parse(outfile):
            message: str = self._logcat_marker_msg.split(':')[0]
            if not (event.tag == self._logcat_marker_tag
                    and event.message.split(':')[0] == message):
                continue

            number = int(event.message.split(':')[1])
            if number > counter:
                return False
            elif number == counter:
                counter += 1

            if counter == self._end_marker:
                return True

        return False

    def start_logcat_wrap_detect(self) -> None:
        """
        start logcat wrap detection
        """
        with self.lock:
            self._start_marker = self._marker_count
            self.insert_logcat_marker()

    def stop_logcat_wrap_detect(self) -> None:
        """
        stop logcat wrap detection
        """
        with self.lock:
            self._end_marker = self._marker_count


class ChromeOsAssistant(LinuxAssistant):
    """
    assistant to connect to a ChromeOs target
    """
    parameters: List[Parameter] = LinuxAssistant.parameters + AndroidAssistant.parameters

    def __init__(self, target: ChromeOsTarget,
                 logcat_poll_period: Optional[int] = None, disable_selinux=True):
        super(ChromeOsAssistant, self).__init__(target)
        if target.supports_android and target.android_container:
            self.android_assistant: Optional[AndroidAssistant] = AndroidAssistant(target.android_container,
                                                                                  logcat_poll_period, disable_selinux)
        else:
            self.android_assistant = None

    def start(self) -> None:
        """
        start ChromeOs target
        """
        super(ChromeOsAssistant, self).start()
        if self.android_assistant:
            self.android_assistant.start()

    def extract_results(self, context: 'ExecutionContext') -> None:
        """
        extract execution results from target
        """
        super(ChromeOsAssistant, self).extract_results(context)
        if self.android_assistant:
            self.android_assistant.extract_results(context)

    def stop(self) -> None:
        """
        stop ChromeOs target
        """
        super(ChromeOsAssistant, self).stop()
        if self.android_assistant:
            self.android_assistant.stop()
