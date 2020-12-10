#    Copyright 2014-2020 ARM Limited
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

from wa import ApkUiautoWorkload, Parameter
from wa.framework.exception import ValidationError, WorkloadError


class Jetstream(ApkUiautoWorkload):

    name = 'jetstream'
    package_names = ['com.android.chrome']
    regex = re.compile(r'Jetstream Score ([\d.]+)')
    tests = ['3d-cube-SP', '3d-raytrace-SP', 'acorn-wtb', 'ai-astar', 'Air', 'async-fs', 'Babylon', 'babylon-wtb', 'base64-SP',
             'Basic', 'bomb-workers', 'Box2D', 'cdjs', 'chai-wtb', 'coffeescript-wtb', 'crypto', 'crypto-aes-SP', 'crypto-md5-SP',
             'crypto-sha1-SP', 'date-format-tofte-SP', 'date-format-xparb-SP', 'delta-blue', 'earley-boyer', 'espree-wtb',
             'first-inspector-code-load', 'FlightPlanner', 'float-mm.c', 'gaussian-blur', 'gbemu', 'hash-map', 'jshint-wtb',
             'json-parse-inspector', 'json-stringify-inspector', 'lebab-wtb', 'mandreel', 'ML', 'multi-inspector-code-load',
             'n-body-SP', 'navier-stokes', 'octane-code-load', 'octane-zlib', 'OfflineAssembler', 'pdfjs', 'prepack-wtb',
             'raytrace', 'regex-dna-SP', 'regexp', 'richards', 'segmentation', 'splay', 'stanford-crypto-aes', 'stanford-crypto-pbkdf2',
             'stanford-crypto-sha256', 'string-unpack-code-SP', 'tagcloud-SP', 'typescript', 'uglify-js-wtb', 'UniPoker']
    description = '''
    A workload to execute the jetstream web based benchmark

    Test description:
    1. Open chrome
    2. Navigate to the jetstream website - https://browserbench.org/JetStream/
    3. Execute the benchmark

    known working chrome version 80.0.3987.149
    '''
    requires_network = True

    def __init__(self, target, **kwargs):
        super(Jetstream, self).__init__(target, **kwargs)
        self.gui.timeout = 2700
        self.regex_tests = []
        for test in self.tests:
            formatted_string = 'text="([\d.]+)" resource-id="results-cell-({})-score"'.format(test)
            self.regex_tests.append(re.compile(formatted_string))
        # Add regex for tests with annoyingly different resource id's
        self.regex_tests.append(re.compile(r'text="([\d.]+)" resource-id="wasm-score-id(gcc-loops-wasm)"'))
        self.regex_tests.append(re.compile(r'text="([\d.]+)" resource-id="wasm-score-id(HashSet-wasm)"'))
        self.regex_tests.append(re.compile(r'text="([\d.]+)" resource-id="wasm-score-id(quicksort-wasm)"'))
        self.regex_tests.append(re.compile(r'text="([\d.]+)" resource-id="wasm-score-id(richards-wasm)"'))
        self.regex_tests.append(re.compile(r'text="([\d.]+)" resource-id="wasm-score-id(tsf-wasm)"'))
        self.regex_tests.append(re.compile(r'text="([\d.]+)" resource-id="(wsl)-score-score"'))
        self.results_xml = 'jetstream_results.xml'

    def extract_results(self, context):
        target_xml_dump = os.path.join(self.target.working_directory, self.results_xml)
        self.target.execute('uiautomator dump {}'.format(target_xml_dump))
        self.target.pull(target_xml_dump, os.path.join(context.output_directory, self.results_xml))

    def update_output(self, context):
        super(Jetstream, self).update_output(context)
        screen_xml = os.path.join(context.output_directory, self.results_xml)
        total_score_regex = re.compile(r'text="([\d.]+)" resource-id=""')
        with open(screen_xml, 'r') as fh:
            xml_str = fh.read()
            total_score_match = total_score_regex.search(xml_str)
            if total_score_match:
                total_score = float(total_score_match.group(1))
                context.add_metric('jetstream', total_score, 'score', lower_is_better=False)
            else:
                raise WorkloadError('Total score for jetstream could not be found')
            for regex in self.regex_tests:
                match = regex.search(xml_str)
                if match:
                    result = float(match.group(1))
                    test_name = match.group(2)
                    context.add_metric(test_name, result, 'score', lower_is_better=False)
                else:
                    raise WorkloadError('score {} cannot be found'.format(regex))
