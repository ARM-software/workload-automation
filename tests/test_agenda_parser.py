#    Copyright 2013-2018 ARM Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#


# pylint: disable=E0611
# pylint: disable=R0201
import os
import sys
import re
from collections import defaultdict
from unittest import TestCase

from nose.tools import assert_equal, assert_in, raises, assert_true


DATA_DIR = os.path.join(os.path.dirname(__file__), 'data')
os.environ['WA_USER_DIRECTORY'] = os.path.join(DATA_DIR, 'includes')

from wa.framework.configuration.execution import ConfigManager
from wa.framework.configuration.parsers import AgendaParser
from wa.framework.exception import ConfigError
from wa.utils.serializer import yaml
from wa.utils.types import reset_all_counters


YAML_TEST_FILE = os.path.join(DATA_DIR, 'test-agenda.yaml')
YAML_BAD_SYNTAX_FILE = os.path.join(DATA_DIR, 'bad-syntax-agenda.yaml')
INCLUDES_TEST_FILE = os.path.join(DATA_DIR, 'includes', 'agenda.yaml')

invalid_agenda_text = """
workloads:
    - id: 1
      workload_parameters:
          test: 1
"""

duplicate_agenda_text = """
global:
    iterations: 1
workloads:
    - id: 1
      workload_name: antutu
      workload_parameters:
          test: 1
    - id: "1"
      workload_name: benchmarkpi
"""

short_agenda_text = """
workloads: [antutu, dhrystone, benchmarkpi]
"""

default_ids_agenda_text = """
workloads:
    - antutu
    - id: wk1
      name: benchmarkpi
    - id: test
      name: dhrystone
      params:
          cpus: 1
    - vellamo
"""

sectioned_agenda_text = """
sections:
    - id: sec1
      runtime_params:
        dp: one
      workloads:
        - name: antutu
          workload_parameters:
            markers_enabled: True
        - benchmarkpi
        - name: dhrystone
          runtime_params:
            dp: two
    - id: sec2
      runtime_params:
        dp: three
      workloads:
        - antutu
workloads:
    - memcpy
"""

dup_sectioned_agenda_text = """
sections:
    - id: sec1
      workloads:
        - antutu
    - id: sec1
      workloads:
        - benchmarkpi
workloads:
    - memcpy
"""

yaml_anchors_agenda_text = """
workloads:
-   name: dhrystone
    params: &dhrystone_single_params
        cleanup_assets: true
        cpus: 0
        delay: 3
        duration: 0
        mloops: 10
        threads: 1
-   name: dhrystone
    params:
        <<: *dhrystone_single_params
        threads: 4
"""


class AgendaTest(TestCase):

    def setUp(self):
        reset_all_counters()
        self.config = ConfigManager()
        self.parser = AgendaParser()

    def test_yaml_load(self):
        self.parser.load_from_path(self.config, YAML_TEST_FILE)
        assert_equal(len(self.config.jobs_config.root_node.workload_entries), 4)

    def test_duplicate_id(self):
        duplicate_agenda = yaml.load(duplicate_agenda_text)

        try:
            self.parser.load(self.config, duplicate_agenda, 'test')
        except ConfigError as e:
            assert_in('duplicate', e.message.lower())  # pylint: disable=E1101
        else:
            raise Exception('ConfigError was not raised for an agenda with duplicate ids.')

    def test_yaml_missing_field(self):
        invalid_agenda = yaml.load(invalid_agenda_text)

        try:
            self.parser.load(self.config, invalid_agenda, 'test')
        except ConfigError as e:
            assert_in('workload name', e.message)
        else:
            raise Exception('ConfigError was not raised for an invalid agenda.')

    def test_defaults(self):
        short_agenda = yaml.load(short_agenda_text)
        self.parser.load(self.config, short_agenda, 'test')

        workload_entries = self.config.jobs_config.root_node.workload_entries
        assert_equal(len(workload_entries), 3)
        assert_equal(workload_entries[0].config['workload_name'], 'antutu')
        assert_equal(workload_entries[0].id, 'wk1')

    def test_default_id_assignment(self):
        default_ids_agenda = yaml.load(default_ids_agenda_text)

        self.parser.load(self.config, default_ids_agenda, 'test2')
        workload_entries = self.config.jobs_config.root_node.workload_entries
        assert_equal(workload_entries[0].id, 'wk2')
        assert_equal(workload_entries[3].id, 'wk3')

    def test_sections(self):
        sectioned_agenda = yaml.load(sectioned_agenda_text)
        self.parser.load(self.config, sectioned_agenda, 'test')

        root_node_workload_entries = self.config.jobs_config.root_node.workload_entries
        leaves = list(self.config.jobs_config.root_node.leaves())
        section1_workload_entries = leaves[0].workload_entries
        section2_workload_entries = leaves[0].workload_entries

        assert_equal(root_node_workload_entries[0].config['workload_name'], 'memcpy')
        assert_true(section1_workload_entries[0].config['workload_parameters']['markers_enabled'])
        assert_equal(section2_workload_entries[0].config['workload_name'], 'antutu')

    def test_yaml_anchors(self):
        yaml_anchors_agenda = yaml.load(yaml_anchors_agenda_text)
        self.parser.load(self.config, yaml_anchors_agenda, 'test')

        workload_entries = self.config.jobs_config.root_node.workload_entries
        assert_equal(len(workload_entries), 2)
        assert_equal(workload_entries[0].config['workload_name'], 'dhrystone')
        assert_equal(workload_entries[0].config['workload_parameters']['threads'], 1)
        assert_equal(workload_entries[0].config['workload_parameters']['delay'], 3)
        assert_equal(workload_entries[1].config['workload_name'], 'dhrystone')
        assert_equal(workload_entries[1].config['workload_parameters']['threads'], 4)
        assert_equal(workload_entries[1].config['workload_parameters']['delay'], 3)

    @raises(ConfigError)
    def test_dup_sections(self):
        dup_sectioned_agenda = yaml.load(dup_sectioned_agenda_text)
        self.parser.load(self.config, dup_sectioned_agenda, 'test')

    @raises(ConfigError)
    def test_bad_syntax(self):
        self.parser.load_from_path(self.config, YAML_BAD_SYNTAX_FILE)


class FakeTargetManager:

    def merge_runtime_parameters(self, params):
        return params

    def validate_runtime_parameters(self, params):
        pass


class IncludesTest(TestCase):

    def test_includes(self):
        from pprint import pprint
        parser = AgendaParser()
        cm = ConfigManager()
        tm = FakeTargetManager()

        includes = parser.load_from_path(cm, INCLUDES_TEST_FILE)
        include_set = set([os.path.basename(i) for i in includes])
        assert_equal(include_set,
            set(['test.yaml', 'section1.yaml', 'section2.yaml',
                 'section-include.yaml', 'workloads.yaml']))

        job_classifiers = {j.id: j.classifiers
                           for j in cm.jobs_config.generate_job_specs(tm)}
        assert_equal(job_classifiers,
                {
                    's1-wk1': {'section': 'one'},
                    's2-wk1': {'section': 'two', 'included': True},
                    's1-wk2': {'section': 'one', 'memcpy': True},
                    's2-wk2': {'section': 'two', 'included': True, 'memcpy': True},
                })

GLOBAL_WKL_SWEEP_TEST = """
workloads:
    - name: dhrystone
      workload_params:
        sweep(range):
          threads: [1,2,3]
"""

SECTION_SWEEP_TEST = """
sections:
    - id: my_section
      workload_params:
        sweep(range): 
          threads: [1,2,3]

workloads:
    - name: dhrystone
"""

SECTION_GROUP_SWEEP_TEST = """
sections:
    - id: my_section1
      group: mygroup
      workload_params:
        sweep(range):
          threads: [1,2,3]
    - id: my_section2
      group: mygroup
      workload_params:
        threads: 8
    - id: my_section3
      group: othergroup
      runtime_parameters:
        freq: 10
workloads:
    - name: dhrystone
"""

GLOBAL_CFG_SWEEP_TEST = """
config:
    workload_parameters:
        sweep(range): 
          duration: [1,2,3,4,5]

workloads:
    - name: idle
"""

WKL_OVERRIDE_SECTION_SWEEP_TEST = """
sections:
    - id: mysection
      workload_parameters:
        sweep(range):
          duration: [1,2,3]
      group: a

workloads:
    - name: idle
      workload_parameters:
        sweep(range):
          duration: [4,5,6]
    - name: idle
      workload_parameters:
        duration: 7
    - name: idle
"""


SECTION_SWEEP_OVERRIDE_CFG_SWEEP_TEST = """
config:
    workload_parameters:
        sweep(range):
          duration: [1,2,3]

sections:
    - id: mysection
      workload_parameters:
        sweep(range):
          duration: [4,5,6,7]

workloads:
    - name: idle
"""

NESTED_WKL_SWEEP_TEST = """
sections:
  - id: mysection
    workloads:
      - name: idle
        params:
          sweep(range):
            duration: [1,2,3]
workloads:
  - name: idle
    params:
      duration: 4
"""

NESTED_WKL_SWEEP_OVERRIDE_TEST = """
sections:
  - id: mysection
    workload_parameters:
      duration: 100
    workloads:
      - name: idle
        params:
          sweep(range):
            duration: [1,2,3]

workloads:
  - name: idle
    params:
      duration: 20
"""

RANGE_SWEEP_TEST = """
workloads:
  - name: idle
    params:
      sweep(range):
        duration: 1-10,2
"""

SWEEP_METADATA_TEST_1 = """
sections:
  - id: mysection
    runtime_params:
      sweep(range):
        threads: 1-4
workloads:
  - name: idle
    params:
      sweep(range):
        duration: 1-5
"""

SWEEP_METADATA_TEST_2 = """
workloads:
  - name: idle
    label: testlabel{duration}
    params:
      sweep(range):
        duration: 1-5
"""

AUTOPARAM_TEST = """
workloads:
  - name: Youtube
    params:
      sweep(autoparam):
        param: video_source
        plugin: Youtube
"""


class SweepsTest(TestCase):

    def test_global_workload_sweeps(self):
        # Do sweeps work on global workloads?
        jobspecs = get_job_specs(GLOBAL_WKL_SWEEP_TEST)
        assert_equal(len(jobspecs), 3)
        for jobspec, threads in zip(jobspecs, [1,2,3]):
            assert_equal(jobspec.workload_parameters['threads'], threads)
    
    def test_section_sweeps(self):
        # Do sweeps work within a section?
        jobspecs = get_job_specs(SECTION_SWEEP_TEST)
        assert_equal(len(jobspecs), 3)
        for jobspec, threads in zip(jobspecs, [1,2,3]):
            assert_equal(jobspec.workload_parameters['threads'], threads)
    
    def test_section_group_sweeps(self):
        # Do sweeps work when defined in a group?
        jobspecs = get_job_specs(SECTION_GROUP_SWEEP_TEST)
        assert_equal(len(jobspecs), 4)
        for jobspec, threads in zip(jobspecs, [1,2,3,8]):
            assert_equal(jobspec.workload_parameters['threads'], threads)
            assert_equal(list(jobspec.runtime_parameters.values())[0]['freq'], 10)
    
    def test_global_config_sweeps(self):
        # Do sweeps work when defined in a global config?
        jobspecs = get_job_specs(GLOBAL_CFG_SWEEP_TEST)
        assert_equal(len(jobspecs), 5)
        for jobspec, duration in zip(jobspecs, [1,2,3,4,5]):
            assert_equal(jobspec.workload_parameters['duration'], duration)
    
    def test_wkl_sweep_override_section(self):
        # Do global workload sweeps override section parameters?
        jobspecs = get_job_specs(WKL_OVERRIDE_SECTION_SWEEP_TEST)
        expect = [4,4,4,5,5,5,6,6,6,7,7,7,1,2,3]
        assert_equal(len(jobspecs), len(expect))
        for jobspec in jobspecs:
            duration = jobspec.workload_parameters['duration']
            assert duration in expect
    
    def test_section_sweep_override_config(self):
        # Do section sweeps override global config?
        jobspecs = get_job_specs(SECTION_SWEEP_OVERRIDE_CFG_SWEEP_TEST)
        expect = [4,4,4, 5,5,5, 6,6,6, 7,7,7]
        assert_equal(len(jobspecs), len(expect))
        for jobspec in jobspecs:
            cfg = jobspec.workload_parameters['duration']
            assert cfg in expect
    
    def test_nested_wkl_sweep_in_section(self):
        # Handle sweeps correctly inside workloads inside sections
        jobspecs = get_job_specs(NESTED_WKL_SWEEP_TEST)
        expect = {1,2,3,4}
        assert_equal(len(jobspecs), len(expect))
        for jobspec in jobspecs:
          cfg = jobspec.workload_parameters['duration']
          expect.remove(cfg)
    
    def test_nested_wkl_override(self):
        jobspecs = get_job_specs(NESTED_WKL_SWEEP_OVERRIDE_TEST)
        expect = {1,2,3,20}
        assert_equal(len(jobspecs), len(expect))
        for jobspec in jobspecs:
            cfg = jobspec.workload_parameters['duration']
            expect.remove(cfg)
    
    def test_section_wkl_sweep_metadata(self):
        # Do sweeps derived from a labelled entry share the label?
        # Do sweeps derived from the same entry share a commonly prefixed identifier?
        jobspecs = get_job_specs(SWEEP_METADATA_TEST_1)
        ids = [job.id for job in jobspecs]
        initial = r'(?P<section>\w*)_\d*-(?P<workload>\w*)_\d*'
        result = re.match(initial, ids[0])
        assert result
        section = result.group('section')
        workload = result.group('workload')
        confirm = section + r'_\d*-' + workload + r'_\d*'

        assert all(re.fullmatch(confirm, other) for other in ids[1:])
        assert_equal([job.label for job in jobspecs], [jobspecs[0].label]*len(jobspecs))
    
    def test_wkl_sweep_metadata(self):
        jobspecs = get_job_specs(SWEEP_METADATA_TEST_2)
        ids = [job.id for job in jobspecs]
        initial = r'(?P<workload>\w*)_\d*'
        result = re.match(initial, ids[0])
        assert result
        workload = result.group('workload')
        confirm = workload + r'_\d*'
        assert all(re.fullmatch(confirm, other) for other in ids[1:])
        labels = ['testlabel' + str(x) for x in range(1,5)]
        assert_equal([job.label for job in jobspecs], labels)

    def test_autoparam_sweep(self):
        jobspecs = get_job_specs(AUTOPARAM_TEST)
        from wa.workloads.youtube import Youtube
        expect = set(Youtube.parameters['video_source'].allowed_values)
        assert_equal(len(expect), len(jobspecs))
        for jobspec in jobspecs:
            expect.remove(jobspec.workload_parameters['video_source'])

def get_job_specs(text):
    ap = AgendaParser()
    cm = ConfigManager()
    tm = FakeTargetManager()
    
    raw = yaml.load(text)
    ap.load(cm, raw, None)
    cm.jobs_config.expand_sweeps(tm)
    return cm.jobs_config.generate_job_specs(tm)
