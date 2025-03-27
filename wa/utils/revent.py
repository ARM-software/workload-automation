#    Copyright 2016-2018 ARM Limited
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
import struct
import signal
from datetime import datetime
from collections import namedtuple

from devlib.utils.misc import memoized

from wa.framework.resource import Executable, NO_ONE, ResourceResolver
from wa.utils.exec_control import once_per_class
from typing import (TYPE_CHECKING, IO, Tuple, Any, List, Union,
                    Optional, cast, Generator)
if TYPE_CHECKING:
    from devlib.target import Target

GENERAL_MODE: int = 0
GAMEPAD_MODE: int = 1


u16_struct = struct.Struct('<H')
u32_struct = struct.Struct('<I')
u64_struct = struct.Struct('<Q')

# See revent section in WA documentation for the detailed description of
# the recording format.
header_one_struct = struct.Struct('<6sH')
header_two_struct = struct.Struct('<H6x')  # version 2 onwards

devid_struct = struct.Struct('<4H')
devinfo_struct = struct.Struct('<4s96s96s96sI')
absinfo_struct = struct.Struct('<7i')

event_struct = struct.Struct('<HqqHHi')
old_event_struct = struct.Struct("<i4xqqHHi")  # prior to version 2


def read_struct(fh: IO, struct_spec: struct.Struct) -> Tuple[Any, ...]:
    """
    read struct
    """
    data = fh.read(struct_spec.size)
    return struct_spec.unpack(data)


def read_string(fh: IO) -> str:
    """
    read string from struct
    """
    length, = read_struct(fh, u32_struct)
    str_struct = struct.Struct('<{}s'.format(length))
    return read_struct(fh, str_struct)[0]


def count_bits(bitarr: List[int]) -> int:
    """
    count bits in bit array
    """
    return sum(bin(b).count('1') for b in bitarr)


def is_set(bitarr: List[int], bit: int) -> int:
    """
    check if bit is set
    """
    byte = bit // 8
    bytebit = bit % 8
    return bitarr[byte] & bytebit


absinfo = namedtuple('absinfo', 'ev_code value min max fuzz flat resolution')


class UinputDeviceInfo(object):
    """
    Uinput device information
    """
    def __init__(self, fh: IO):
        parts: Tuple[Any, ...] = read_struct(fh, devid_struct)
        self.bustype: int = parts[0]
        self.vendor: int = parts[1]
        self.product: int = parts[2]
        self.version: int = parts[3]

        self.name: str = read_string(fh)

        parts = read_struct(fh, devinfo_struct)
        self.ev_bits = bytearray(parts[0])
        self.key_bits = bytearray(parts[1])
        self.rel_bits = bytearray(parts[2])
        self.abs_bits = bytearray(parts[3])
        self.num_absinfo: int = parts[4]
        self.absinfo: List[absinfo] = [absinfo(*read_struct(fh, absinfo_struct))
                                       for _ in range(self.num_absinfo)]

    def __str__(self) -> str:
        return 'UInputInfo({})'.format(self.__dict__)


class ReventEvent(object):
    """
    represents an revent event
    """
    def __init__(self, fh: IO, legacy: bool = False):
        if not legacy:
            dev_id, ts_sec, ts_usec, type_, code, value = read_struct(fh, event_struct)
        else:
            dev_id, ts_sec, ts_usec, type_, code, value = read_struct(fh, old_event_struct)
        self.device_id = dev_id
        self.time = datetime.fromtimestamp(ts_sec + float(ts_usec) / 1000000)
        self.type = type_
        self.code = code
        self.value = value

    def __str__(self):
        return 'InputEvent({})'.format(self.__dict__)


class ReventRecording(object):
    """
    Represents a parsed revent recording. This contains input events and device
    descriptions recorded by revent. Two parsing modes are supported. By
    default, the recording will be parsed in the "streaming" mode. In this
    mode, initial headers and device descriptions are parsed on creation and an
    open file handle to the recording is saved. Events will be read from the
    file as they are being iterated over. In this mode, the entire recording is
    never loaded into memory at once. The underlying file may be "released" by
    calling ``close`` on the recording, after which further iteration over the
    events will not be possible (but would still be possible to access the file
    description and header information).

    The alternative is to load the entire recording on creation (in which case
    the file handle will be closed once the recording is loaded). This can be
    enabled by specifying ``streaming=False``. This will make it faster to
    subsequently iterate over the events, and also will not "hold" the file
    open.

    .. note:: When starting a new iteration over the events in streaming mode,
              the postion in the open file will be automatically reset to the
              beginning of the event stream. This means it's possible to iterate
              over the events multiple times without having to re-open the
              recording, however it is not possible to do so in parallel. If
              parallel iteration is required, streaming should be disabled.

    """

    def __init__(self, f: Union[str, IO], stream: bool = True):
        self.device_paths: List[str] = []
        self.gamepad_device: Optional[UinputDeviceInfo] = None
        self.num_events: Optional[int] = None
        self.stream = stream
        self._events: Optional[List[ReventEvent]] = None
        self._close_when_done: bool = False
        self._events_start: Optional[int] = None
        self._duration: Optional[Union[int, float]] = None

        if hasattr(f, 'name'):  # file-like object
            self.filepath: str = cast(IO, f).name
            self.fh: Optional[IO] = cast(IO, f)
        else:  # path to file
            self.filepath = cast(str, f)
            self.fh = open(self.filepath, 'rb')
            if not self.stream:
                self._close_when_done = True
        try:
            self._parse_header_and_devices(self.fh)
            self._events_start = self.fh.tell()
            if not self.stream:
                self._events = list(self._iter_events())
        finally:
            if self._close_when_done:
                self.close()

    @property
    def duration(self) -> Optional[Union[float, int]]:
        """
        recording duration in seconds
        """
        if self._duration is None:
            if self.stream:
                events: Generator[ReventEvent, Any, None] = self._iter_events()
                try:
                    first = last = next(events)
                except StopIteration:
                    self._duration = 0
                for last in events:
                    pass
                self._duration = (last.time - first.time).total_seconds()
            else:  # not streaming
                if not self._events:
                    self._duration = 0
                else:
                    self._duration = (self._events[-1].time
                                      - self._events[0].time).total_seconds()
        return self._duration

    @property
    def events(self) -> Union[Generator[ReventEvent, Any, None],
                              Optional[List[ReventEvent]]]:
        """
        Revent events
        """
        if self.stream:
            return self._iter_events()
        else:
            return self._events

    def close(self) -> None:
        """
        close file handle
        """
        if self.fh is not None:
            self.fh.close()
            self.fh = None
            self._events_start = None

    def _parse_header_and_devices(self, fh: IO) -> None:
        """
        parse header and devices
        """
        magic, version = read_struct(fh, header_one_struct)
        if magic != b'REVENT':
            msg: str = '{} does not appear to be an revent recording'
            raise ValueError(msg.format(self.filepath))
        self.version = version

        if 3 >= self.version >= 2:
            self.mode, = read_struct(fh, header_two_struct)
            if self.mode == GENERAL_MODE:
                self._read_devices(fh)
            elif self.mode == GAMEPAD_MODE:
                self._read_gamepad_info(fh)
            else:
                raise ValueError('Unexpected recording mode: {}'.format(self.mode))
            self.num_events, = read_struct(fh, u64_struct)
            if self.version > 2:
                ts_sec: float = read_struct(fh, u64_struct)[0]
                ts_usec: float = read_struct(fh, u64_struct)[0]
                self.start_time = datetime.fromtimestamp(ts_sec + float(ts_usec) / 1000000)
                ts_sec = read_struct(fh, u64_struct)[0]
                ts_usec = read_struct(fh, u64_struct)[0]
                self.end_time = datetime.fromtimestamp(ts_sec + float(ts_usec) / 1000000)

        elif 2 > self.version >= 0:
            self.mode = GENERAL_MODE
            self._read_devices(fh)
        else:
            raise ValueError('Invalid recording version: {}'.format(self.version))

    def _read_devices(self, fh: IO) -> None:
        """
        read devices
        """
        num_devices, = read_struct(fh, u32_struct)
        for _ in range(num_devices):
            self.device_paths.append(read_string(fh))

    def _read_gamepad_info(self, fh: IO) -> None:
        """
        read gamepad info
        """
        self.gamepad_device = UinputDeviceInfo(fh)
        self.device_paths.append('[GAMEPAD]')

    def _iter_events(self) -> Generator[ReventEvent, Any, None]:
        """
        iterate over recorded events
        """
        if self.fh is None:
            msg: str = 'Attempting to iterate over events of a closed recording'
            raise RuntimeError(msg)
        self.fh.seek(self._events_start or 0)
        if self.version >= 2:
            for _ in range(self.num_events or 0):
                yield ReventEvent(self.fh)
        else:
            file_size: int = os.path.getsize(self.filepath)
            while self.fh.tell() < file_size:
                yield ReventEvent(self.fh, legacy=True)

    def __iter__(self):
        if self.events:
            for event in self.events:
                yield event

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def __del__(self):
        self.close()


def get_revent_binary(abi: str) -> Optional[str]:
    """
    get revent binary
    """
    resolver = ResourceResolver()
    resolver.load()
    resource = Executable(NO_ONE, abi, 'revent')
    return resolver.get(resource)


class ReventRecorder(object):
    """
    revent recorder
    """
    # Share location of target excutable across all instances
    target_executable: Optional[str] = None

    def __init__(self, target: 'Target'):
        self.target = target
        if not ReventRecorder.target_executable:
            ReventRecorder.target_executable = self._get_target_path(self.target)

    @once_per_class
    def deploy(self) -> None:
        """
        deploy the revent recorder
        """
        if not ReventRecorder.target_executable:
            ReventRecorder.target_executable = self.target.get_installed('revent')
        host_executable = get_revent_binary(self.target.abi or '')
        ReventRecorder.target_executable = self.target.install(host_executable)

    @once_per_class
    def remove(self) -> None:
        """
        uninstall revent on target
        """
        if ReventRecorder.target_executable:
            self.target.uninstall('revent')

    def start_record(self, revent_file: str) -> None:
        """
        start recording
        """
        command: str = '{} record -s {}'.format(ReventRecorder.target_executable, revent_file)
        self.target.kick_off(command, self.target.is_rooted)

    def stop_record(self) -> None:
        """
        stop recording
        """
        self.target.killall('revent', signal.SIGINT, as_root=self.target.is_rooted)

    def replay(self, revent_file: str, timeout: Optional[int] = None) -> None:
        """
        replay the recording
        """
        self.target.killall('revent')
        command: str = "{} replay {}".format(ReventRecorder.target_executable, revent_file)
        self.target.execute(command, timeout=timeout)

    @memoized
    @staticmethod
    def _get_target_path(target: 'Target') -> str:
        """
        get path of revent installation on target
        """
        return target.get_installed('revent')
