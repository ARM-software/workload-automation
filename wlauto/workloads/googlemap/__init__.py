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


from wlauto import GameWorkload, Parameter


class GoogleMap(GameWorkload):

    name = 'googlemap'
    description = """
    Navigation app.

    Stock map provided by Google Inc.
    """
    package = 'com.google.android.apps.maps'
    activity = 'com.google.android.maps.MapsActivity'
    install_timeout = 120
    loading_time = 20
    parameters = [
        Parameter('duration', kind=int, default=100,
                  description=('Duration, in seconds, of the run (may need to'
                               'be adjusted for different devices.')),
    ]

    def run(self, context):
        super(GoogleMap, self).run(context)

