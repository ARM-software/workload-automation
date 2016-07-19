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
import wlauto.common.resources

from wlauto import AndroidUiAutoBenchmark, Parameter
from wlauto.exceptions import ValidationError
from wlauto.utils.types import list_of_strings

__version__ = '0.1.1'


class Googlephotos(AndroidUiAutoBenchmark):

    name = 'googlephotos'
    package = 'com.google.android.apps.photos'
    activity = 'com.google.android.apps.photos.home.HomeActivity'
    view = [package + '/com.google.android.apps.consumerphotoeditor.fragments.ConsumerPhotoEditorActivity',
            package + '/com.google.android.apps.photos.home.HomeActivity',
            package + '/com.google.android.apps.photos.localmedia.ui.LocalPhotosActivity',
            package + '/com.google.android.apps.photos.onboarding.AccountPickerActivity',
            package + '/com.google.android.apps.photos.onboarding.IntroActivity']
    description = """
    A workload to perform standard productivity tasks with Google Photos.  The workload carries out
    various tasks, such as browsing images, performing zooms, post-processing and saving a selected
    image to file.

    Test description:
    1. Four images are copied to the device
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

    default_test_images = [
        'uxperf_1200x1600.png', 'uxperf_1600x1200.jpg',
        'uxperf_2448x3264.png', 'uxperf_3264x2448.jpg',
    ]

    parameters = [
        Parameter('dumpsys_enabled', kind=bool, default=True,
                  description="""
                  If ``True`` turns on the action logger which outputs
                  timestamps to logcat for actions recorded in the workload.
                  """),
        Parameter('test_images', kind=list_of_strings, default=default_test_images,
                  description="""
                  A list of four image files to be pushed to the device.
                  Absolute file paths may be used but tilde expansion is not supported.
                  """),
    ]

    def validate(self):
        super(Googlephotos, self).validate()
        self.uiauto_params['package'] = self.package
        self.uiauto_params['output_dir'] = self.device.working_directory
        self.uiauto_params['dumpsys_enabled'] = self.dumpsys_enabled

        self._check_image_numbers()
        self._check_image_extensions()
        self._check_image_duplicates()
        self._info_image_used()

    def initialize(self, context):
        super(Googlephotos, self).initialize(context)
        for image in self.test_images:
            if os.path.exists(image):
                image_path = image
            else:
                image_path = context.resolver.get(wlauto.common.resources.File(self, image))
            self.device.push_file(image_path, self.device.working_directory, timeout=300)

        # Force a re-index of the mediaserver cache to pick up new files
        self.device.execute('am broadcast -a android.intent.action.MEDIA_MOUNTED -d file:///sdcard')

    def teardown(self, context):
        super(Googlephotos, self).teardown(context)
        self.device.execute('am broadcast -a android.intent.action.MEDIA_MOUNTED -d file:///sdcard')

    def finalize(self, context):
        super(Googlephotos, self).finalize(context)

        for entry in self.device.listdir(self.device.working_directory):
            if entry in self.test_images:
                self.device.delete_file(self.device.path.join(self.device.working_directory, entry))

        self.device.execute('am broadcast -a android.intent.action.MEDIA_MOUNTED -d file:///sdcard')

    # -------------------------------------------------------------------------
    # Internal methods
    # -------------------------------------------------------------------------

    def _check_image_extensions(self):
        for image in self.test_images:
            if not image.endswith(('jpg', 'jpeg', 'png')):
                raise ValidationError('{} must be a jpeg or png file'.format(image))

    def _check_image_numbers(self):
        if len(self.test_images) != 4:
            message = "This workload requires four test images - only {} specified"
            raise ValidationError(message.format(len(self.test_images)))

    def _check_image_duplicates(self):
        if len(self.test_images) != len(set(self.test_images)):
            raise ValidationError('Duplicate image names not allowed')

    def _info_image_used(self):
        if set(self.test_images) & set(self.default_test_images):
            self.logger.info('Using default test images')
        else:
            self.logger.warning('Using custom test images')
