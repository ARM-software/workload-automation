
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


from wlauto import LinuxDevice, Parameter
from wlauto.utils.misc import convert_new_lines
import re


class ChromeOsDevice(LinuxDevice):

    name = "generic_chromeos"
    description = """
    Chrome OS generic device. Use this if you are workng on a chrome OS device and you
    do not have a device file specific to your device.

    """

    platform = 'chromeos'
    abi = 'armeabi'
    has_gpu = True
    default_timeout = 100

    parameters = [
        Parameter('core_names', default=[], override=True),
        Parameter('core_clusters', default=[], override=True),
        Parameter('username', default='root', override=True),
        Parameter('password', default='test0000', override=True),
        Parameter('password_prompt', default='Password:', override=True),
        Parameter('binaries_directory', default='/usr/local/bin', override=True),
        Parameter('working_directory', default='/home/root/wa-working', override=True),
    ]

    def initialize(self, context, *args, **kwargs):
        self.uninstall('busybox')  # busybox that comes with chromeos is missing some usefull utilities
        super(ChromeOsDevice, self).initialize(context, *args, **kwargs)

