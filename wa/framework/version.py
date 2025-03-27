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
from collections import namedtuple
from subprocess import Popen, PIPE
from typing import Optional

VersionTuple = namedtuple('VersionTuple', ['major', 'minor', 'revision', 'dev'])

version = VersionTuple(3, 4, 0, 'dev1')

required_devlib_version = VersionTuple(1, 4, 0, 'dev3')


def format_version(v: VersionTuple) -> str:
    """
    create version string from version tuple
    """
    version_string: str = '{}.{}.{}'.format(
        v.major, v.minor, v.revision)
    if v.dev:
        version_string += '.{}'.format(v.dev)
    return version_string


def get_wa_version() -> str:
    """
    get workload automation version
    """
    return format_version(version)


def get_wa_version_with_commit() -> str:
    """
    get workload automation version with commit id
    """
    version_string: str = get_wa_version()
    commit: Optional[str] = get_commit()
    if commit:
        return '{}+{}'.format(version_string, commit)
    else:
        return version_string


def get_commit() -> Optional[str]:
    """
    get commit id of workload automation
    """
    try:
        p = Popen(['git', 'rev-parse', 'HEAD'],
                  cwd=os.path.dirname(__file__), stdout=PIPE, stderr=PIPE)
    except FileNotFoundError:
        return None
    std, _ = p.communicate()
    p.wait()
    if p.returncode:
        return None
    return std[:8].decode(sys.stdout.encoding or 'utf-8')
