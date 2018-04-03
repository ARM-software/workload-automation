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


import os
import sys

from wa import ApkUiautoWorkload


class Facebook(ApkUiautoWorkload):

    name = 'facebook'
    description = """
    Uses com.facebook.patana apk for facebook workload.
    This workload does the following activities in facebook

        Login to facebook account.
        Send a message.
        Check latest notification.
        Search particular user account and visit his/her facebook account.
        Find friends.
        Update the facebook status

    .. note::  This workload starts disableUpdate workload as a part of setup to
               disable online updates, which helps to tackle problem of uncertain
               behavier during facebook workload run.]

    """
    package_names = ['com.facebook.katana']
    activity_name = '.LoginActivity'
    max_apk_version = '3.4'
