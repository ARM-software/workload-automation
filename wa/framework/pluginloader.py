#    Copyright 2013-2018 ARM Limited
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
import sys
from typing import (Optional, List, Tuple, Dict, cast, Type,
                    DefaultDict, Any)
from types import ModuleType
from wa.framework import plugin


class __LoaderWrapper(object):
    """
    wrapper around plugin loader
    """
    @property
    def kinds(self) -> List[str]:
        """
        kinds of plugins
        """
        if not self._loader:
            self.reset()
        return list(self._loader.kind_map.keys()) if self._loader else []

    @property
    def kind_map(self) -> DefaultDict[str, Dict[str, Type[plugin.Plugin]]]:
        """
        map from plugin name to the type
        """
        if not self._loader:
            self.reset()
        return self._loader.kind_map if self._loader else cast(DefaultDict, {})

    def __init__(self) -> None:
        self._loader: Optional[plugin.PluginLoader] = None

    def reset(self):
        """
        reset the plugin loader
        """
        # These imports cannot be done at top level, because of
        # sys.modules manipulation below
        # pylint: disable=import-outside-toplevel
        from wa.framework.plugin import PluginLoader
        from wa.framework.configuration.core import settings
        self._loader = PluginLoader(settings.plugin_packages,
                                    settings.plugin_paths, [])

    def update(self, packages: Optional[List[str]] = None,
               paths: Optional[List[str]] = None,
               ignore_paths: Optional[List[str]] = None) -> None:
        """
        update the internal plugins with new plugins loaded
        """
        if not self._loader:
            self.reset()
        if self._loader:
            self._loader.update(packages, paths, ignore_paths)

    def reload(self) -> None:
        """
        reload the plugins
        """
        if not self._loader:
            self.reset()
        if self._loader:
            self._loader.reload()

    def list_plugins(self, kind: Optional[str] = None) -> List[Type[plugin.Plugin]]:
        """
        List the plugins loaded
        """
        if not self._loader:
            self.reset()
        if self._loader:
            return self._loader.list_plugins(kind)
        else:
            return []

    def has_plugin(self, name: str, kind: Optional[str] = None) -> bool:
        """
        True if the plugin of the given name and kind is already loaded
        """
        if not self._loader:
            self.reset()
        if self._loader:
            return self._loader.has_plugin(name, kind)
        return False

    def get_plugin_class(self, name: str, kind: Optional[str] = None) -> Type[plugin.Plugin]:
        """
        get the class type of the plugin
        """
        if not self._loader:
            self.reset()
        if self._loader:
            return self._loader.get_plugin_class(name, kind)
        else:
            return plugin.Plugin  # dummy to satisfy type checker.

    def get_plugin(self, name: Optional[str] = None,
                   kind: Optional[str] = None, *args, **kwargs) -> Optional[plugin.Plugin]:  # pylint: disable=keyword-arg-before-vararg
        """
        get plugin of the specified name
        """
        if not self._loader:
            self.reset()
        if self._loader:
            return self._loader.get_plugin(name, kind, *args, **kwargs)
        return None

    def get_default_config(self, name: str) -> Optional[Dict[str, Any]]:
        """
        get default configuration
        """
        if not self._loader:
            self.reset()
        if self._loader:
            return self._loader.get_default_config(name)
        return None

    def resolve_alias(self, name: str) -> Tuple[str, Dict]:
        """
        resolve Alias of the plugin
        """
        if not self._loader:
            self.reset()
        if self._loader:
            return self._loader.resolve_alias(name)
        else:
            return ('', {})  # dummy to satisfy type checker

    def __getattr__(self, name: str) -> Any:
        """
        get attribute with the specified name
        """
        if not self._loader:
            self.reset()
        return getattr(self._loader, name)


sys.modules[__name__] = cast(ModuleType, __LoaderWrapper())
