#    Copyright 2014-2018 ARM Limited
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
import re

from wa import ApkUiautoWorkload, WorkloadError, Parameter, ApkFile


class Antutu(ApkUiautoWorkload):

    name = 'antutu'
    package_names = ['com.antutu.ABenchMark']
    regex_matches_v7 = [re.compile(r'CPU Maths Score (.+)'),
                        re.compile(r'CPU Common Score (.+)'),
                        re.compile(r'CPU Multi Score (.+)'),
                        re.compile(r'GPU Marooned Score (.+)'),
                        re.compile(r'GPU Coastline Score (.+)'),
                        re.compile(r'GPU Refinery Score (.+)'),
                        re.compile(r'Data Security Score (.+)'),
                        re.compile(r'Data Processing Score (.+)'),
                        re.compile(r'Image Processing Score (.+)'),
                        re.compile(r'User Experience Score (.+)'),
                        re.compile(r'RAM Score (.+)'),
                        re.compile(r'ROM Score (.+)')]
    regex_matches_v8 = [re.compile(r'CPU Mathematical Operations Score (.+)'),
                        re.compile(r'CPU Common Algorithms Score (.+)'),
                        re.compile(r'CPU Multi-Core Score (.+)'),
                        re.compile(r'GPU Terracotta Score (.+)'),
                        re.compile(r'GPU Coastline Score (.+)'),
                        re.compile(r'GPU Refinery Score (.+)'),
                        re.compile(r'Data Security Score (.+)'),
                        re.compile(r'Data Processing Score (.+)'),
                        re.compile(r'Image Processing Score (.+)'),
                        re.compile(r'User Experience Score (.+)'),
                        re.compile(r'RAM Access Score (.+)'),
                        re.compile(r'ROM APP IO Score (.+)'),
                        re.compile(r'ROM Sequential Read Score (.+)'),
                        re.compile(r'ROM Sequential Write Score (.+)'),
                        re.compile(r'ROM Random Access Score (.+)')]
    regex_matches_v9 = [re.compile(r'CPU Mathematical Operations Score (.+)'),
                        re.compile(r'CPU Common Algorithms Score (.+)'),
                        re.compile(r'CPU Multi-Core Score (.+)'),
                        re.compile(r'GPU Terracotta Score (.+)'),
                        re.compile(r'GPU Swordsman Score (.+)'),
                        re.compile(r'GPU Refinery Score (.+)'),
                        re.compile(r'Data Security Score (.+)'),
                        re.compile(r'Data Processing Score (.+)'),
                        re.compile(r'Image Processing Score (.+)'),
                        re.compile(r'User Experience Score (.+)'),
                        re.compile(r'Video CTS Score (.+)'),
                        re.compile(r'Video Decode Score (.+)'),
                        re.compile(r'RAM Access Score (.+)'),
                        re.compile(r'ROM APP IO Score (.+)'),
                        re.compile(r'ROM Sequential Read Score (.+)'),
                        re.compile(r'ROM Sequential Write Score (.+)'),
                        re.compile(r'ROM Random Access Score (.+)')]
    regex_matches_v10 = [re.compile(r'CPU Mathematical Operations Score (.+)'),
                        re.compile(r'CPU Common Algorithms Score (.+)'),
                        re.compile(r'CPU Multi-Core Score (.+)'),
                        re.compile(r'GPU Seasons Score (.+)'),
                        re.compile(r'GPU Coastline2 Score (.+)'),
                        re.compile(r'RAM Bandwidth Score (.+)'),
                        re.compile(r'RAM Latency Score (.+)'),
                        re.compile(r'ROM APP IO Score (.+)'),
                        re.compile(r'ROM Sequential Read Score (.+)'),
                        re.compile(r'ROM Sequential Write Score (.+)'),
                        re.compile(r'ROM Random Access Score (.+)'),
                        re.compile(r'Data Security Score (.+)'),
                        re.compile(r'Data Processing Score (.+)'),
                        re.compile(r'Document Processing Score (.+)'),
                        re.compile(r'Image Decoding Score (.+)'),
                        re.compile(r'Image Processing Score (.+)'),
                        re.compile(r'User Experience Score (.+)'),
                        re.compile(r'Video CTS Score (.+)'),
                        re.compile(r'Video Decoding Score (.+)'),
                        re.compile(r'Video Editing Score (.+)')]
    description = '''
    Executes Antutu 3D, UX, CPU and Memory tests

    Test description:
    1. Open Antutu application
    2. Execute Antutu benchmark

    Known working APK version: 8.0.4
    '''

    supported_versions = ['7.0.4', '7.2.0',
            '8.0.4', '8.1.9', '8.4.5',
            '9.1.6', '9.2.9',
            '10.0.1-OB1', '10.0.6-OB6', '10.1.9', '10.2.1']

    parameters = [
        Parameter('version', kind=str, allowed_values=supported_versions, override=True,
                  description=(
                      '''Specify the version of Antutu to be run.
                      If not specified, the latest available version will be used.
                      ''')
                  )
    ]

    def __init__(self, device, **kwargs):
        super(Antutu, self).__init__(device, **kwargs)
        self.gui.timeout = 1200

    def initialize(self, context):
        super(Antutu, self).initialize(context)
        #Install the supporting benchmark
        supporting_apk = context.get_resource(ApkFile(self, package='com.antutu.benchmark.full'))
        self.target.install(supporting_apk)
        #Ensure the orientation is set to portrait
        self.target.set_rotation(0)
        #Change the logcat buffer to be the max size - required to avoid missing out on scores - alternatively use the logcat polling param - DOES NOT WORK
        #cmd = "logcat -G 16M"
        #self.target.execute(cmd)
        #Launch adb logcat as a process
        #print("Launching logcat")
        #cmd = "logcat &> /data/local/tmp/logcat.log &"
        #self.target.execute(cmd)
        #print("Logcat launched")

    def setup(self, context):
        self.gui.uiauto_params['version'] = self.version
        super(Antutu, self).setup(context)

    def extract_scores(self, context, regex_version):
        cpu = []
        gpu = []
        ux = []
        mem = []
        #pylint: disable=no-self-use
        expected_results = len(regex_version)
        logcat_file = context.get_artifact_path('logcat')
        with open(logcat_file, errors='replace') as fh:
            for line in fh:
                for regex in regex_version:
                    match = regex.search(line)
                    if match:
                        try:
                            result = float(match.group(1))
                            #print("MATCHED")
                            #print(regex)
                        except ValueError:
                            result = float('NaN')
                        entry = regex.pattern.rsplit(None, 1)[0]
                        context.add_metric(entry, result, lower_is_better=False)
        #Calculate group scores if 'CPU' in entry:
                        if 'CPU' in entry:
                            cpu.append(result)
                            cpu_result = sum(cpu)
                        if 'GPU' in entry:
                            gpu.append(result)
                            gpu_result = sum(gpu)
                        if any([i in entry for i in ['Data', 'Document', 'Image', 'User', 'Video']]):
                            ux.append(result)
                            ux_result = sum(ux)
                        if any([i in entry for i in ['RAM', 'ROM']]):
                            mem.append(result)
                            mem_result = sum(mem)
                        expected_results -= 1
        if expected_results > 0:
            msg = "The Antutu workload has failed. Expected {} scores, Detected {} scores."
            #raise WorkloadError(msg.format(len(regex_version), expected_results))

        context.add_metric('CPU Total Score', cpu_result, lower_is_better=False)
        context.add_metric('GPU Total Score', gpu_result, lower_is_better=False)
        context.add_metric('UX Total Score', ux_result, lower_is_better=False)
        context.add_metric('MEM Total Score', mem_result, lower_is_better=False)

        #Calculate overall scores
        overall_result = float(cpu_result + gpu_result + ux_result + mem_result)
        context.add_metric('Overall Score', overall_result, lower_is_better=False)

    def update_output(self, context):
        super(Antutu, self).update_output(context)
        if self.version.startswith('10'):
            self.extract_scores(context, self.regex_matches_v10)
        if self.version.startswith('9'):
            self.extract_scores(context, self.regex_matches_v9)
        if self.version.startswith('8'):
            self.extract_scores(context, self.regex_matches_v8)
        if self.version.startswith('7'):
            self.extract_scores(context, self.regex_matches_v7)
