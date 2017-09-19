#    Copyright 2017 ARM Limited
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

from time import sleep

from wa import ApkWorkload, Parameter

class UiBench(ApkWorkload):

    name = 'uibench'
    description = """
    Benchmark from AOSP for evaluating performance of Android UI elements.

    Built from AOSP source with 'make UiBench'. Tested with AOSP branch
    android-8.0.0_r4.
    """
    package = 'com.android.test.uibench'

    test_activities = [
        'BitmapUploadActivity',
        'DialogListActivity',
        'EditTextTypeActivity',
        'FullscreenOverdrawActivity',
        'GlTextureViewActivity',
        'InflatingListActivity',
        'InvalidateActivity',
        'ShadowGridActivity',
        'TextCacheHighHitrateActivity',
        'TextCacheLowHitrateActivity',
        'ActivityTransition',
        'ActivityTransitionDetails',
        'TrivialAnimationActivity',
        'TrivialListActivity',
        'TrivialRecyclerViewActivity',
    ]

    parameters = [
        Parameter('activity',
                  mandatory=True,
                  allowed_values=test_activities,
                  description='ID of the UiBench test activity to be run.'),
        Parameter('duration_s', kind=int, default=10,
                  description="""Time (in seconds) to leave activity running for"""),
    ]

    def run(self, context):
        self.apk.start_activity('.' + self.activity)
        sleep(self.duration_s)
