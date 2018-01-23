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


from wlauto.common.resources import FileResource


class ReventFile(FileResource):

    name = 'revent'

    def __init__(self, owner, stage):
        super(ReventFile, self).__init__(owner)
        self.stage = stage


class JarFile(FileResource):

    name = 'jar'


class ApkFile(FileResource):

    name = 'apk'

    def __init__(self, owner, platform=None, uiauto=False, package=None):
        super(ApkFile, self).__init__(owner)
        self.platform = platform
        self.uiauto = uiauto
        self.package = package

    def __str__(self):
        apk_type = 'uiautomator ' if self.uiauto else ''
        return '<{}\'s {} {}APK>'.format(self.owner, self.platform, apk_type)
