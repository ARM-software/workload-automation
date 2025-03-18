#    Copyright 2016-2018 ARM Limited
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

import logging

from wa.utils import log
from wa.utils.types import obj_dict
from typing import Optional, List, Generator, Any

logger = logging.getLogger('config')


class JobSpecSource(object):
    """
    class representing a job specification source.
    """
    kind: str = ""

    def __init__(self, config: obj_dict, parent: Optional['SectionNode'] = None):
        self.config = config
        self.parent = parent
        self._log_self()

    @property
    def id(self) -> str:
        """
        source id
        """
        return self.config['id']

    @property
    def name(self) -> str:
        """
        name of the specification
        """
        raise NotImplementedError()

    def _log_self(self) -> None:
        """
        log the source structure
        """
        logger.debug('Creating {} node'.format(self.kind))
        with log.indentcontext():
            for key, value in self.config.items():
                logger.debug('"{}" to "{}"'.format(key, value))


class WorkloadEntry(JobSpecSource):
    """
    workloads in section nodes
    """
    kind: str = "workload"

    @property
    def name(self) -> str:
        """
        name of the workload entry
        """
        if self.parent and self.parent.id == "global":
            return 'workload "{}"'.format(self.id)
        else:
            return 'workload "{}" from section "{}"'.format(self.id, self.parent.id if self.parent else '')


class SectionNode(JobSpecSource):
    """
    a node representing a section in the job tree.
    section is a set of configurations for how jobs should be run. The
    settings in them take less precedence than workload-specific settings. For
    every section, all jobs will be run again, with the changes
    specified in the section's agenda entry. Sections
    are useful for several runs in which global settings change.
    """
    kind: str = "section"

    @property
    def name(self) -> str:
        """
        name of the section node
        """
        if self.id == "global":
            return "globally specified configuration"
        else:
            return 'section "{}"'.format(self.id)

    @property
    def is_leaf(self) -> bool:
        """
        true if it is a leaf node of the tree
        """
        return not bool(self.children)

    def __init__(self, config: obj_dict, parent=None, group: Optional[str] = None):
        super(SectionNode, self).__init__(config, parent=parent)
        self.workload_entries: List[WorkloadEntry] = []
        self.children: List['SectionNode'] = []
        self.group = group

    def add_section(self, section: obj_dict, group: Optional[str] = None) -> 'SectionNode':
        """
        add section to the job tree
        """
        # Each level is the same group, only need to check first
        if not self.children or group == self.children[0].group:
            new_node = SectionNode(section, parent=self, group=group)
            self.children.append(new_node)
        else:
            for child in self.children:
                new_node = child.add_section(section, group)
        return new_node

    def add_workload(self, workload_config: obj_dict) -> None:
        """
        add a workload to the section node
        """
        self.workload_entries.append(WorkloadEntry(workload_config, self))

    def descendants(self) -> Generator['SectionNode', Any, None]:
        """
        descendants of the current section node
        """
        for child in self.children:
            for n in child.descendants():
                yield n
            yield child

    def ancestors(self) -> Generator['SectionNode', Any, None]:
        """
        ancestors of the current section node
        """
        if self.parent is not None:
            yield self.parent
            for ancestor in self.parent.ancestors():
                yield ancestor

    def leaves(self) -> Generator['SectionNode', Any, None]:
        """
        leaf nodes of the job tree starting from current section node
        """
        if self.is_leaf:
            yield self
        else:
            for n in self.descendants():
                if n.is_leaf:
                    yield n
