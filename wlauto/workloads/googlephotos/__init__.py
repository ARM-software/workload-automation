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

from wlauto import AndroidUxPerfWorkload, Parameter
from wlauto.exceptions import ValidationError
from wlauto.utils.types import list_of_strings
from wlauto.utils.misc import unique


class Googlephotos(AndroidUxPerfWorkload):

    name = 'googlephotos'
    package = 'com.google.android.apps.photos'
    min_apk_version = '1.21.0.123444480'
    activity = 'com.google.android.apps.photos.home.HomeActivity'
    view = [package + '/com.google.android.apps.consumerphotoeditor.fragments.ConsumerPhotoEditorActivity',
            package + '/com.google.android.apps.photos.home.HomeActivity',
            package + '/com.google.android.apps.photos.localmedia.ui.LocalPhotosActivity',
            package + '/com.google.android.apps.photos.onboarding.AccountPickerActivity',
            package + '/com.google.android.apps.photos.onboarding.IntroActivity']
    description = '''
    A workload to perform standard productivity tasks with Google Photos. The workload carries out
    various tasks, such as browsing images, performing zooms, and post-processing the image.

    Test description:

    1. Four images are copied to the device
    2. The application is started in offline access mode
    3. Gestures are performed to pinch zoom in and out of the selected image
    4. The colour of a selected image is edited by selecting the colour menu, incrementing the
       colour, resetting the colour and decrementing the colour using the seek bar.
    5. A crop test is performed on a selected image.  UiAutomator does not allow the selection of
       the crop markers so the image is tilted positively, reset and then tilted negatively to get a
       similar cropping effect.
    6. A rotate test is performed on a selected image, rotating anticlockwise 90 degrees, 180
       degrees and 270 degrees.
    '''

    default_test_images = [
        'uxperf_1200x1600.png', 'uxperf_1600x1200.jpg',
        'uxperf_2448x3264.png', 'uxperf_3264x2448.jpg',
    ]

    parameters = [
        Parameter('test_images', kind=list_of_strings, default=default_test_images,
                  constraint=lambda x: len(unique(x)) == 4,
                  description='''
                  A list of four JPEG and/or PNG files to be pushed to the device.
                  Absolute file paths may be used but tilde expansion must be escaped.
                  '''),
    ]

    def __init__(self, device, **kwargs):
        super(Googlephotos, self).__init__(device, **kwargs)
        self.deployable_assets = self.test_images

    def validate(self):
        super(Googlephotos, self).validate()
        # Only accept certain image formats
        for image in self.test_images:
            if os.path.splitext(image.lower())[1] not in ['.jpg', '.jpeg', '.png']:
                raise ValidationError('{} must be a JPEG or PNG file'.format(image))

    def setup(self, context):
        super(Googlephotos, self).setup(context)
        # Create a subfolder for each test_image named ``wa-[1-4]``
        # Move each image into its subfolder
        # This is to guarantee ordering and allows the workload to select a specific
        # image by subfolder, as filenames are not shown easily within the app
        d = self.device.working_directory
        for i, f in enumerate(self.test_images):
            self.device.execute('mkdir -p {0}/wa-{1}'.format(d, i + 1))
            self.device.execute('mv {0}/{2} {0}/wa-{1}/{2}'.format(d, i + 1, f))
        # Force rescan
        self.device.broadcast_media_mounted(self.device.working_directory)

    def teardown(self, context):
        super(Googlephotos, self).teardown(context)
        # Remove the subfolders and its content
        d = self.device.working_directory
        for i in xrange(len(self.test_images)):
            self.device.execute('rm -rf {0}/wa-{1}'.format(d, i + 1))
        # Force rescan
        self.device.broadcast_media_mounted(self.device.working_directory)
