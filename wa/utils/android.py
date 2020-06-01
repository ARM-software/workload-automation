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
from datetime import datetime

from devlib.utils.android import ApkInfo as _ApkInfo

from wa import settings
from wa.framework.exception import ConfigError
from wa.utils.serializer import read_pod, write_pod, Podable
from wa.utils.types import enum
from wa.utils.misc import lock_file


LogcatLogLevel = enum(['verbose', 'debug', 'info', 'warn', 'error', 'assert'], start=2)

log_level_map = ''.join(n[0].upper() for n in LogcatLogLevel.names)

logger = logging.getLogger('logcat')


class LogcatEvent(object):

    __slots__ = ['timestamp', 'pid', 'tid', 'level', 'tag', 'message']

    def __init__(self, timestamp, pid, tid, level, tag, message):
        self.timestamp = timestamp
        self.pid = pid
        self.tid = tid
        self.level = level
        self.tag = tag
        self.message = message

    def __repr__(self):
        return '{} {} {} {} {}: {}'.format(
            self.timestamp, self.pid, self.tid,
            self.level.name.upper(), self.tag,
            self.message,
        )

    __str__ = __repr__


class LogcatParser(object):

    def parse(self, filepath):
        with open(filepath, errors='replace') as fh:
            for line in fh:
                event = self.parse_line(line)
                if event:
                    yield event

    def parse_line(self, line):  # pylint: disable=no-self-use
        line = line.strip()
        if not line or line.startswith('-') or ': ' not in line:
            return None

        metadata, message = line.split(': ', 1)

        parts = metadata.split(None, 5)
        try:
            ts = ' '.join([parts.pop(0), parts.pop(0)])
            timestamp = datetime.strptime(ts, '%m-%d %H:%M:%S.%f').replace(year=datetime.now().year)
            pid = int(parts.pop(0))
            tid = int(parts.pop(0))
            level = LogcatLogLevel.levels[log_level_map.index(parts.pop(0))]
            tag = (parts.pop(0) if parts else '').strip()
        except Exception as e:  # pylint: disable=broad-except
            message = 'Invalid metadata for line:\n\t{}\n\tgot: "{}"'
            logger.warning(message.format(line, e))
            return None

        return LogcatEvent(timestamp, pid, tid, level, tag, message)


class ApkInfo(_ApkInfo, Podable):
    # Implement ApkInfo as a Podable class.

    _pod_serialization_version = 1

    @staticmethod
    def from_pod(pod):
        instance = ApkInfo()
        instance.path = pod['path']
        instance.package = pod['package']
        instance.activity = pod['activity']
        instance.label = pod['label']
        instance.version_name = pod['version_name']
        instance.version_code = pod['version_code']
        instance.native_code = pod['native_code']
        instance.permissions = pod['permissions']
        instance._apk_path = pod['_apk_path']
        instance._activities = pod['_activities']
        instance._methods = pod['_methods']
        return instance

    def __init__(self, path=None):
        super().__init__(path)
        self._pod_version = self._pod_serialization_version

    def to_pod(self):
        pod = super().to_pod()
        pod['path'] = self.path
        pod['package'] = self.package
        pod['activity'] = self.activity
        pod['label'] = self.label
        pod['version_name'] = self.version_name
        pod['version_code'] = self.version_code
        pod['native_code'] = self.native_code
        pod['permissions'] = self.permissions
        pod['_apk_path'] = self._apk_path
        pod['_activities'] = self.activities  # Force extraction
        pod['_methods'] = self.methods  # Force extraction
        return pod

    @staticmethod
    def _pod_upgrade_v1(pod):
        pod['_pod_version'] = pod.get('_pod_version', 1)
        return pod

