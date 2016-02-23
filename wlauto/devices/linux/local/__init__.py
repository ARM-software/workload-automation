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


from wlauto import LocalLinuxDevice, Parameter

class Local(LocalLinuxDevice):
    name = 'local_linux'
    description = """
    A local Linux device interface.

    This should allow basic WA functionality on most local Linux devices. Some additional
    configuration may be required for some WA extensions
    (e.g. configuring ``core_names`` and ``core_clusters``).

    """

    abi = 'armeabi'
    has_gpu = True

    parameters = [
        Parameter('core_names', default=[], override=True),
        Parameter('core_clusters', default=[], override=True),
    ]
