#    Copyright 2016 Linaro Limited
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
# Author: Milosz Wasilewski <milosz.wasilewski@linaro.org>
# pylint: disable=E1101,W0201
import os
import time
import urllib
import shutil
import re
import zipfile

from wlauto import (
    settings,
    Parameter,
    UiAutomatorWorkload
)
from wlauto.exceptions import WorkloadError
from wlauto.utils.types import boolean

# Use master from github as there is no better candidate
LOGCAT_FILE_NAME = "browser_octane2_logcat.txt"

class Octane2(UiAutomatorWorkload):

    name = 'octane2'
    description = """
    Octane 2 is a JavaScript benchmark for browser

    """
    octane_jar_file = 'org.linaro.wlauto.uiauto.octane2.jar'
    octane_run_string = 'org.linaro.wlauto.uiauto.octane2.UiAutomation#runUiAutomation'

    parameters = [
        Parameter('force_dependency_push', kind=boolean, default=False,
                  description=('Specifies whether to push dependency files to the device'
                               'if they are already on it.')),
        Parameter('perform_cleanup', kind=boolean, default=False,
                  description='If ``True``, workload files on the device will be deleted after execution.'),
        Parameter('browser_package', default='org.chromium.chrome',
                  description='Specifies the package name of the device\'s browser app.'),
        Parameter('browser_activity', default='.browser.ChromeTabbedActivity',
                  description='Specifies the startup activity  name of the device\'s browser app.'),
        Parameter('octane_archive', default="https://github.com/chromium/octane/archive/master.zip",
                  description='URL of the octane zip file to be downloaded in case it is absent \
                  from dependencies directory'),
        Parameter('octane_filename', default="octane2.zip",
                  description='File name that is downloaded from octane_archive'),
        Parameter('octane_timeout', kind=int, default=900,
                  description='Specifies the timeout (in seconds) before the uiautomator script is terminated.'),
        Parameter('clear_file_cache', kind=boolean, default=True,
                  description='Clear the the file cache on the target device prior to running the workload.'),
    ]

    supported_platforms = ['android']

    def setup(self, context):  # NOQA
        UiAutomatorWorkload.setup(self, context)
        self.octane2_on_device = self.device.path.join(self.device.working_directory, self.name)
        self.index_octane = 'file://{}'.format(self.octane2_on_device) + '/index.html'

        # assume that it's enough to have index.html in the dependencies
        if not os.path.isdir(self.dependencies_directory) or \
              not os.path.exists(os.path.join(self.dependencies_directory, "index.html")):
            self._download_octane2_file()

        # Push the octane2
        if self.force_dependency_push or not self.device.file_exists(
                os.path.join(self.octane2_on_device, "index.html")):
            self.logger.debug('Copying octane2 to device.')
            self.device.push_file(self.dependencies_directory, self.octane2_on_device, timeout=300)

        # Stop the browser if already running and wait for it to stop
        self.device.execute('am force-stop {}'.format(self.browser_package))

        # Clear the logs
        self.device.clear_logcat()

        # clear browser cache
        self.device.execute('pm clear {}'.format(self.browser_package))
        if self.clear_file_cache:
            self.device.execute('sync')
            self.device.set_sysfile_value('/proc/sys/vm/drop_caches', 3)

        #On android 6+ the web browser requires permissions to access the sd card
        if self.device.get_sdk_version() >= 23:
            self.device.execute("pm grant {} android.permission.READ_EXTERNAL_STORAGE".format(self.browser_package))
            self.device.execute("pm grant {} android.permission.WRITE_EXTERNAL_STORAGE".format(self.browser_package))


    def run(self, context):
        # Launch browser
        self.device.execute('am start -W -n  {}/{} {}'.format(self.browser_package, self.browser_activity, self.index_octane))
        # Launch automation script
        self.logger.debug('working directory: {}'.format(self.device.working_directory))
        command = 'uiautomator runtest {} -e workdir {} -c {}'.format(
            os.path.join(self.device.working_directory, self.octane_jar_file),
            self.device.working_directory,
            self.octane_run_string)
        self.device.execute(command, timeout=self.octane_timeout)

    def update_result(self, context):
        # Stop the browser
        self.device.execute('am force-stop {}'.format(self.browser_package))

        # Get the logs
        output_file = os.path.join(self.device.working_directory, LOGCAT_FILE_NAME)
        self.device.execute('logcat -v time -d > {}'.format(output_file))
        self.device.pull_file(output_file, context.output_directory)

        metrics = _parse_metrics(os.path.join(context.output_directory, LOGCAT_FILE_NAME))
        if not metrics:
            raise WorkloadError('No Octane2 metrics extracted from Logcat')

        summary_result = 1.
        for key, value in metrics:
            summary_result = summary_result * float(value)
            context.result.add_metric(key, value, units='points', lower_is_better=False)
        context.result.add_metric(
            "Octane2 Score",
            float(summary_result)**(1./float(len(metrics))),
            units='points',
            lower_is_better=False)

    def teardown(self, context):
        super(Octane2, self).teardown(context)
        if self.perform_cleanup:
            self.device.execute('rm -r {}'.format(
                os.path.join(self.device.working_directory, LOGCAT_FILE_NAME)))
            self.device.execute('rm -r {}'.format(self.octane2_on_device))

    def _download_octane2_file(self):
        # downloading the file to dependencies
        self.logger.debug('Downloading octane2 dependencies.')
        full_file_path = os.path.join(self.dependencies_directory, self.octane_filename)
        urllib.urlretrieve(self.octane_archive, full_file_path)

        # Extracting Octane2 to dependencies/octane2
        self.logger.debug('Extracting octane2 dependencies.')
        zip_file = zipfile.ZipFile(full_file_path)
        self.logger.debug("Extracting {}".format(full_file_path))
        # skip top level directory (works for github)
        for member in zip_file.namelist():
            self.logger.debug("Extracting file {}".format(member))
            member_data = zip_file.read(member, self.dependencies_directory)
            new_member_path = os.path.join(self.dependencies_directory, member.split("/", 1)[1])
            if not new_member_path.endswith("/"):
                self.logger.debug("New file path {}".format(new_member_path))
                new_member = open(new_member_path, "wb")
                new_member.write(member_data)
                new_member.close()
            else:
                if not os.path.exists(new_member_path):
                    os.makedirs(new_member_path)
        zip_file.close()

        os.unlink(full_file_path)

def _parse_metrics(logfile):
    regex_octanescore = re.compile(r'OCTANE2 RESULT: (?P<name>\w+)\s+(?P<score>\d+)')

    results_list = []
    with open(logfile) as fh:
        for line in fh:
            result = regex_octanescore.search(line)
            if result:
                results_list.append((result.group("name"), int(result.group("score"))))

    return results_list
