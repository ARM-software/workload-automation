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
# pylint: disable=protected-access

import os

from devlib.exception import TargetError
from devlib.target import (KernelConfig, KernelVersion, Cpuinfo,
                           AndroidTarget, Target)
from devlib.utils.android import AndroidProperties

from wa.framework.configuration.core import settings
from wa.framework.exception import ConfigError
from wa.utils.serializer import read_pod, write_pod, Podable
from wa.utils.misc import atomic_write_path
from typing import cast, Optional, List, Dict, Tuple, Any
from devlib.module.cpufreq import CpufreqModule
from devlib.module.cpuidle import Cpuidle


def cpuinfo_from_pod(pod: Dict[str, Any]) -> Cpuinfo:
    """
    get cpu info (devlib) from a plain old datastructure
    """
    cpuinfo = Cpuinfo('')
    cpuinfo.sections = pod['cpuinfo']
    lines: List[str] = []
    for section in cpuinfo.sections:
        for key, value in section.items():
            line = '{}: {}'.format(key, value)
            lines.append(line)
        lines.append('')
    cpuinfo.text = '\n'.join(lines)
    return cpuinfo


def kernel_version_from_pod(pod) -> KernelVersion:
    """
    get kernel version from plain old datastructure
    """
    release_string: str = pod['kernel_release']
    version_string: str = pod['kernel_version']
    if release_string:
        if version_string:
            kernel_string = '{} #{}'.format(release_string, version_string)
        else:
            kernel_string = release_string
    else:
        kernel_string = '#{}'.format(version_string)
    return KernelVersion(kernel_string)


def kernel_config_from_pod(pod: Dict[str, Any]) -> KernelConfig:
    """
    get kernel configuration from plain old datastructure
    """
    config = KernelConfig('')
    config.typed_config._config = pod['kernel_config']
    lines: List[str] = []
    for key, value in config.items():
        if value == 'n':
            lines.append('# {} is not set'.format(key))
        else:
            lines.append('{}={}'.format(key, value))
    config.text = '\n'.join(lines)
    return config


class CpufreqInfo(Podable):
    """
    cpu frequency information
    """
    _pod_serialization_version: int = 1

    @staticmethod
    def from_pod(pod: Dict[str, Any]) -> 'CpufreqInfo':
        pod = CpufreqInfo._upgrade_pod(pod)
        return CpufreqInfo(**pod)

    def __init__(self, **kwargs) -> None:
        super(CpufreqInfo, self).__init__()
        self.available_frequencies: List[int] = kwargs.pop('available_frequencies', [])
        self.available_governors: List[str] = kwargs.pop('available_governors', [])
        self.related_cpus: List[int] = kwargs.pop('related_cpus', [])
        self.driver: Optional[str] = kwargs.pop('driver', None)
        self._pod_version: int = kwargs.pop('_pod_version', self._pod_serialization_version)

    def to_pod(self) -> Dict[str, Any]:
        pod = super(CpufreqInfo, self).to_pod()
        pod.update(self.__dict__)
        return pod

    @staticmethod
    def _pod_upgrade_v1(pod: Dict[str, Any]) -> Dict[str, Any]:
        pod['_pod_version'] = pod.get('_pod_version', 1)
        return pod

    def __repr__(self):
        return 'Cpufreq({} {})'.format(self.driver, self.related_cpus)

    __str__ = __repr__


class IdleStateInfo(Podable):
    """
    idle state information
    """
    _pod_serialization_version: int = 1

    @staticmethod
    def from_pod(pod: Dict[str, Any]) -> 'IdleStateInfo':
        pod = IdleStateInfo._upgrade_pod(pod)
        return IdleStateInfo(**pod)

    def __init__(self, **kwargs) -> None:
        super(IdleStateInfo, self).__init__()
        self.name: Optional[str] = kwargs.pop('name', None)
        self.desc: Optional[str] = kwargs.pop('desc', None)
        self.power: Optional[int] = kwargs.pop('power', None)
        self.latency: Optional[int] = kwargs.pop('latency', None)
        self._pod_version: int = kwargs.pop('_pod_version', self._pod_serialization_version)

    def to_pod(self) -> Dict[str, Any]:
        pod = super(IdleStateInfo, self).to_pod()
        pod.update(self.__dict__)
        return pod

    @staticmethod
    def _pod_upgrade_v1(pod: Dict[str, Any]) -> Dict[str, Any]:
        pod['_pod_version'] = pod.get('_pod_version', 1)
        return pod

    def __repr__(self):
        return 'IdleState({}/{})'.format(self.name, self.desc)

    __str__ = __repr__


class CpuidleInfo(Podable):
    """
    cpu idle information
    """
    _pod_serialization_version: int = 1

    @staticmethod
    def from_pod(pod: Dict[str, Any]) -> 'CpuidleInfo':
        pod = CpuidleInfo._upgrade_pod(pod)
        instance = CpuidleInfo()
        instance._pod_version = pod['_pod_version']
        instance.governor = pod['governor']
        instance.driver = pod['driver']
        instance.states = [IdleStateInfo.from_pod(s) for s in pod['states']]
        return instance

    @property
    def num_states(self) -> int:
        """
        number of cpu idle states
        """
        return len(self.states)

    def __init__(self) -> None:
        super(CpuidleInfo, self).__init__()
        self.governor: Optional[str] = None
        self.driver: Optional[str] = None
        self.states: List[IdleStateInfo] = []

    def to_pod(self) -> Dict[str, Any]:
        pod = super(CpuidleInfo, self).to_pod()
        pod['governor'] = self.governor
        pod['driver'] = self.driver
        pod['states'] = [s.to_pod() for s in self.states]
        return pod

    @staticmethod
    def _pod_upgrade_v1(pod: Dict[str, Any]) -> Dict[str, Any]:
        pod['_pod_version'] = pod.get('_pod_version', 1)
        return pod

    def __repr__(self):
        return 'Cpuidle({}/{} {} states)'.format(
            self.governor, self.driver, self.num_states)

    __str__ = __repr__


class CpuInfo(Podable):
    """
    Cpu information
    """
    _pod_serialization_version: int = 1

    @staticmethod
    def from_pod(pod) -> 'CpuInfo':
        instance = cast('CpuInfo', super(CpuInfo, CpuInfo).from_pod(pod))
        instance.id = pod['id']
        instance.name = pod['name']
        instance.architecture = pod['architecture']
        instance.features = pod['features']
        instance.cpufreq = CpufreqInfo.from_pod(pod['cpufreq'])
        instance.cpuidle = CpuidleInfo.from_pod(pod['cpuidle'])
        return instance

    def __init__(self) -> None:
        super(CpuInfo, self).__init__()
        self.id: Optional[int] = None
        self.name: Optional[str] = None
        self.architecture: Optional[str] = None
        self.features: List[str] = []
        self.cpufreq = CpufreqInfo()
        self.cpuidle = CpuidleInfo()

    def to_pod(self) -> Dict[str, Any]:
        pod = super(CpuInfo, self).to_pod()
        pod['id'] = self.id
        pod['name'] = self.name
        pod['architecture'] = self.architecture
        pod['features'] = self.features
        pod['cpufreq'] = self.cpufreq.to_pod()
        pod['cpuidle'] = self.cpuidle.to_pod()
        return pod

    @staticmethod
    def _pod_upgrade_v1(pod: Dict[str, Any]) -> Dict[str, Any]:
        pod['_pod_version'] = pod.get('_pod_version', 1)
        return pod

    def __repr__(self):
        return 'Cpu({} {})'.format(self.id, self.name)

    __str__ = __repr__


def get_target_info(target: Target) -> 'TargetInfo':
    """
    get information about the target
    """
    info = TargetInfo()
    info.target = target.__class__.__name__
    info.modules = target.modules
    info.os = target.os
    info.os_version = target.os_version
    info.system_id = target.system_id
    info.abi = target.abi
    info.is_rooted = target.is_rooted
    info.kernel_version = target.kernel_version
    info.kernel_config = target.config
    info.hostname = target.hostname
    info.hostid = target.hostid

    try:
        info.sched_features = cast(str, target.read_value('/sys/kernel/debug/sched_features')).split()
    except TargetError:
        # best effort -- debugfs might not be mounted
        pass

    for i, name in enumerate(target.cpuinfo.cpu_names):
        cpu = CpuInfo()
        cpu.id = i
        cpu.name = name
        cpu.features = target.cpuinfo.get_cpu_features(i)
        cpu.architecture = target.cpuinfo.architecture

        if target.has('cpufreq'):
            cpu.cpufreq.available_governors = cast(CpufreqModule, target.cpufreq).list_governors(i)
            cpu.cpufreq.available_frequencies = cast(CpufreqModule, target.cpufreq).list_frequencies(i)
            cpu.cpufreq.related_cpus = cast(CpufreqModule, target.cpufreq).get_related_cpus(i)
            cpu.cpufreq.driver = cast(CpufreqModule, target.cpufreq).get_driver(i)

        if target.has('cpuidle'):
            cpu.cpuidle.driver = cast(Cpuidle, target.cpuidle).get_driver()
            cpu.cpuidle.governor = cast(Cpuidle, target.cpuidle).get_governor()
            for state in cast(Cpuidle, target.cpuidle).get_states(i):
                state_info = IdleStateInfo()
                state_info.name = state.name
                state_info.desc = state.desc
                state_info.power = state.power
                state_info.latency = state.latency
                cpu.cpuidle.states.append(state_info)

        info.cpus.append(cpu)

    info.page_size_kb = target.page_size_kb

    if isinstance(target, AndroidTarget):
        info.screen_resolution = target.screen_resolution
        info.prop = target.getprop()
        info.android_id = target.android_id

    return info


def read_target_info_cache() -> Dict[str, Any]:
    """
    read cached target information
    """
    if not os.path.exists(settings.cache_directory):
        os.makedirs(settings.cache_directory)
    if not os.path.isfile(settings.target_info_cache_file):
        return {}
    return read_pod(settings.target_info_cache_file)


def write_target_info_cache(cache: Dict[str, Any]) -> None:
    """
    cache the target information
    """
    if not os.path.exists(settings.cache_directory):
        os.makedirs(settings.cache_directory)
    with atomic_write_path(settings.target_info_cache_file) as at_path:
        write_pod(cache, at_path)


def get_target_info_from_cache(system_id: str,
                               cache: Optional[Dict[str, Any]] = None) -> Optional['TargetInfo']:
    """
    get target information from cache
    """
    if cache is None:
        cache = read_target_info_cache()
    pod = cache.get(system_id, None)

    if not pod:
        return None

    _pod_version: int = pod.get('_pod_version', 0)
    if _pod_version != TargetInfo._pod_serialization_version:
        msg = 'Target info version mismatch. Expected {}, but found {}.\nTry deleting {}'
        raise ConfigError(msg.format(TargetInfo._pod_serialization_version, _pod_version,
                                     settings.target_info_cache_file))
    return TargetInfo.from_pod(pod)


def cache_target_info(target_info: 'TargetInfo', overwrite: bool = False,
                      cache: Optional[Dict[str, Any]] = None):
    """
    store target information into the cache
    """
    if cache is None:
        cache = read_target_info_cache()
    if target_info.system_id in cache and not overwrite:
        raise ValueError('TargetInfo for {} is already in cache.'.format(target_info.system_id))
    if target_info.system_id:
        cache[target_info.system_id] = target_info.to_pod()
    write_target_info_cache(cache)


class TargetInfo(Podable):
    """
    target information
    """
    _pod_serialization_version: int = 5

    @staticmethod
    def from_pod(pod) -> 'TargetInfo':
        instance = cast('TargetInfo', super(TargetInfo, TargetInfo).from_pod(pod))
        instance.target = pod['target']
        instance.modules = pod['modules']
        instance.abi = pod['abi']
        instance.cpus = [CpuInfo.from_pod(c) for c in pod['cpus']]
        instance.os = pod['os']
        instance.os_version = pod['os_version']
        instance.system_id = pod['system_id']
        instance.hostid = pod['hostid']
        instance.hostname = pod['hostname']
        instance.abi = pod['abi']
        instance.is_rooted = pod['is_rooted']
        instance.kernel_version = kernel_version_from_pod(pod)
        instance.kernel_config = kernel_config_from_pod(pod)
        instance.sched_features = pod['sched_features']
        instance.page_size_kb = pod.get('page_size_kb')
        if instance.os == 'android':
            instance.screen_resolution = pod['screen_resolution']
            instance.prop = AndroidProperties('')
            instance.prop._properties = pod['prop']
            instance.android_id = pod['android_id']

        return instance

    def __init__(self) -> None:
        super(TargetInfo, self).__init__()
        self.target: Optional[str] = None
        self.modules: List[str] = []
        self.cpus: List[CpuInfo] = []
        self.os: Optional[str] = None
        self.os_version: Optional[Dict[str, str]] = None
        self.system_id: Optional[str] = None
        self.hostid: Optional[int] = None
        self.hostname: Optional[str] = None
        self.abi: Optional[str] = None
        self.is_rooted: Optional[bool] = None
        self.kernel_version: Optional[KernelVersion] = None
        self.kernel_config: Optional[KernelConfig] = None
        self.sched_features: Optional[List[str]] = None
        self.screen_resolution: Optional[Tuple[int, int]] = None
        self.prop: Optional[AndroidProperties] = None
        self.android_id: Optional[str] = None
        self.page_size_kb: Optional[int] = None

    def to_pod(self) -> Dict[str, Any]:
        pod = super(TargetInfo, self).to_pod()
        pod['target'] = self.target
        pod['modules'] = self.modules
        pod['abi'] = self.abi
        pod['cpus'] = [c.to_pod() for c in self.cpus]
        pod['os'] = self.os
        pod['os_version'] = self.os_version
        pod['system_id'] = self.system_id
        pod['hostid'] = self.hostid
        pod['hostname'] = self.hostname
        pod['abi'] = self.abi
        pod['is_rooted'] = self.is_rooted
        pod['kernel_release'] = self.kernel_version.release if self.kernel_version else ''
        pod['kernel_version'] = self.kernel_version.version if self.kernel_version else ''
        pod['kernel_config'] = dict(self.kernel_config.iteritems()) if self.kernel_config else {}
        pod['sched_features'] = self.sched_features
        pod['page_size_kb'] = self.page_size_kb
        if self.os == 'android':
            pod['screen_resolution'] = self.screen_resolution
            pod['prop'] = self.prop._properties if self.prop else {}
            pod['android_id'] = self.android_id

        return pod

    @staticmethod
    def _pod_upgrade_v1(pod: Dict[str, Any]) -> Dict[str, Any]:
        pod['_pod_version'] = pod.get('_pod_version', 1)
        pod['cpus'] = pod.get('cpus', [])
        pod['system_id'] = pod.get('system_id')
        pod['hostid'] = pod.get('hostid')
        pod['hostname'] = pod.get('hostname')
        pod['sched_features'] = pod.get('sched_features')
        pod['screen_resolution'] = pod.get('screen_resolution', (0, 0))
        pod['prop'] = pod.get('prop')
        pod['android_id'] = pod.get('android_id')
        return pod

    @staticmethod
    def _pod_upgrade_v2(pod: Dict[str, Any]) -> Dict[str, Any]:
        pod['page_size_kb'] = pod.get('page_size_kb')
        pod['_pod_version'] = pod.get('format_version', 0)
        return pod

    @staticmethod
    def _pod_upgrade_v3(pod: Dict[str, Any]) -> Dict[str, Any]:
        config: Dict[str, Any] = {}
        for key, value in pod['kernel_config'].items():
            config[key.upper()] = value
        pod['kernel_config'] = config
        return pod

    @staticmethod
    def _pod_upgrade_v4(pod: Dict[str, Any]) -> Dict[str, Any]:
        return TargetInfo._pod_upgrade_v3(pod)

    @staticmethod
    def _pod_upgrade_v5(pod: Dict[str, Any]) -> Dict[str, Any]:
        pod['modules'] = pod.get('modules') or []
        return pod
