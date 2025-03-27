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

import logging
import time
from collections import defaultdict, OrderedDict
from copy import copy

from devlib.exception import TargetError
from devlib.utils.misc import unique
from devlib.utils.types import integer

from wa.framework.exception import ConfigError
from wa.framework.plugin import Plugin, Parameter
from wa.utils.misc import resolve_cpus, resolve_unique_domain_cpus
from wa.utils.types import caseless_string, enum
from devlib.target import Target, AndroidTarget
from devlib.module.hotplug import HotplugModule
from devlib.module.cpufreq import CpufreqModule
from devlib.module.cpuidle import Cpuidle, CpuidleState
from typing import (Optional, Set, List, Tuple, Callable, Dict,
                    Any, cast, DefaultDict, OrderedDict as od, Union)

logger = logging.getLogger('RuntimeConfig')


class RuntimeParameter(Parameter):
    """
    represents a runtime parameter
    """
    def __init__(self, name: str, setter: Callable,
                 setter_params: Optional[Dict] = None, **kwargs):
        super(RuntimeParameter, self).__init__(name, **kwargs)
        self.setter = setter
        self.setter_params = setter_params or {}

    def set(self, obj: Any, value: Any) -> None:
        """
        set value to object
        """
        self.validate_value(self.name, value)
        self.setter(obj, value, **self.setter_params)


class RuntimeConfig(Plugin):
    """"
    represents a runtime configuration
    """
    name: Optional[str] = None
    kind: str = 'runtime-config'

    @property
    def supported_parameters(self) -> List[Parameter]:
        """
        supported parameters
        """
        return list(self._runtime_params.values())

    @property
    def core_names(self) -> List[str]:
        """
        list of core names
        """
        return unique(self.target.core_names)

    def __init__(self, target: Target, **kwargs):
        super(RuntimeConfig, self).__init__(**kwargs)
        self.target = target
        self._target_checked: bool = False
        self._runtime_params: Dict[str, RuntimeParameter] = {}
        try:
            self.initialize()
        except TargetError:
            msg = 'Failed to initialize: "{}"'
            self.logger.debug(msg.format(self.name))
            self._runtime_params = {}

    def initialize(self) -> None:
        """
        initialize runtime configuration
        """
        raise NotImplementedError()

    def commit(self) -> None:
        """
        commit runtime configuration
        """
        raise NotImplementedError()

    def set_runtime_parameter(self, name: str, value: Any) -> None:
        """
        set runtime parameters
        """
        if not self._target_checked:
            self.check_target()
            self._target_checked = True
        self._runtime_params[name].set(self, value)

    def set_defaults(self) -> None:
        """
        set default runtime configuration parameters
        """
        for p in self.supported_parameters:
            if p.default:
                self.set_runtime_parameter(p.name, p.default)

    def validate_parameters(self) -> None:
        """
        validate runtime configuration parameters
        """
        raise NotImplementedError()

    def check_target(self) -> Optional[bool]:
        """
        check target for runtime configuration
        """
        raise NotImplementedError()

    def clear(self) -> None:
        """
        clear the runtime configuration
        """
        raise NotImplementedError()


class HotplugRuntimeConfig(RuntimeConfig):
    '''
    NOTE: Currently will fail if trying to hotplug back a core that
    was hotplugged out when the devlib target was created.
    '''

    name: str = 'rt-hotplug'

    @staticmethod
    def set_num_cores(obj: 'HotplugRuntimeConfig', value: Any, core: str) -> None:
        """
        set number of cores to be enabled
        """
        cpus: List[int] = resolve_cpus(core, obj.target)
        max_cores: int = len(cpus)
        value_int = integer(value)
        if value_int > max_cores:
            msg = 'Cannot set number of {}\'s to {}; max is {}'
            raise ValueError(msg.format(core, value_int, max_cores))

        msg = 'CPU{} Hotplugging already configured'
        # Set cpus to be enabled
        for cpu in cpus[:value_int]:
            if cpu in obj.num_cores:
                raise ConfigError(msg.format(cpu))
            obj.num_cores[cpu] = True
        # Set the remaining cpus to be disabled.
        for cpu in cpus[value_int:]:
            if cpu in obj.num_cores:
                raise ConfigError(msg.format(cpu))
            obj.num_cores[cpu] = False

    def __init__(self, target: Target):
        self.num_cores: DefaultDict = defaultdict(dict)
        super(HotplugRuntimeConfig, self).__init__(target)

    def initialize(self) -> None:
        if not self.target.has('hotplug'):
            return
        param_name: str = 'num_cores'
        self._runtime_params[param_name] = \
            RuntimeParameter(param_name, kind=int,
                             constraint=lambda x: 0 <= x <= self.target.number_of_cpus,
                             description="""
                             The number of cpu cores to be online
                             """,
                             setter=self.set_num_cores,
                             setter_params={'core': None})

        for name in unique(self.target.platform.core_names):
            param_name = 'num_{}_cores'.format(name)
            self._runtime_params[param_name] = \
                RuntimeParameter(param_name, kind=int,
                                 constraint=lambda x, name=name: 0 <= x <= len(self.target.core_cpus(name)),
                                 description="""
                                 The number of {} cores to be online
                                 """.format(name),
                                 setter=self.set_num_cores,
                                 setter_params={'core': name})

        for cpu_no in range(self.target.number_of_cpus):
            param_name = 'cpu{}_online'.format(cpu_no)
            self._runtime_params[param_name] = \
                RuntimeParameter(param_name, kind=bool,
                                 description="""
                                 Specify whether cpu{} should be online
                                 """.format(cpu_no),
                                 setter=self.set_num_cores,
                                 setter_params={'core': cpu_no})

        if self.target.has('bl'):
            for cluster in ['big', 'little']:
                param_name = 'num_{}_cores'.format(cluster)
                self._runtime_params[param_name] = \
                    RuntimeParameter(param_name, kind=int,
                                     constraint=lambda x, c=cluster: 0 <= x <= len(resolve_cpus(c, self.target)),
                                     description="""
                                     The number of cores on the {} cluster to be online
                                     """.format(cluster),
                                     setter=self.set_num_cores,
                                     setter_params={'core': cluster})

    def check_target(self) -> Optional[bool]:
        """
        check whether target supports hotplugging
        """
        if not self.target.has('hotplug'):
            raise TargetError('Target does not appear to support hotplug')
        return True

    def validate_parameters(self) -> None:
        """
        validate parameters of hotplug
        """
        if self.num_cores and len(self.num_cores) == self.target.number_of_cpus:
            if all(v is False for v in list(self.num_cores.values())):
                raise ValueError('Cannot set number of all cores to 0')

    def commit(self) -> None:
        '''Online all CPUs required in order before then off-lining'''
        num_cores: List[Tuple[int, bool]] = sorted(self.num_cores.items())
        for cpu, online in num_cores:
            if online:
                cast(HotplugModule, self.target.hotplug).online(cpu)
        for cpu, online in reversed(num_cores):
            if not online:
                cast(HotplugModule, self.target.hotplug).offline(cpu)

    def clear(self) -> None:
        self.num_cores = defaultdict(dict)


class SysfileValuesRuntimeConfig(RuntimeConfig):
    """
    sys file values runtime configuration
    """
    name: str = 'rt-sysfiles'

    # pylint: disable=unused-argument
    @staticmethod
    def set_sysfile(obj: 'SysfileValuesRuntimeConfig',
                    values: Dict[str, Any], core: str) -> None:
        """
        set sys file
        """
        for path, value in values.items():
            verify: bool = True
            if path.endswith('!'):
                verify = False
                path = path[:-1]

            if path in obj.sysfile_values:
                msg = 'Syspath "{}:{}" already specified with a value of "{}"'
                raise ConfigError(msg.format(path, value, obj.sysfile_values[path][0]))

            obj.sysfile_values[path] = (value, verify)

    def __init__(self, target: Target):
        self.sysfile_values: od[str, Tuple[Any, bool]] = OrderedDict()
        super(SysfileValuesRuntimeConfig, self).__init__(target)

    def initialize(self) -> None:
        self._runtime_params['sysfile_values'] = \
            RuntimeParameter('sysfile_values', kind=dict, merge=True,
                             setter=self.set_sysfile,
                             setter_params={'core': None},
                             description="""
                             Sysfile path to be set
                             """)

    def check_target(self) -> Optional[bool]:
        return True

    def validate_parameters(self) -> None:
        return

    def commit(self) -> None:
        for path, (value, verify) in self.sysfile_values.items():
            self.target.write_value(path, value, verify=verify)

    def clear(self) -> None:
        self.sysfile_values = OrderedDict()

    def check_exists(self, path: str) -> None:
        """
        check if file exists in the path
        """
        if not self.target.file_exists(path):
            raise ConfigError('Sysfile "{}" does not exist.'.format(path))


class FreqValue(object):
    """
    frequency values
    """
    def __init__(self, values: Optional[Set[int]]):
        if values is None:
            self.values: Optional[List[int]] = values
        else:
            self.values = sorted(values)

    def __call__(self, value: Union[int, str]):
        '''
        `self.values` can be `None` if the device's supported values could not be retrieved
        for some reason e.g. the cluster was offline, in this case we assume
        the user values will be available and allow any integer values.
        '''
        if self.values is None:
            if isinstance(value, int):
                return value
            else:
                msg: str = 'CPU frequency values could not be retrieved, cannot resolve "{}"'
                raise TargetError(msg.format(value))
        elif isinstance(value, int) and value in self.values:
            return value
        elif isinstance(value, str):
            value = caseless_string(value)
            if value in ['min', 'max']:
                return value

        msg = 'Invalid frequency value: {}; Must be in {}'
        raise ValueError(msg.format(value, self.values))

    def __str__(self):
        return 'valid frequency value: {}'.format(self.values)


class CpufreqRuntimeConfig(RuntimeConfig):
    """
    cpu frequency runtime configuration
    """
    name: str = 'rt-cpufreq'

    @staticmethod
    def set_frequency(obj: 'CpufreqRuntimeConfig', value: Any, core: str):
        obj.set_param(obj, value, core, 'frequency')

    @staticmethod
    def set_max_frequency(obj: 'CpufreqRuntimeConfig', value: Any, core: str):
        obj.set_param(obj, value, core, 'max_frequency')

    @staticmethod
    def set_min_frequency(obj: 'CpufreqRuntimeConfig', value: Any, core: str):
        obj.set_param(obj, value, core, 'min_frequency')

    @staticmethod
    def set_governor(obj: 'CpufreqRuntimeConfig', value: Any, core: str):
        obj.set_param(obj, value, core, 'governor')

    @staticmethod
    def set_governor_tunables(obj: 'CpufreqRuntimeConfig', value: Any, core: str):
        obj.set_param(obj, value, core, 'governor_tunables')

    @staticmethod
    def set_param(obj: 'CpufreqRuntimeConfig', value: Any, core: str, parameter: str):
        '''Method to store passed parameter if it is not already specified for that cpu'''
        cpus: List[int] = resolve_unique_domain_cpus(core, obj.target)
        for cpu in cpus:
            if parameter in obj.config[cpu]:
                msg: str = 'Cannot set "{}" for core "{}"; Parameter for CPU{} has already been set'
                raise ConfigError(msg.format(parameter, core, cpu))
            obj.config[cpu][parameter] = value

    def __init__(self, target: Target):
        self.config: DefaultDict[int, Dict[str, Any]] = defaultdict(dict)
        self.supported_cpu_freqs: Dict[int, Set[int]] = {}
        self.supported_cpu_governors: Dict[int, Set[str]] = {}
        super(CpufreqRuntimeConfig, self).__init__(target)

    def initialize(self) -> None:
        # pylint: disable=too-many-statements
        if not self.target.has('cpufreq'):
            return

        self._retrive_cpufreq_info()
        _, common_freqs, common_gov = self._get_common_values()

        # Add common parameters if available.
        freq_val = FreqValue(common_freqs)
        param_name: str = 'frequency'
        self._runtime_params[param_name] = \
            RuntimeParameter(
                param_name, kind=freq_val,
                setter=self.set_frequency,
                setter_params={'core': None},
                description="""
                The desired frequency for all cores
                """)
        param_name = 'max_frequency'
        self._runtime_params[param_name] = \
            RuntimeParameter(
                param_name, kind=freq_val,
                setter=self.set_max_frequency,
                setter_params={'core': None},
                description="""
                The maximum frequency for all cores
                """)
        param_name = 'min_frequency'
        self._runtime_params[param_name] = \
            RuntimeParameter(
                param_name, kind=freq_val,
                setter=self.set_min_frequency,
                setter_params={'core': None},
                description="""
                The minimum frequency for all cores
                """)

        if common_gov:
            param_name = 'governor'
            self._runtime_params[param_name] = \
                RuntimeParameter(
                    param_name, kind=str,
                    allowed_values=common_gov,
                    setter=self.set_governor,
                    setter_params={'core': None},
                    description="""
                    The governor to be set for all cores
                    """)

        param_name = 'gov_tunables'
        self._runtime_params[param_name] = \
            RuntimeParameter(
                param_name, kind=dict,
                merge=True,
                setter=self.set_governor_tunables,
                setter_params={'core': None},
                aliases=['governor_tunables'],
                description="""
                The governor tunables to be set for all cores
                """)

        # Add core name parameters
        for name in unique(self.target.platform.core_names):
            cpu: int = resolve_unique_domain_cpus(name, self.target)[0]
            freq_val = FreqValue(self.supported_cpu_freqs.get(cpu))
            avail_govs: Optional[Set[str]] = self.supported_cpu_governors.get(cpu)

            param_name = '{}_frequency'.format(name)
            self._runtime_params[param_name] = \
                RuntimeParameter(
                    param_name, kind=freq_val,
                    setter=self.set_frequency,
                    setter_params={'core': name},
                    description="""
                    The desired frequency for the {} cores
                    """.format(name))
            param_name = '{}_max_frequency'.format(name)
            self._runtime_params[param_name] = \
                RuntimeParameter(
                    param_name, kind=freq_val,
                    setter=self.set_max_frequency,
                    setter_params={'core': name},
                    description="""
                    The maximum frequency for the {} cores
                    """.format(name))
            param_name = '{}_min_frequency'.format(name)
            self._runtime_params[param_name] = \
                RuntimeParameter(
                    param_name, kind=freq_val,
                    setter=self.set_min_frequency,
                    setter_params={'core': name},
                    description="""
                    The minimum frequency for the {} cores
                    """.format(name))
            param_name = '{}_governor'.format(name)
            self._runtime_params[param_name] = \
                RuntimeParameter(
                    param_name, kind=str,
                    allowed_values=avail_govs,
                    setter=self.set_governor,
                    setter_params={'core': name},
                    description="""
                    The governor to be set for the {} cores
                    """.format(name))
            param_name = '{}_gov_tunables'.format(name)
            self._runtime_params[param_name] = \
                RuntimeParameter(
                    param_name, kind=dict,
                    setter=self.set_governor_tunables,
                    setter_params={'core': name},
                    merge=True,
                    description="""
                    The governor tunables to be set for the {} cores
                    """.format(name))

        # Add cpuX parameters.
        for cpu_no in range(self.target.number_of_cpus):
            freq_val = FreqValue(self.supported_cpu_freqs.get(cpu_no))
            avail_govs = self.supported_cpu_governors.get(cpu_no)

            param_name = 'cpu{}_frequency'.format(cpu_no)
            self._runtime_params[param_name] = \
                RuntimeParameter(
                    param_name, kind=freq_val,
                    setter=self.set_frequency,
                    setter_params={'core': cpu_no},
                    description="""
                    The desired frequency for cpu{}
                    """.format(cpu_no))
            param_name = 'cpu{}_max_frequency'.format(cpu_no)
            self._runtime_params[param_name] = \
                RuntimeParameter(
                    param_name, kind=freq_val,
                    setter=self.set_max_frequency,
                    setter_params={'core': cpu_no},
                    description="""
                    The maximum frequency for cpu{}
                    """.format(cpu_no))
            param_name = 'cpu{}_min_frequency'.format(cpu_no)
            self._runtime_params[param_name] = \
                RuntimeParameter(
                    param_name, kind=freq_val,
                    setter=self.set_min_frequency,
                    setter_params={'core': cpu_no},
                    description="""
                    The minimum frequency for cpu{}
                    """.format(cpu_no))
            param_name = 'cpu{}_governor'.format(cpu_no)
            self._runtime_params[param_name] = \
                RuntimeParameter(
                    param_name, kind=str,
                    allowed_values=avail_govs,
                    setter=self.set_governor,
                    setter_params={'core': cpu_no},
                    description="""
                    The governor to be set for cpu{}
                    """.format(cpu_no))
            param_name = 'cpu{}_gov_tunables'.format(cpu_no)
            self._runtime_params[param_name] = \
                RuntimeParameter(
                    param_name, kind=dict,
                    setter=self.set_governor_tunables,
                    setter_params={'core': cpu_no},
                    merge=True,
                    description="""
                    The governor tunables to be set for cpu{}
                    """.format(cpu_no))

        # Add big.little cores if present on device.
        if self.target.has('bl'):
            for cluster in ['big', 'little']:
                cpu = resolve_unique_domain_cpus(cluster, self.target)[0]
                freq_val = FreqValue(self.supported_cpu_freqs.get(cpu))
                avail_govs = self.supported_cpu_governors.get(cpu)
                param_name = '{}_frequency'.format(cluster)

                self._runtime_params[param_name] = \
                    RuntimeParameter(
                        param_name, kind=freq_val,
                        setter=self.set_frequency,
                        setter_params={'core': cluster},
                        description="""
                        The desired frequency for the {} cluster
                        """.format(cluster))
                param_name = '{}_max_frequency'.format(cluster)
                self._runtime_params[param_name] = \
                    RuntimeParameter(
                        param_name, kind=freq_val,
                        setter=self.set_max_frequency,
                        setter_params={'core': cluster},
                        description="""
                        The maximum frequency for the {} cluster
                        """.format(cluster))
                param_name = '{}_min_frequency'.format(cluster)
                self._runtime_params[param_name] = \
                    RuntimeParameter(
                        param_name, kind=freq_val,
                        setter=self.set_min_frequency,
                        setter_params={'core': cluster},
                        description="""
                        The minimum frequency for the {} cluster
                        """.format(cluster))
                param_name = '{}_governor'.format(cluster)
                self._runtime_params[param_name] = \
                    RuntimeParameter(
                        param_name, kind=str,
                        allowed_values=avail_govs,
                        setter=self.set_governor,
                        setter_params={'core': cluster},
                        description="""
                        The governor to be set for the {} cores
                        """.format(cluster))
                param_name = '{}_gov_tunables'.format(cluster)
                self._runtime_params[param_name] = \
                    RuntimeParameter(
                        param_name, kind=dict,
                        setter=self.set_governor_tunables,
                        setter_params={'core': cluster},
                        merge=True,
                        description="""
                        The governor tunables to be set for the {} cores
                        """.format(cluster))

    def check_target(self) -> Optional[bool]:
        if not self.target.has('cpufreq'):
            raise TargetError('Target does not appear to support cpufreq')
        return True

    def validate_parameters(self) -> None:
        '''Method to validate parameters against each other'''
        for cpu in self.config:
            config: Dict[str, Any] = self.config[cpu]
            minf: int = config.get('min_frequency') or 0
            maxf: int = config.get('max_frequency') or 0
            freq: int = config.get('frequency') or 0

            if freq and minf:
                msg: str = 'CPU{}: Can\'t set both cpu frequency and minimum frequency'
                raise ConfigError(msg.format(cpu))
            if freq and maxf:
                msg = 'CPU{}: Can\'t set both cpu frequency and maximum frequency'
                raise ConfigError(msg.format(cpu))

            if (maxf and minf) and self._resolve_freq(minf, cpu) > self._resolve_freq(maxf, cpu):
                msg = 'CPU{}: min_frequency "{}" cannot be greater than max_frequency "{}"'
                raise ConfigError(msg.format(cpu, minf, maxf))

    def commit(self) -> None:
        for cpu in self.config:
            config: Dict[str, Any] = self.config[cpu]
            freq: int = self._resolve_freq(config.get('frequency') or 0, cpu)
            minf: int = self._resolve_freq(config.get('min_frequency') or 0, cpu)
            maxf: int = self._resolve_freq(config.get('max_frequency') or 0, cpu)

            self.configure_governor(cpu,
                                    config.get('governor'),
                                    config.get('governor_tunables'))
            self.configure_frequency(cpu, freq, minf, maxf, config.get('governor'))

    def clear(self):
        self.config = defaultdict(dict)

    def configure_governor(self, cpu: int, governor: Optional[str] = None,
                           gov_tunables: Optional[Dict] = None) -> None:
        """
        configure governor
        """
        if not governor and not gov_tunables:
            return
        if cpu not in self.target.list_online_cpus():
            msg: str = 'Cannot configure governor for {} as no CPUs are online.'
            raise TargetError(msg.format(cpu))
        if not governor:
            governor = cast(CpufreqModule, self.target.cpufreq).get_governor(cpu)
        if not gov_tunables:
            gov_tunables = {}
        cast(CpufreqModule, self.target.cpufreq).set_governor(cpu, governor, **gov_tunables)

    def configure_frequency(self, cpu: int, freq: Optional[int] = None, min_freq: Optional[int] = None,
                            max_freq: Optional[int] = None, governor: Optional[str] = None) -> None:
        """
        configure frequency
        """
        if freq and (min_freq or max_freq):
            msg: str = 'Cannot specify both frequency and min/max frequency'
            raise ConfigError(msg)

        if cpu not in self.target.list_online_cpus():
            msg = 'Cannot configure frequencies for CPU{} as no CPUs are online.'
            raise TargetError(msg.format(cpu))

        if freq:
            self._set_frequency(cpu, freq, governor)
        else:
            self._set_min_max_frequencies(cpu, min_freq, max_freq)

    def _resolve_freq(self, value: Union[str, int], cpu: int) -> int:
        if value == 'min':
            value = cast(CpufreqModule, self.target.cpufreq).get_min_available_frequency(cpu) or 0
        elif value == 'max':
            value = cast(CpufreqModule, self.target.cpufreq).get_max_available_frequency(cpu) or 0
        return cast(int, value)

    def _set_frequency(self, cpu: int, freq: int, governor: Optional[str]) -> None:
        """
        set frequency to the cpu under the specified governor
        """
        if not governor:
            governor = cast(CpufreqModule, self.target.cpufreq).get_governor(cpu)
        has_userspace = governor == 'userspace'

        # Sets all frequency to be to desired frequency
        if freq < cast(CpufreqModule, self.target.cpufreq).get_frequency(cpu):
            cast(CpufreqModule, self.target.cpufreq).set_min_frequency(cpu, freq)
            if has_userspace:
                cast(CpufreqModule, self.target.cpufreq).set_frequency(cpu, freq)
            cast(CpufreqModule, self.target.cpufreq).set_max_frequency(cpu, freq)
        else:
            cast(CpufreqModule, self.target.cpufreq).set_max_frequency(cpu, freq)
            if has_userspace:
                cast(CpufreqModule, self.target.cpufreq).set_frequency(cpu, freq)
            cast(CpufreqModule, self.target.cpufreq).set_min_frequency(cpu, freq)

    def _set_min_max_frequencies(self, cpu: int, min_freq: Optional[int], max_freq: Optional[int]) -> None:
        """
        set minimum and maximum frequencies
        """
        min_freq_set: bool = False
        current_min_freq: int = cast(CpufreqModule, self.target.cpufreq).get_min_frequency(cpu)
        current_max_freq: int = cast(CpufreqModule, self.target.cpufreq).get_max_frequency(cpu)
        if max_freq:
            if max_freq < current_min_freq:
                if min_freq:
                    cast(CpufreqModule, self.target.cpufreq).set_min_frequency(cpu, min_freq)
                    cast(CpufreqModule, self.target.cpufreq).set_max_frequency(cpu, max_freq)
                    min_freq_set = True
                else:
                    msg: str = 'CPU {}: Cannot set max_frequency ({}) below current min frequency ({}).'
                    raise ConfigError(msg.format(cpu, max_freq, current_min_freq))
            else:
                cast(CpufreqModule, self.target.cpufreq).set_max_frequency(cpu, max_freq)
        if min_freq and not min_freq_set:
            current_max_freq = max_freq or current_max_freq
            if min_freq > current_max_freq:
                msg = 'CPU {}: Cannot set min_frequency ({}) above current max frequency ({}).'
                raise ConfigError(msg.format(cpu, min_freq, current_max_freq))
            cast(CpufreqModule, self.target.cpufreq).set_min_frequency(cpu, min_freq)

    def _retrive_cpufreq_info(self) -> None:
        '''
        Tries to retrieve cpu freq information for all cpus on device.
        For each cpu domain, only one cpu is queried for information and
        duplicated across related cpus. This is to reduce calls to the target
        and as long as one core per domain is online the remaining cpus information
        can still be populated.
        '''
        for cluster_cpu in resolve_unique_domain_cpus('all', self.target):
            domain_cpus: List[int] = cast(CpufreqModule, self.target.cpufreq).get_related_cpus(cluster_cpu)
            for cpu in domain_cpus:
                if cpu in self.target.list_online_cpus():
                    supported_cpu_freqs: Set[int] = cast(CpufreqModule, self.target.cpufreq).list_frequencies(cpu)
                    supported_cpu_governors: Set[str] = cast(CpufreqModule, self.target.cpufreq).list_governors(cpu)
                    break
            else:
                msg: str = 'CPUFreq information could not be retrieved for{};'\
                    'Will not be validated against device.'
                logger.debug(msg.format(' CPU{},'.format(cpu for cpu in domain_cpus)))
                return

            for cpu in domain_cpus:
                self.supported_cpu_freqs[cpu] = supported_cpu_freqs
                self.supported_cpu_governors[cpu] = supported_cpu_governors

    def _get_common_values(self) -> Tuple[Optional[Set[int]], Optional[Set[int]], Optional[Set[str]]]:
        ''' Find common values for frequency and governors across all cores'''
        common_freqs: Optional[Set[int]] = None
        common_gov: Optional[Set[str]] = None
        all_freqs: Optional[Set[int]] = None
        initialized: bool = False
        for cpu in resolve_unique_domain_cpus('all', self.target):
            if not initialized:
                initialized = True
                common_freqs = set(self.supported_cpu_freqs.get(cpu) or [])
                all_freqs = copy(common_freqs)
                common_gov = set(self.supported_cpu_governors.get(cpu) or [])
            else:
                common_freqs = common_freqs.intersection(self.supported_cpu_freqs.get(cpu) or set()) if common_freqs else set()
                all_freqs = all_freqs.union(self.supported_cpu_freqs.get(cpu) or set()) if all_freqs else set()
                common_gov = common_gov.intersection(self.supported_cpu_governors.get(cpu) or set()) if common_gov else set()

        return all_freqs, common_freqs, common_gov


class IdleStateValue(object):
    """
    value of idle state
    """
    def __init__(self, values: Optional[List[CpuidleState]]):
        if values is None:
            self.values = values
        else:
            self.values = [(value.id, value.name, value.desc) for value in values]

    def __call__(self, value: Union[List[str], str]):
        if self.values is None:
            return value

        if isinstance(value, str):
            value = caseless_string(value)
            if value == 'all':
                return [state[0] for state in self.values]
            elif value == 'none':
                return []
            else:
                return [self._get_state_ID(value)]

        elif isinstance(value, list):
            valid_states: List[str] = []
            for state in value:
                valid_states.append(self._get_state_ID(state))
            return valid_states
        else:
            raise ValueError('Invalid IdleState: "{}"'.format(value))

    def _get_state_ID(self, value: str) -> str:
        '''Checks passed state and converts to its ID'''
        value = caseless_string(value)
        if not self.values:
            raise ValueError('self.values is none')
        for s_id, s_name, s_desc in self.values:
            if value in (s_id, s_name, s_desc):
                return s_id
        msg = 'Invalid IdleState: "{}"; Must be in {}'
        raise ValueError(msg.format(value, self.values))

    def __str__(self):
        return 'valid idle state: "{}"'.format(self.values).replace('\'', '')


class CpuidleRuntimeConfig(RuntimeConfig):
    """
    cpu idle runtime configuration
    """
    name: str = 'rt-cpuidle'

    @staticmethod
    def set_idle_state(obj: 'CpuidleRuntimeConfig', value: Any, core: str) -> None:
        cpus: List[int] = resolve_cpus(core, obj.target)
        for cpu in cpus:
            obj.config[cpu] = []
            for state in value:
                obj.config[cpu].append(state)

    def __init__(self, target: Target):
        self.config: DefaultDict = defaultdict(dict)
        self.supported_idle_states: Dict[int, List[CpuidleState]] = {}
        super(CpuidleRuntimeConfig, self).__init__(target)

    def initialize(self) -> None:
        if not self.target.has('cpuidle'):
            return

        self._retrieve_device_idle_info()

        common_idle_states: List[CpuidleState] = self._get_common_idle_values()
        idle_state_val = IdleStateValue(common_idle_states)

        if common_idle_states:
            param_name: str = 'idle_states'
            self._runtime_params[param_name] = \
                RuntimeParameter(
                    param_name, kind=idle_state_val,
                    setter=self.set_idle_state,
                    setter_params={'core': None},
                    description="""
                    The idle states to be set for all cores
                    """)

        for name in unique(self.target.platform.core_names):
            cpu: int = resolve_cpus(name, self.target)[0]
            idle_state_val = IdleStateValue(self.supported_idle_states.get(cpu))
            param_name = '{}_idle_states'.format(name)
            self._runtime_params[param_name] = \
                RuntimeParameter(
                    param_name, kind=idle_state_val,
                    setter=self.set_idle_state,
                    setter_params={'core': name},
                    description="""
                    The idle states to be set for {} cores
                    """.format(name))

        for cpu_no in range(self.target.number_of_cpus):
            idle_state_val = IdleStateValue(self.supported_idle_states.get(cpu_no))
            param_name = 'cpu{}_idle_states'.format(cpu_no)
            self._runtime_params[param_name] = \
                RuntimeParameter(
                    param_name, kind=idle_state_val,
                    setter=self.set_idle_state,
                    setter_params={'core': cpu_no},
                    description="""
                    The idle states to be set for cpu{}
                    """.format(cpu_no))

        if self.target.has('bl'):
            for cluster in ['big', 'little']:
                cpu = resolve_cpus(cluster, self.target)[0]
                idle_state_val = IdleStateValue(self.supported_idle_states.get(cpu))
                param_name = '{}_idle_states'.format(cluster)
                self._runtime_params[param_name] = \
                    RuntimeParameter(
                        param_name, kind=idle_state_val,
                        setter=self.set_idle_state,
                        setter_params={'core': cluster},
                        description="""
                        The idle states to be set for the {} cores
                        """.format(cluster))

    def check_target(self) -> Optional[bool]:
        if not self.target.has('cpuidle'):
            raise TargetError('Target does not appear to support cpuidle')
        return True

    def validate_parameters(self) -> None:
        return

    def clear(self) -> None:
        self.config = defaultdict(dict)

    def commit(self) -> None:
        for cpu in self.config:
            idle_states: Set[str] = set(state.id for state in self.supported_idle_states.get(cpu, []))
            enabled: Set[str] = self.config[cpu]
            disabled: Set[str] = idle_states.difference(enabled)
            for state in enabled:
                cast(Cpuidle, self.target.cpuidle).enable(state, cpu)
            for state in disabled:
                cast(Cpuidle, self.target.cpuidle).disable(state, cpu)

    def _retrieve_device_idle_info(self) -> None:
        """
        get the device idle info
        """
        for cpu in range(self.target.number_of_cpus):
            self.supported_idle_states[cpu] = cast(Cpuidle, self.target.cpuidle).get_states(cpu)

    def _get_common_idle_values(self) -> List[CpuidleState]:
        '''Find common values for cpu idle states across all cores'''
        common_idle_states: List[CpuidleState] = []
        for cpu in range(self.target.number_of_cpus):
            for state in self.supported_idle_states.get(cpu) or []:
                if state.name not in common_idle_states:
                    common_idle_states.append(state)
        return common_idle_states


ScreenOrientation = enum(['NATURAL', 'LEFT', 'INVERTED', 'RIGHT'])


class AndroidRuntimeConfig(RuntimeConfig):
    """
    android runtime configuration
    """
    name: str = 'rt-android'

    @staticmethod
    def set_brightness(obj: 'AndroidRuntimeConfig', value: Optional[int]) -> None:
        """
        set brightness
        """
        if value is not None:
            obj.config['brightness'] = value

    @staticmethod
    def set_airplane_mode(obj: 'AndroidRuntimeConfig', value: Optional[bool]) -> None:
        """
        set airplane mode
        """
        if value is not None:
            obj.config['airplane_mode'] = value

    @staticmethod
    def set_rotation(obj: 'AndroidRuntimeConfig', value: Any) -> None:
        """
        set rotation
        """
        if value is not None:
            obj.config['rotation'] = value.value

    @staticmethod
    def set_screen_state(obj: 'AndroidRuntimeConfig', value: Optional[bool]) -> None:
        """
        set screen on or off state
        """
        if value is not None:
            obj.config['screen_on'] = value

    @staticmethod
    def set_unlock_screen(obj: 'AndroidRuntimeConfig', value: str) -> None:
        """
        set unlock screen
        """
        if value is not None:
            obj.config['unlock_screen'] = value

    def __init__(self, target: Target):
        self.config: DefaultDict[str, Any] = defaultdict(dict)
        super(AndroidRuntimeConfig, self).__init__(target)
        self.target = cast(AndroidTarget, target)

    def initialize(self) -> None:
        if self.target.os not in ['android', 'chromeos']:
            return
        if self.target.os == 'chromeos' and not self.target.supports_android:
            return

        param_name: str = 'brightness'
        self._runtime_params[param_name] = \
            RuntimeParameter(
                param_name, kind=int,
                constraint=lambda x: 0 <= x <= 255,
                default=127,
                setter=self.set_brightness,
                description="""
                Specify the screen brightness to be set for
                the device
                """)

        if self.target.os == 'android':
            param_name = 'airplane_mode'
            self._runtime_params[param_name] = \
                RuntimeParameter(
                    param_name, kind=bool,
                    setter=self.set_airplane_mode,
                    description="""
                    Specify whether airplane mode should be
                    enabled for the device
                    """)

            param_name = 'rotation'
            self._runtime_params[param_name] = \
                RuntimeParameter(
                    param_name, kind=ScreenOrientation,
                    setter=self.set_rotation,
                    description="""
                    Specify the screen orientation for the device
                    """)

            param_name = 'screen_on'
            self._runtime_params[param_name] = \
                RuntimeParameter(
                    param_name, kind=bool,
                    default=True,
                    setter=self.set_screen_state,
                    description="""
                    Specify whether the device screen should be on
                    """)

            param_name = 'unlock_screen'
            self._runtime_params[param_name] = \
                RuntimeParameter(
                    param_name, kind=str,
                    default=None,
                    setter=self.set_unlock_screen,
                    description="""
                    Specify how the device screen should be unlocked (e.g., vertical)
                    """)

    def check_target(self) -> Optional[bool]:
        if self.target.os != 'android' and self.target.os != 'chromeos':
            raise ConfigError('Target does not appear to be running Android')
        if self.target.os == 'chromeos' and not self.target.supports_android:
            raise ConfigError('Target does not appear to support Android')
        return True

    def validate_parameters(self) -> None:
        pass

    def commit(self) -> None:
        # pylint: disable=too-many-branches
        if 'airplane_mode' in self.config:
            new_airplane_mode: bool = self.config['airplane_mode']
            old_airplane_mode: bool = cast(Callable, self.target.get_airplane_mode)()
            cast(Callable, self.target.set_airplane_mode)(new_airplane_mode)

            # If we've just switched airplane mode off, wait a few seconds to
            # enable the network state to stabilise. That's helpful if we're
            # about to run a workload that is going to check for network
            # connectivity.
            if old_airplane_mode and not new_airplane_mode:
                self.logger.info('Disabled airplane mode, waiting up to 20 seconds for network setup')
                network_is_ready: bool = False
                for _ in range(4):
                    time.sleep(5)
                    network_is_ready = self.target.is_network_connected()
                    if network_is_ready:
                        break
                if network_is_ready:
                    self.logger.info("Found a network")
                else:
                    self.logger.warning("Network unreachable")

        if 'brightness' in self.config:
            cast(Callable, self.target.set_brightness)(self.config['brightness'])

        if 'rotation' in self.config:
            cast(Callable, self.target.set_rotation)(self.config['rotation'])

        if 'screen_on' in self.config:
            if self.config['screen_on']:
                cast(Callable, self.target.ensure_screen_is_on)()
            else:
                cast(Callable, self.target.ensure_screen_is_off)()

        if self.config.get('unlock_screen'):
            cast(Callable, self.target.ensure_screen_is_on)()
            if cast(Callable, self.target.is_screen_locked)():
                cast(Callable, self.target.swipe_to_unlock)(self.config['unlock_screen'])

    def clear(self) -> None:
        self.config.clear()
