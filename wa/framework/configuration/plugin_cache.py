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

from copy import copy
from collections import defaultdict
from itertools import chain

from devlib.utils.misc import memoized

from wa.framework import pluginloader
from wa.framework.configuration.core import get_config_point_map
from wa.framework.exception import ConfigError, NotFoundError
from wa.framework.target.descriptor import list_target_descriptions
from wa.utils.types import obj_dict, caseless_string
from typing import (TYPE_CHECKING, Dict, cast, Optional, List, Any,
                    DefaultDict, Set, Tuple, Type)
from types import ModuleType
from wa.framework.configuration.tree import JobSpecSource
if TYPE_CHECKING:
    from wa.framework.configuration.core import ConfigurationPoint, Configuration
    from wa.framework.pluginloader import __LoaderWrapper
    from wa.framework.target.descriptor import TargetDescriptionProtocol
    from wa.framework.plugin import Plugin

GENERIC_CONFIGS: List[str] = ["device_config", "workload_parameters",
                              "boot_parameters", "runtime_parameters"]


class PluginCache(object):
    """
    The plugin cache is used to store configuration that cannot be processed at
    this stage, whether thats because it is unknown if its needed
    (in the case of disabled plug-ins) or it is not know what it belongs to (in
    the case of "device-config" ect.). It also maintains where configuration came
    from, and the priority order of said sources.
    """

    def __init__(self, loader: ModuleType = pluginloader):
        self.loader = cast('__LoaderWrapper', loader)
        self.sources: List[JobSpecSource] = []
        self.plugin_configs: Dict[str, Dict[JobSpecSource,
                                            Dict[str, Any]]] = defaultdict(lambda: defaultdict(dict))
        self.global_alias_values: DefaultDict = defaultdict(dict)
        self.targets: Dict[str, 'TargetDescriptionProtocol'] = {td.name: cast('TargetDescriptionProtocol', td)
                                                                for td in list_target_descriptions()}

        # Generate a mapping of what global aliases belong to
        self._global_alias_map: DefaultDict[str, Dict] = defaultdict(dict)
        self._list_of_global_aliases: Set[str] = set()
        for plugin in self.loader.list_plugins():
            for param in plugin.parameters:
                if param.global_alias:
                    self._global_alias_map[plugin.name or ''][param.global_alias] = param
                    self._list_of_global_aliases.add(param.global_alias)

    def add_source(self, source: JobSpecSource):
        """
        add a source to the plugin cache
        """
        if source in self.sources:
            msg: str = "Source '{}' has already been added."
            raise Exception(msg.format(source))
        self.sources.append(source)

    def add_global_alias(self, alias: str, value: Dict[str, Any], source: JobSpecSource) -> None:
        """
        add global alias to a source
        Typically, values for plugin parameters are specified name spaced under
        the plugin's name in the configuration. A global alias is an alias that
        may be specified at the top level in configuration.

        There two common reasons for this. First, several plugins might
        specify the same global alias for the same parameter, thus allowing all
        of them to be configured with one settings. Second, a plugin may not be
        exposed directly to the user (e.g. resource getters) so it makes more
        sense to treat its parameters as global configuration values.
        """
        if source not in self.sources:
            msg: str = "Source '{}' has not been added to the plugin cache."
            raise RuntimeError(msg.format(source))

        if not self.is_global_alias(alias):
            msg = "'{} is not a valid global alias'"
            raise RuntimeError(msg.format(alias))

        self.global_alias_values[alias][source] = value

    def add_configs(self, plugin_name: str, values: Dict[str, Any], source: JobSpecSource) -> None:
        """
        add configurations to the plugin
        """
        if self.is_global_alias(plugin_name):
            self.add_global_alias(plugin_name, values, source)
            return

        if source not in self.sources:
            msg: str = "Source '{}' has not been added to the plugin cache."
            raise RuntimeError(msg.format(source))

        if caseless_string(plugin_name) in ['global', 'config']:
            msg = '"{}" entry specified inside config/global section; If this is ' \
                  'defined in a config file, move the entry content into the top level'
            raise ConfigError(msg.format((plugin_name)))

        if (not self.loader.has_plugin(plugin_name)
                and plugin_name not in self.targets
                and plugin_name not in GENERIC_CONFIGS):
            msg = 'configuration provided for unknown plugin "{}"'
            raise ConfigError(msg.format(plugin_name))

        if not hasattr(values, 'items'):
            msg = 'Plugin configuration for "{}" not a dictionary ({} is {})'
            raise ConfigError(msg.format(plugin_name, repr(values), type(values)))

        for name, value in values.items():
            if (plugin_name not in GENERIC_CONFIGS
                    and name not in self.get_plugin_parameters(plugin_name)):
                msg = "'{}' is not a valid parameter for '{}'"
                raise ConfigError(msg.format(name, plugin_name))

            self.plugin_configs[plugin_name][source][name] = value

    def is_global_alias(self, name: str) -> bool:
        """
        check whether the provided name is in the list of global aliases
        """
        return name in self._list_of_global_aliases

    def list_plugins(self, kind: Optional[str] = None) -> List[Type['Plugin']]:
        """
        List plugins in the plugin cache
        """
        return self.loader.list_plugins(kind)

    def get_plugin_config(self, plugin_name: str, generic_name: Optional[str] = None,
                          is_final: bool = True) -> obj_dict:
        """
        get the plugin configuration
        """
        config = obj_dict(not_in_dict=['name'])
        config.name = plugin_name

        if plugin_name not in GENERIC_CONFIGS:
            self._set_plugin_defaults(plugin_name, config)
            self._set_from_global_aliases(plugin_name, config)

        if generic_name is None:
            # Perform a simple merge with the order of sources representing
            # priority
            plugin_config: Dict[JobSpecSource, Dict[str, Any]] = self.plugin_configs[plugin_name]
            cfg_points: Dict[str, 'ConfigurationPoint'] = self.get_plugin_parameters(plugin_name)
            for source in self.sources:
                if source not in plugin_config:
                    continue
                for name, value in plugin_config[source].items():
                    cfg_points[name].set_value(config, value=value)
        else:
            # A more complicated merge that involves priority of sources and
            # specificity
            self._merge_using_priority_specificity(plugin_name, generic_name,
                                                   config, is_final)

        return config

    def get_plugin(self, name: str, kind: Optional[str] = None,
                   *args, **kwargs) -> Optional['Plugin']:
        """
        get plugin from plugin cache
        """
        config: obj_dict = self.get_plugin_config(name)
        kwargs = dict(list(config.items()) + list(kwargs.items()))
        return self.loader.get_plugin(name, kind, *args, **kwargs)

    def get_plugin_class(self, name: str, kind: Optional[str] = None) -> Type['Plugin']:
        return self.loader.get_plugin_class(name, kind)

    @memoized
    def get_plugin_parameters(self, name: str) -> Dict[str, 'ConfigurationPoint']:
        """
        get the plugin parameters
        """
        if name in self.targets:
            return self._get_target_params(name)
        params: List[ConfigurationPoint] = self.loader.get_plugin_class(name).parameters
        return get_config_point_map(params)

    def resolve_alias(self, name: str) -> Tuple[str, Dict]:
        """
        resolve the name aliases
        """
        return self.loader.resolve_alias(name)

    def _set_plugin_defaults(self, plugin_name: str, config: obj_dict) -> None:
        """
        set the defaults for the plugin
        """
        cfg_points: Dict[str, 'ConfigurationPoint'] = self.get_plugin_parameters(plugin_name)
        for cfg_point in cfg_points.values():
            cfg_point.set_value(config, check_mandatory=False)

        try:
            _, alias_params = self.resolve_alias(plugin_name)
            for name, value in alias_params.items():
                cfg_points[name].set_value(config, value)
        except NotFoundError:
            pass

    def _set_from_global_aliases(self, plugin_name: str, config: obj_dict) -> None:
        """
        set configuration parameter values based on global alias values
        """
        for alias, param in self._global_alias_map[plugin_name].items():
            if alias in self.global_alias_values:
                for source in self.sources:
                    if source not in self.global_alias_values[alias]:
                        continue
                    val = self.global_alias_values[alias][source]
                    param.set_value(config, value=val)

    def _get_target_params(self, name: str) -> Dict[str, 'ConfigurationPoint']:
        """
        get the target parameters
        """
        td: 'TargetDescriptionProtocol' = cast('TargetDescriptionProtocol', self.targets[name])
        return get_config_point_map(list(chain(td.target_params, td.platform_params, td.conn_params, td.assistant_params)))

    # pylint: disable=too-many-nested-blocks, too-many-branches
    def _merge_using_priority_specificity(self, specific_name: str,
                                          generic_name: str, merged_config: obj_dict,
                                          is_final: bool = True) -> None:
        """
        WA configuration can come from various sources of increasing priority,
        as well as being specified in a generic and specific manner (e.g
        ``device_config`` and ``nexus10`` respectivly). WA has two rules for
        the priority of configuration:

            - Configuration from higher priority sources overrides
              configuration from lower priority sources.
            - More specific configuration overrides less specific configuration.

        There is a situation where these two rules come into conflict. When a
        generic configuration is given in config source of high priority and a
        specific configuration is given in a config source of lower priority.
        In this situation it is not possible to know the end users intention
        and WA will error.

        :param specific_name: The name of the specific configuration used
                              e.g ``nexus10``
        :param generic_name: The name of the generic configuration
                             e.g ``device_config``
        :param merge_config: A dict of ``ConfigurationPoint``s to be used when
                             merging configuration.  keys=config point name,
                             values=config point
        :param is_final: if ``True`` (the default) make sure that mandatory
                         parameters are set.

        :rtype: A fully merged and validated configuration in the form of a
                obj_dict.
        """
        ms = MergeState()
        ms.generic_name = generic_name
        ms.specific_name = specific_name
        ms.generic_config = copy(self.plugin_configs[generic_name])
        ms.specific_config = copy(self.plugin_configs[specific_name])
        ms.cfg_points = self.get_plugin_parameters(specific_name)
        sources = self.sources

        # set_value uses the 'name' attribute of the passed object in it error
        # messages, to ensure these messages make sense the name will have to be
        # changed several times during this function.
        merged_config.name = specific_name

        for source in sources:
            try:
                update_config_from_source(merged_config, source, ms)
            except ConfigError as e:
                raise ConfigError('Error in "{}":\n\t{}'.format(source, str(e)))

        # Validate final configuration
        merged_config.name = specific_name
        if ms.cfg_points:
            for cfg_point in ms.cfg_points.values():
                cfg_point.validate(cast('Configuration', merged_config), check_mandatory=is_final)

    def __getattr__(self, name):
        """
        This resolves methods for specific plugins types based on corresponding
        generic plugin methods. So it's possible to say things like ::

            loader.get_device('foo')

        instead of ::

            loader.get_plugin('foo', kind='device')

        """
        error_msg = 'No plugins of type "{}" discovered'
        if name.startswith('get_'):
            name = name.replace('get_', '', 1)
            if name in self.loader.kind_map:
                def __wrapper(pname, *args, **kwargs):
                    return self.get_plugin(pname, name, *args, **kwargs)
                return __wrapper
            raise NotFoundError(error_msg.format(name))
        if name.startswith('list_'):
            name = name.replace('list_', '', 1).rstrip('s')
            if name in self.loader.kind_map:
                def __list_plugins_wrapper(*args, **kwargs):  # pylint: disable=E0102
                    return self.list_plugins(name, *args, **kwargs)
                return __list_plugins_wrapper
            raise NotFoundError(error_msg.format(name))
        if name.startswith('has_'):
            name = name.replace('has_', '', 1)
            if name in self.loader.kind_map:
                def __has_plugin_wrapper(pname, *args, **kwargs):  # pylint: disable=E0102
                    return self.loader.has_plugin(pname, name, *args, **kwargs)
                return __has_plugin_wrapper
            raise NotFoundError(error_msg.format(name))
        raise AttributeError(name)


class MergeState(object):
    """
    merge configurations based on priority specificity
    """
    def __init__(self) -> None:
        self.generic_name: Optional[str] = None
        self.specific_name: Optional[str] = None
        self.generic_config: Optional[Dict[JobSpecSource, Dict[str, Any]]] = None
        self.specific_config: Optional[Dict[JobSpecSource, Dict[str, Any]]] = None
        self.cfg_points: Optional[Dict[str, 'ConfigurationPoint']] = None
        self.seen_specific_config: DefaultDict[str, List[str]] = defaultdict(list)


def update_config_from_source(final_config: obj_dict, source: JobSpecSource,
                              state: MergeState) -> None:
    """
    update configuration from source and merge based on priority specificity
    """
    if state.generic_config and source in state.generic_config:
        final_config.name = state.generic_name
        if state.cfg_points:
            for name, cfg_point in state.cfg_points.items():
                if name in state.generic_config[source]:
                    if name in state.seen_specific_config:
                        msg: str = ('"{generic_name}" configuration "{config_name}" has '
                                    'already been specified more specifically for '
                                    '{specific_name} in:\n\t\t{sources}')
                        seen_sources: List[str] = state.seen_specific_config[name]
                        msg = msg.format(generic_name=state.generic_name,
                                         config_name=name,
                                         specific_name=state.specific_name,
                                         sources=", ".join(seen_sources))
                        raise ConfigError(msg)
                    value = state.generic_config[source].pop(name)
                    cfg_point.set_value(final_config, value, check_mandatory=False)

        if state.generic_config[source]:
            msg = 'Unexpected values for {}: {}'
            raise ConfigError(msg.format(state.generic_name,
                                         state.generic_config[source]))

    if state.specific_config and source in state.specific_config:
        final_config.name = state.specific_name
        if state.cfg_points:
            for name, cfg_point in state.cfg_points.items():
                if name in state.specific_config[source]:
                    state.seen_specific_config[name].append(str(source))
                    value = state.specific_config[source].pop(name)
                    cfg_point.set_value(final_config, value, check_mandatory=False)

        if state.specific_config[source]:
            msg = 'Unexpected values for {}: {}'
            raise ConfigError(msg.format(state.specific_name,
                                         state.specific_config[source]))
