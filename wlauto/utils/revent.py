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

import struct
import datetime
import os


class ReventParser(object):
    """
    Parses revent binary recording files so they can be easily read within python.
    """

    int32_struct = struct.Struct("<i")
    header_struct = struct.Struct("<6sH")
    event_struct = struct.Struct("<i4xqqHHi")

    def __init__(self):
        self.path = None
        self.device_paths = []

    def parse(self, path):
        ReventParser.check_revent_file(path)

        with open(path, "rb") as f:
            _read_struct(f, ReventParser.header_struct)
            path_count, = _read_struct(f, self.int32_struct)
            for _ in xrange(path_count):
                path_length, = _read_struct(f, self.int32_struct)
                if path_length >= 30:
                    raise ValueError("path length too long. corrupt file")
                self.device_paths.append(f.read(path_length))

            while f.tell() < os.path.getsize(path):
                device_id, sec, usec, typ, code, value = _read_struct(f, self.event_struct)
                yield (device_id, datetime.datetime.fromtimestamp(sec + float(usec) / 1000000),
                       typ, code, value)

    @staticmethod
    def check_revent_file(path):
        """
        Checks whether a file starts with "REVENT"
        """
        with open(path, "rb") as f:
            magic, file_version = _read_struct(f, ReventParser.header_struct)

            if magic != "REVENT":
                msg = "'{}' isn't an revent file, are you using an old recording?"
                raise ValueError(msg.format(path))
            return file_version

    @staticmethod
    def get_revent_duration(path):
        """
        Takes an ReventParser and returns the duration of the revent recording in seconds.
        """
        revent_parser = ReventParser().parse(path)
        first = last = next(revent_parser)
        for last in revent_parser:
            pass
        return (last[1] - first[1]).total_seconds()


def _read_struct(f, struct_spec):
    data = f.read(struct_spec.size)
    return struct_spec.unpack(data)
