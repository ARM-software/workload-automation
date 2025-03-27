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

from collections import namedtuple

from wa.framework.exception import ConfigError
from wa.framework.target.runtime_config import (SysfileValuesRuntimeConfig,
                                                HotplugRuntimeConfig,
                                                CpufreqRuntimeConfig,
                                                CpuidleRuntimeConfig,
                                                AndroidRuntimeConfig,
                                                RuntimeConfig)
from wa.utils.types import obj_dict, caseless_string
from wa.framework import pluginloader
from typing import TYPE_CHECKING, Dict, List, Optional, cast, Type
from wa.framework.configuration.tree import JobSpecSource
if TYPE_CHECKING:
    from wa.framework.configuration.core import ConfigurationPoint
    from devlib.target import Target
    from wa.framework.pluginloader import __LoaderWrapper


class RuntimeParameterManager(object):

    runtime_config_cls: List[Type[RuntimeConfig]] = [
        # order matters
        SysfileValuesRuntimeConfig,
        HotplugRuntimeConfig,
        CpufreqRuntimeConfig,
        CpuidleRuntimeConfig,
        AndroidRuntimeConfig,
    ]

    def __init__(self, target: 'Target'):
        self.target = target
        RuntimeParameter = namedtuple('RuntimeParameter', 'cfg_point, rt_config')
        self.runtime_params: Dict[str, RuntimeParameter] = {}

        try:
            for rt_cls in cast('__LoaderWrapper', pluginloader).list_plugins(kind='runtime-config'):
                if rt_cls not in self.runtime_config_cls:
                    self.runtime_config_cls.append(cast(Type[RuntimeConfig], rt_cls))
        except ValueError:
            pass
        self.runtime_configs: List[RuntimeConfig] = [cls(self.target) for cls in self.runtime_config_cls]

        for cfg in self.runtime_configs:
            for param in cfg.supported_parameters:
                if param.name in self.runtime_params:
                    msg: str = 'Duplicate runtime parameter name "{}": in both {} and {}'
                    raise RuntimeError(msg.format(param.name,
                                                  self.runtime_params[param.name].rt_config.name,
                                                  cfg.name))
                self.runtime_params[param.name] = RuntimeParameter(param, cfg)

    # Uses corresponding config point to merge parameters
    def merge_runtime_parameters(self, parameters: Dict[JobSpecSource, Dict[str, 'ConfigurationPoint']]) -> Dict:
        """
        merge the runtime parameters
        """
        merged_params = obj_dict()
        for source in parameters:
            for name, value in parameters[source].items():
                cp: 'ConfigurationPoint' = self.get_cfg_point(name)
                cp.set_value(merged_params, value)
        return dict(merged_params)

    # Validates runtime_parameters against each other
    def validate_runtime_parameters(self, parameters: obj_dict) -> None:
        """
        validate the runtime parameters
        """
        self.clear_runtime_parameters()
        self.set_runtime_parameters(parameters)
        for cfg in self.runtime_configs:
            cfg.validate_parameters()

    # Writes the given parameters to the device.
    def commit_runtime_parameters(self, parameters: obj_dict) -> None:
        """
        commit the runtime parameters
        """
        self.clear_runtime_parameters()
        self.set_runtime_parameters(parameters)
        for cfg in self.runtime_configs:
            cfg.commit()

    # Stores a set of parameters performing isolated validation when appropriate
    def set_runtime_parameters(self, parameters: obj_dict) -> None:
        """
        set the runtime parameters
        """
        for name, value in parameters.items():
            cfg: Optional[RuntimeConfig] = self.get_config_for_name(name)
            if cfg is None:
                msg: str = 'Unsupported runtime parameter: "{}"'
                raise ConfigError(msg.format(name))
            cfg.set_runtime_parameter(name, value)

    def clear_runtime_parameters(self) -> None:
        """
        clear runtime parameters
        """
        for cfg in self.runtime_configs:
            cfg.clear()
            cfg.set_defaults()

    def get_config_for_name(self, name: str) -> Optional[RuntimeConfig]:
        """
        get the configuration for the provided name
        """
        name = caseless_string(name)
        for k, v in self.runtime_params.items():
            if name == k:
                return v.rt_config
        return None

    def get_cfg_point(self, name: str) -> 'ConfigurationPoint':
        """
        get the configuration point
        """
        name = caseless_string(name)
        for k, v in self.runtime_params.items():
            if name == k or name in v.cfg_point.aliases:
                return v.cfg_point
        raise ConfigError('Unknown runtime parameter: {}'.format(name))
