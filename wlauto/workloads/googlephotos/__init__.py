#    Copyright 2014-2016 ARM Limited
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
import re

from wlauto import AndroidUiAutoBenchmark, Parameter
from wlauto.exceptions import DeviceError
from wlauto.exceptions import NotFoundError

__version__ = '0.1.0'


class Googlephotos(AndroidUiAutoBenchmark):

    name = 'googlephotos'
    package = 'com.google.android.apps.photos'
    activity = 'com.google.android.apps.photos.home.HomeActivity'
    view = [package+'/com.google.android.apps.consumerphotoeditor.fragments.ConsumerPhotoEditorActivity',
            package+'/com.google.android.apps.photos.home.HomeActivity',
            package+'/com.google.android.apps.photos.localmedia.ui.LocalPhotosActivity',
            package+'/com.google.android.apps.photos.onboarding.AccountPickerActivity',
            package+'/com.google.android.apps.photos.onboarding.IntroActivity']
    description = """
    A workload to perform standard productivity tasks with Google Photos.  The workload carries out
    various tasks, such as browsing images, performing zooms, post-processing and saving a selected
    image to file.

    Although this workload attempts to be network independent it requires a network connection
    (ideally, wifi) to run. This is because the welcome screen UI is dependent on an existing
    connection.

    Test description:
    1. Four images are copied to the devices
    2. The application is started in offline access mode
    3. Gestures are performed to swipe between images and pinch zoom in and out of the selected
       image
    4. The Colour of a selected image is edited by selecting the colour menu, incrementing the
       colour, resetting the colour and decrementing the colour using the seek bar.
    5. A Crop test is performed on a selected image.  UiAutomator does not allow the selection of
       the crop markers so the image is tilted positively, reset and then negatively to get a
       similar cropping effect.
    6. A Rotate test is performed on a selected image, rotating anticlockwise 90 degrees, 180
       degrees and 270 degrees.
    """

    parameters = [
        Parameter('dumpsys_enabled', kind=bool, default=True,
                  description="""
                  If ``True``, dumpsys captures will be carried out during the
                  test run.  The output is piped to log files which are then
                  pulled from the phone.
                  """),
    ]

    instrumentation_log = ''.join([name, '_instrumentation.log'])

    def __init__(self, device, **kwargs):
        super(Googlephotos, self).__init__(device, **kwargs)
        self.output_file = os.path.join(self.device.working_directory, self.instrumentation_log)

    def validate(self):
        super(Googlephotos, self).validate()
        self.uiauto_params['package'] = self.package
        self.uiauto_params['output_dir'] = self.device.working_directory
        self.uiauto_params['output_file'] = self.output_file
        self.uiauto_params['dumpsys_enabled'] = self.dumpsys_enabled

    def initialize(self, context):
        super(Googlephotos, self).initialize(context)

        # Check for workload dependencies before proceeding
        jpeg_files = [entry for entry in os.listdir(self.dependencies_directory) if entry.endswith(".jpg")]

        if len(jpeg_files) < 4:
            raise NotFoundError("This workload requires a minimum of four {} files in {}".format('jpg',
                                self.dependencies_directory))
        else:
            for entry in jpeg_files:
                self.device.push_file(os.path.join(self.dependencies_directory, entry),
                                      os.path.join(self.device.working_directory, entry),
                                      timeout=300)

        # Force a re-index of the mediaserver cache to pick up new files
        self.device.execute('am broadcast -a android.intent.action.MEDIA_MOUNTED -d file:///sdcard')

    def update_result(self, context):
        super(Googlephotos, self).update_result(context)

        self.device.pull_file(self.output_file, context.output_directory)
        result_file = os.path.join(context.output_directory, self.instrumentation_log)

        with open(result_file, 'r') as wfh:
            pattern = r'(?P<key>\w+)\s+(?P<value1>\d+)\s+(?P<value2>\d+)\s+(?P<value3>\d+)'
            regex = re.compile(pattern)
            for line in wfh:
                match = regex.search(line)
                if match:
                    context.result.add_metric((match.group('key') + "_start"),
                                              match.group('value1'), units='ms')
                    context.result.add_metric((match.group('key') + "_finish"),
                                              match.group('value2'), units='ms')
                    context.result.add_metric((match.group('key') + "_duration"),
                                              match.group('value3'), units='ms')

    def teardown(self, context):
        super(Googlephotos, self).teardown(context)

        regex = re.compile(r'^\w+~\d+\.jpg$')

        for entry in self.device.listdir(self.device.working_directory):
            match = regex.search(entry)
            if entry.endswith(".log"):
                self.device.pull_file(os.path.join(self.device.working_directory, entry),
                                      context.output_directory)
                self.device.delete_file(os.path.join(self.device.working_directory, entry))

            # Clean up edited files on each iteration
            if match:
                self.device.delete_file(os.path.join(self.device.working_directory, entry))

        self.device.execute('am broadcast -a android.intent.action.MEDIA_MOUNTED -d file:///sdcard')

    def finalize(self, context):
        super(Googlephotos, self).finalize(context)

        for entry in self.device.listdir(self.device.working_directory):
            if entry.endswith(".jpg"):
                self.device.delete_file(os.path.join(self.device.working_directory, entry))

        # Force a re-index of the mediaserver cache to removed cached files
        self.device.execute('am broadcast -a android.intent.action.MEDIA_MOUNTED -d file:///sdcard')
