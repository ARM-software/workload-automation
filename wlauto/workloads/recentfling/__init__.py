#    Copyright 2013-2015 ARM Limited
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

#pylint: disable=E1101,W0201

import os
import re
from collections import defaultdict

from wlauto import Workload, Parameter, File
from wlauto.utils.types import caseless_string
from wlauto.exceptions import WorkloadError, DeviceError


class Recentfling(Workload):

    name = 'recentfling'
    description = """
    Tests UI jank on android devices.

    For this workload to work, ``recentfling.sh`` and ``defs.sh`` must be placed
    in ``~/.workload_automation/dependencies/recentfling/``. These can be found
    in the `AOSP Git repository <https://android.googlesource.com/platform/system/extras/+/master/tests/workloads>`_.

    To change the apps that are opened at the start of the workload you will need
    to modify the ``defs.sh`` file. You will need to add your app to ``dfltAppList``
    and then add a variable called ``{app_name}Activity`` with the name of the
    activity to launch (where ``{add_name}`` is the name you put into ``dfltAppList``).

    You can get a list of activities available on your device by running
    ``adb shell pm list packages -f``
    """
    supported_platforms = ['android']

    parameters = [
        Parameter('loops', kind=int, default=3,
                  description="The number of test iterations."),
        Parameter('start_apps', kind=bool, default=True,
                  description="""
                  If set to ``False``,no apps will be started before flinging
                  through the recent apps list (in which the assumption is
                  there are already recently started apps in the list.
                  """),
    ]

    def initialise(self, context):  # pylint: disable=no-self-use
        if context.device.get_sdk_version() < 23:
            raise WorkloadError("This workload relies on ``dumpsys gfxinfo`` \
                                 only present in Android M and onwards")

    def setup(self, context):
        self.defs_host = context.resolver.get(File(self, "defs.sh"))
        self.defs_target = self.device.install(self.defs_host)
        self.recentfling_host = context.resolver.get(File(self, "recentfling.sh"))
        self.recentfling_target = self.device.install(self.recentfling_host)
        self._kill_recentfling()
        self.device.ensure_screen_is_on()

    def run(self, context):
        args = '-i {} '.format(self.loops)
        if not self.start_apps:
            args += '-N '
        cmd = "echo $$>{dir}/pidfile; cd {bindir}; exec ./recentfling.sh {args}; rm {dir}/pidfile"
        cmd = cmd.format(args=args, dir=self.device.working_directory, bindir=self.device.binaries_directory)
        try:
            self.output = self.device.execute(cmd, timeout=120)
        except KeyboardInterrupt:
            self._kill_recentfling()
            raise

    def update_result(self, context):
        group_names = ["90th Percentile", "95th Percentile", "99th Percentile", "Jank", "Jank%"]
        count = 0
        for line in self.output.strip().splitlines():
            p = re.compile("Frames: \d+ latency: (?P<pct90>\d+)/(?P<pct95>\d+)/(?P<pct99>\d+) Janks: (?P<jank>\d+)\((?P<jank_pct>\d+)%\)")
            match = p.search(line)
            if match:
                count += 1
                if line.startswith("AVE: "):
                    group_names = ["Average " + g for g in group_names]
                    count = 0
                for metric in zip(group_names, match.groups()):
                    context.result.add_metric(metric[0],
                                              metric[1],
                                              None,
                                              classifiers={"loop": count or "Average"})

    def teardown(self, context):
        self.device.uninstall_executable(self.recentfling_target)
        self.device.uninstall_executable(self.defs_target)

    def _kill_recentfling(self):
        command = 'cat {}/pidfile'.format(self.device.working_directory)
        try:
            pid = self.device.execute(command)
            if pid.strip():
                self.device.kill(pid.strip(), signal='SIGKILL')
        except DeviceError:
            pass  # may have already been deleted
