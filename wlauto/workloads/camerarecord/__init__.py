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

from wlauto import UiAutomatorWorkload, Parameter
from wlauto.utils.types import range_dict
from wlauto.exceptions import WorkloadError


class Camerarecord(UiAutomatorWorkload):

    name = 'camerarecord'
    description = """
    Uses in-built Android camera app to record the video for given interval
    of time.

    """
    package = 'com.google.android.gallery3d'
    activity = 'com.android.camera.CameraActivity'
    run_timeout = 0
    camera_modes = ['normal', 'slow_motion']

    api_packages = range_dict()
    api_packages[1] = 'com.google.android.gallery3d'
    api_packages[23] = 'com.google.android.GoogleCamera'

    parameters = [
        Parameter('recording_time', kind=int, default=60,
                  description='The video recording time in seconds.'),
        Parameter('recording_mode', kind=str, allowed_values=camera_modes,
                  default='normal', description='The video recording mode.'),
    ]

    def initialize(self, context):
        self.uiauto_params['recording_time'] = self.recording_time  # pylint: disable=E1101
        self.uiauto_params['version'] = "button"
        self.run_timeout = 3 * self.uiauto_params['recording_time']
        api = self.device.get_sdk_version()
        self.uiauto_params['api_level'] = api
        self.package = self.api_packages[api]
        version = self.device.get_installed_package_version(self.package)
        version = version.replace(' ', '_')
        self.uiauto_params['version'] = version
        self.uiauto_params['recording_mode'] = self.recording_mode

    def setup(self, context):
        if self.recording_mode != 'normal':
            if self.device.get_sdk_version() < 23:
                raise WorkloadError('{} recording mode only supported by '
                                    'Android version M onwards'
                                    .format(self.recording_mode))

        super(Camerarecord, self).setup(context)
        # Start camera activity
        self.device.execute('am start -n {}/{}'.format(self.package, self.activity))
        # Reset framestats collection
        self.device.execute('dumpsys gfxinfo {} reset'.format(self.package))

    def teardown(self, context):
        # Collect framestats
        framestats_file = self.device.path.join(self.device.working_directory,
                                                'framestats.txt')
        self.device.execute('dumpsys gfxinfo {} > {}'
                            .format(self.package, framestats_file))
        self.device.pull_file(framestats_file,
                              context.output_directory,
                              as_root=True)
        self.device.delete_file(framestats_file)

        # Stop the activity
        self.device.execute('am force-stop {}'.format(self.package))
        super(Camerarecord, self).teardown(context)
