#!/bin/bash
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



class_dir=bin/classes/com/arm/wlauto/uiauto
base_class=`python -c "import os, wlauto; print os.path.join(os.path.dirname(wlauto.__file__), 'common', 'android', 'BaseUiAutomation.class')"`
mkdir -p $class_dir
cp $base_class $class_dir

ant build

if [[ -f bin/org.linaro.wlauto.uiauto.octane2.jar ]]; then
    cp bin/org.linaro.wlauto.uiauto.octane2.jar ..
fi
