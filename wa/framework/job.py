#    Copyright 2018 ARM Limited
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

# Because of use of Enum (dynamic attrs)
# pylint: disable=no-member

import logging
from copy import copy
from datetime import datetime, timedelta

from wa.framework import pluginloader, signal, instrument
from wa.framework.configuration.core import Status
from wa.utils.log import indentcontext
from wa.framework.run import JobState
from typing import (TYPE_CHECKING, Optional, Any, Dict,
                    Type, cast, OrderedDict, Set)
from devlib.target import Target
from types import ModuleType
if TYPE_CHECKING:
    from wa.framework.configuration.core import JobSpecProtocol
    from wa.framework.execution import ExecutionContext
    from wa.framework.workload import Workload
    from wa.framework.output import JobOutput
    from wa.framework.output_processor import ProcessorManager
    from wa.framework.configuration.core import StatusType
    from wa.framework.plugin import Plugin
    from louie.dispatcher import Anonymous  # type:ignore


class Job(object):
    """
        A single execution of a workload. A job is defined by an associated
        :term:`spec`. However, multiple jobs can share the same spec;
        E.g. Even if you only have 1 workload to run but wanted 5 iterations
        then 5 individual jobs will be generated to be run.
    """
    _workload_cache: Dict[str, 'Workload'] = {}

    def __init__(self, spec: 'JobSpecProtocol',
                 iteration: int, context: 'ExecutionContext'):
        self.logger = logging.getLogger('job')
        self.spec = spec
        self.iteration = iteration
        self.context = context
        self.workload: Optional['Workload'] = None
        self.output: Optional['JobOutput'] = None
        self.run_time: Optional[timedelta] = None
        self.classifiers: OrderedDict[str, str] = copy(self.spec.classifiers)
        self._has_been_initialized: bool = False
        self.state = JobState(self.id or '', self.label, self.iteration, Status.NEW)

    @property
    def id(self) -> Optional[str]:
        """
        job id
        """
        return self.spec.id

    @property
    def label(self) -> str:
        """
        job label
        """
        return self.spec.label

    @property
    def status(self) -> 'StatusType':
        """
        job status getter
        """
        return self.state.status

    @status.setter
    def status(self, value: 'StatusType') -> None:
        """
        job status setter
        """
        self.state.status = value
        self.state.timestamp = datetime.utcnow()
        if self.output:
            self.output.status = value

    @property
    def has_been_initialized(self) -> bool:
        """
        check if the job has been initialized
        """
        return self._has_been_initialized

    @property
    def retries(self) -> int:
        """
        number of retries for the job execution
        """
        return self.state.retries

    @retries.setter
    def retries(self, value: int) -> None:
        """
        setter for retries
        """
        self.state.retries = value

    def load(self, target: Target, loader: ModuleType = pluginloader) -> None:
        """
        load workload for the job
        """
        self.logger.info('Loading job {}'.format(self))
        if self.id not in self._workload_cache:
            self.workload = loader.get_workload(self.spec.workload_name,
                                                target,
                                                **self.spec.workload_parameters)
            if self.workload:
                self.workload.init_resources(self.context)
                self.workload.validate()
                self._workload_cache[self.id or ''] = self.workload
        else:
            self.workload = self._workload_cache[self.id]

    def set_output(self, output: 'JobOutput') -> None:
        """
        set output
        """
        output.classifiers = copy(self.classifiers)
        self.output = output

    def initialize(self, context: 'ExecutionContext') -> None:
        """
        initialize the job execution
        """
        self.logger.info('Initializing job {}'.format(self))
        with indentcontext():
            with signal.wrap('WORKLOAD_INITIALIZED', cast(Type['Anonymous'], self), context):
                if self.workload:
                    self.workload.logger.context = context  # type:ignore
                    self.workload.initialize(context)
            self.set_status(Status.PENDING)
            self._has_been_initialized = True

    def configure_augmentations(self, context: 'ExecutionContext',
                                pm: 'ProcessorManager') -> None:
        """
        configure augmentations
        """
        self.logger.info('Configuring augmentations')
        with indentcontext():
            instruments_to_enable: Set[str] = set()
            output_processors_to_enable: Set[str] = set()
            enabled_instruments: Set[Optional[str]] = set(i.name for i in instrument.get_enabled())
            enabled_output_processors: Set[Optional[str]] = set(p.name for p in pm.get_enabled())

            for augmentation in list(self.spec.augmentations.values()):
                augmentation_cls: Type['Plugin'] = context.cm.plugin_cache.get_plugin_class(augmentation)
                if augmentation_cls.kind == 'instrument':
                    instruments_to_enable.add(augmentation)
                elif augmentation_cls.kind == 'output_processor':
                    output_processors_to_enable.add(augmentation)

            # Disable unrequired instruments
            for instrument_name in enabled_instruments.difference(instruments_to_enable):
                instrument.disable(instrument_name or '')
            # Enable additional instruments
            for instrument_name in instruments_to_enable.difference(enabled_instruments):
                instrument.enable(instrument_name or '')

            # Disable unrequired output_processors
            for processor in enabled_output_processors.difference(output_processors_to_enable):
                pm.disable(processor or '')
            # Enable additional output_processors
            for processor in output_processors_to_enable.difference(enabled_output_processors):
                pm.enable(processor or '')

    def configure_target(self, context: 'ExecutionContext') -> None:
        """
        configure target
        """
        self.logger.info('Configuring target for job {}'.format(self))
        with indentcontext():
            context.tm.commit_runtime_parameters(self.spec.runtime_parameters)

    def setup(self, context: 'ExecutionContext') -> None:
        """
        setup the job
        """
        self.logger.info('Setting up job {}'.format(self))
        with indentcontext():
            with signal.wrap('WORKLOAD_SETUP', cast(Type['Anonymous'], self), context):
                if self.workload:
                    self.workload.setup(context)

    def run(self, context: 'ExecutionContext') -> None:
        """
        run the job
        """
        self.logger.info('Running job {}'.format(self))
        with indentcontext():
            with signal.wrap('WORKLOAD_EXECUTION', cast(Type['Anonymous'], self), context):
                start_time: datetime = datetime.utcnow()
                try:
                    if self.workload:
                        self.workload.run(context)
                finally:
                    self.run_time = datetime.utcnow() - start_time

    def process_output(self, context: 'ExecutionContext') -> None:
        """
        process job output
        """
        if not context.tm.is_responsive:
            self.logger.info('Target unresponsive; not processing job output.')
            return
        self.logger.info('Processing output for job {}'.format(self))
        with indentcontext():
            if self.status != Status.FAILED:
                with signal.wrap('WORKLOAD_RESULT_EXTRACTION', cast(Type['Anonymous'], self), context):
                    if self.workload:
                        self.workload.extract_results(context)
                    context.extract_results()
                with signal.wrap('WORKLOAD_OUTPUT_UPDATE', cast(Type['Anonymous'], self), context):
                    if self.workload:
                        self.workload.update_output(context)

    def teardown(self, context: 'ExecutionContext') -> None:
        """
        teardown the job run
        """
        if not context.tm.is_responsive:
            self.logger.info('Target unresponsive; not tearing down.')
            return
        self.logger.info('Tearing down job {}'.format(self))
        with indentcontext():
            with signal.wrap('WORKLOAD_TEARDOWN', cast(Type['Anonymous'], self), context):
                if self.workload:
                    self.workload.teardown(context)

    def finalize(self, context: 'ExecutionContext') -> None:
        """
        finalize the job run
        """
        if not self._has_been_initialized:
            return
        if not context.tm.is_responsive:
            self.logger.info('Target unresponsive; not finalizing.')
            return
        self.logger.info('Finalizing job {} '.format(self))
        with indentcontext():
            with signal.wrap('WORKLOAD_FINALIZED', cast(Type['Anonymous'], self), context):
                if self.workload:
                    self.workload.finalize(context)

    def set_status(self, status: 'StatusType',
                   force: bool = False) -> None:
        """
        set job status
        """
        status = Status(status)
        if force or cast(int, self.status) < cast(int, status):
            self.status = status

    def add_classifier(self, name: str, value: Any,
                       overwrite: bool = False) -> None:
        """
        add classifier to the job
        """
        if name in self.classifiers and not overwrite:
            raise ValueError('Cannot overwrite "{}" classifier.'.format(name))
        self.classifiers[name] = value

    def __str__(self):
        return '{} ({}) [{}]'.format(self.id, self.label, self.iteration)

    def __repr__(self):
        return 'Job({})'.format(self)
