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

import random
from itertools import groupby, chain

from future.moves.itertools import zip_longest  # type:ignore

from devlib.utils.types import identifier
from devlib.target import Target

from wa.framework.configuration.core import (MetaConfiguration, RunConfiguration,
                                             JobGenerator, settings,
                                             JobSpecProtocol)
from wa.framework.configuration.parsers import ConfigParser
from wa.framework.configuration.plugin_cache import PluginCache
from wa.framework.exception import NotFoundError, ConfigError
from wa.framework.job import Job
from wa.utils import log
from wa.utils.serializer import Podable
from typing import (TYPE_CHECKING, cast, Dict, Any, Tuple,
                    Optional, List, Callable, Generator)
if TYPE_CHECKING:
    from wa.framework.execution import ExecutionContext
    from wa.framework.configuration.core import RunConfigurationProtocol, MetaConfigurationProtocol
    from wa.framework.instrument import Instrument
    from wa.framework.output_processor import OutputProcessor
    from wa.framework.plugin import Plugin


class CombinedConfig(Podable):

    _pod_serialization_version: int = 1

    @staticmethod
    def from_pod(pod: Dict[str, Any]) -> 'CombinedConfig':
        instance = cast('CombinedConfig', super(CombinedConfig, CombinedConfig).from_pod(pod))
        instance.settings = cast('MetaConfigurationProtocol', MetaConfiguration.from_pod(pod.get('settings', {})))
        instance.run_config = cast('RunConfigurationProtocol', RunConfiguration.from_pod(pod.get('run_config', {})))
        return instance

    def __init__(self, settings: Optional['MetaConfigurationProtocol'] = None,
                 run_config: Optional['RunConfigurationProtocol'] = None):  # pylint: disable=redefined-outer-name
        super(CombinedConfig, self).__init__()
        self.settings = settings
        self.run_config = run_config

    def to_pod(self) -> Dict[str, Any]:
        pod = super(CombinedConfig, self).to_pod()
        if self.settings:
            pod['settings'] = self.settings.to_pod()
        if self.run_config:
            pod['run_config'] = self.run_config.to_pod()
        return pod

    @staticmethod
    def _pod_upgrade_v1(pod: Dict[str, Any]) -> Dict[str, Any]:
        """
        pod upgrade function for CombinedConfig
        """
        pod['_pod_version'] = pod.get('_pod_version', 1)
        return pod


class ConfigManager(object):
    """
    Represents run-time state of WA. Mostly used as a container for loaded
    configuration and discovered plugins.

    This exists outside of any command or run and is associated with the running
    instance of wA itself.
    """

    @property
    def enabled_instruments(self) -> List[str]:
        """
        list of enabled instruments
        """
        return self.jobs_config.enabled_instruments

    @property
    def enabled_processors(self) -> List[str]:
        """
        list of enabled output processors
        """
        return self.jobs_config.enabled_processors

    @property
    def job_specs(self) -> List[JobSpecProtocol]:
        """
        list of job specifications
        """
        if not self._jobs_generated:
            msg: str = 'Attempting to access job specs before '\
                'jobs have been generated'
            raise RuntimeError(msg)
        return [j.spec for j in self._jobs]

    @property
    def jobs(self) -> List[Job]:
        """
        List of jobs generated
        """
        if not self._jobs_generated:
            msg: str = 'Attempting to access jobs before '\
                'they have been generated'
            raise RuntimeError(msg)
        return self._jobs

    def __init__(self, settings: 'MetaConfigurationProtocol' = settings):  # pylint: disable=redefined-outer-name
        self.settings = settings
        self.run_config: 'RunConfigurationProtocol' = cast('RunConfigurationProtocol', RunConfiguration())
        self.plugin_cache = PluginCache()
        self.jobs_config = JobGenerator(self.plugin_cache)
        self.loaded_config_sources: List[str] = []
        self._config_parser = ConfigParser()
        self._jobs: List[Job] = []
        self._jobs_generated: bool = False
        self.agenda: Optional[str] = None

    def load_config_file(self, filepath: str) -> None:
        """
        Load configuration file
        """
        includes = self._config_parser.load_from_path(self, filepath)
        self.loaded_config_sources.append(filepath)
        self.loaded_config_sources.extend(includes)

    def load_config(self, values: Dict, source: str) -> None:
        """
        load configuration from source
        """
        self._config_parser.load(self, values, source)
        self.loaded_config_sources.append(source)

    def get_plugin(self, name: Optional[str] = None, kind: Optional[str] = None,
                   *args, **kwargs) -> Optional['Plugin']:
        """
        get the plugin of the specified name and kind
        """
        return self.plugin_cache.get_plugin(identifier(name), kind, *args, **kwargs)

    def get_instruments(self, target: Target) -> List['Instrument']:
        """
        get the list of instruments associated with the WA
        """
        instruments: List['Instrument'] = []
        for name in self.enabled_instruments:
            try:
                instruments.append(cast('Instrument', self.get_plugin(name, kind='instrument',
                                                                      target=target)))
            except NotFoundError:
                msg = 'Instrument "{}" not found'
                raise NotFoundError(msg.format(name))
        return instruments

    def get_processors(self) -> List['OutputProcessor']:
        """
        get the output processors associated with the WA
        """
        processors: List['OutputProcessor'] = []
        for name in self.enabled_processors:
            try:
                proc: 'OutputProcessor' = cast('OutputProcessor',
                                               self.plugin_cache.get_plugin(name, kind='output_processor'))
            except NotFoundError:
                msg = 'Output Processor "{}" not found'
                raise NotFoundError(msg.format(name))
            processors.append(proc)
        return processors

    def get_config(self) -> CombinedConfig:
        """
        get the combined configuration
        """
        return CombinedConfig(self.settings, self.run_config)

    def finalize(self) -> CombinedConfig:
        """
        finalize the configuration
        """
        if not self.agenda:
            msg: str = 'Attempting to finalize config before agenda has been set'
            raise RuntimeError(msg)
        self.run_config.merge_device_config(self.plugin_cache)
        return self.get_config()

    def generate_jobs(self, context: 'ExecutionContext') -> None:
        """
        generate jobs based on job specifications based on the configuration
        """
        job_specs: List[JobSpecProtocol] = self.jobs_config.generate_job_specs(context.tm)
        if not job_specs:
            msg: str = 'No jobs available for running.'
            raise ConfigError(msg)
        exec_order: str = cast('RunConfigurationProtocol', self.run_config).execution_order
        log.indent()
        for spec, i in permute_iterations(job_specs, exec_order):
            job = Job(spec, i, context)
            if context.tm.target:
                job.load(context.tm.target)
            self._jobs.append(job)
            if context.run_state:
                context.run_state.add_job(job)
        log.dedent()
        self._jobs_generated = True


def permute_by_workload(specs: List[JobSpecProtocol]) -> Generator[Tuple[JobSpecProtocol, int], Any, None]:
    """
    This is that "classic" implementation that executes all iterations of a
    workload spec before proceeding onto the next spec.

    """
    for spec in specs:
        for i in range(1, spec.iterations + 1):
            yield (spec, i)


def permute_by_iteration(specs: List[JobSpecProtocol]) -> Generator[Tuple[JobSpecProtocol, int], Any, None]:
    """
    Runs the first iteration for all benchmarks first, before proceeding to the
    next iteration, i.e. A1, B1, C1, A2, B2, C2...  instead of  A1, A1, B1, B2,
    C1, C2...

    If multiple sections where specified in the agenda, this will run all
    sections for the first global spec first, followed by all sections for the
    second spec, etc.

    e.g. given sections X and Y, and global specs A and B, with 2 iterations,
    this will run

    X.A1, Y.A1, X.B1, Y.B1, X.A2, Y.A2, X.B2, Y.B2

    """
    groups: List[List[JobSpecProtocol]] = [list(g) for _, g in groupby(specs, lambda s: s.workload_id)]

    all_tuples: List[List[Tuple[JobSpecProtocol, int]]] = []
    for spec in chain(*groups):
        all_tuples.append([(spec, i + 1)
                           for i in range(spec.iterations)])
    for t in chain(*list(map(list, zip_longest(*all_tuples)))):
        if t is not None:
            yield t


def permute_by_section(specs: List[JobSpecProtocol]) -> Generator[Tuple[JobSpecProtocol, int], Any, None]:
    """
    Runs the first iteration for all benchmarks first, before proceeding to the
    next iteration, i.e. A1, B1, C1, A2, B2, C2...  instead of  A1, A1, B1, B2,
    C1, C2...

    If multiple sections where specified in the agenda, this will run all specs
    for the first section followed by all specs for the seciod section, etc.

    e.g. given sections X and Y, and global specs A and B, with 2 iterations,
    this will run

    X.A1, X.B1, Y.A1, Y.B1, X.A2, X.B2, Y.A2, Y.B2

    """
    groups: List[List[JobSpecProtocol]] = [list(g) for _, g in groupby(specs, lambda s: s.section_id)]

    all_tuples: List[List[Tuple[JobSpecProtocol, int]]] = []
    for spec in chain(*groups):
        all_tuples.append([(spec, i + 1)
                           for i in range(spec.iterations)])
    for t in chain(*list(map(list, zip_longest(*all_tuples)))):
        if t is not None:
            yield t


def permute_randomly(specs: List[JobSpecProtocol]) -> Generator[Tuple[JobSpecProtocol, int], Any, None]:
    """
    This will generate a random permutation of specs/iteration tuples.

    """
    result: List[Tuple[JobSpecProtocol, int]] = []
    for spec in specs:
        for i in range(1, spec.iterations + 1):
            result.append((spec, i))
    random.shuffle(result)
    for t in result:
        yield t


permute_map: Dict[str, Callable[[List[JobSpecProtocol]],
                                Generator[Tuple[JobSpecProtocol, int], Any, None]]] = {
    'by_iteration': permute_by_iteration,
    'by_workload': permute_by_workload,
    'by_section': permute_by_section,
    'random': permute_randomly,
}


def permute_iterations(specs: List[JobSpecProtocol], exec_order: str):
    """
    permute iterations based on the specified execution order
    """
    if exec_order not in permute_map:
        msg = 'Unknown execution order "{}"; must be in: {}'
        raise ValueError(msg.format(exec_order, list(permute_map.keys())))
    return permute_map[exec_order](specs)
