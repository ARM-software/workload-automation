#    Copyright 2015-2018 ARM Limited
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
# pylint: disable=no-self-use

import os
import logging
from functools import reduce  # pylint: disable=redefined-builtin

from devlib.utils.types import identifier

from wa.framework.configuration.core import JobSpec
from wa.framework.exception import ConfigError
from wa.utils import log
from wa.utils.serializer import json, read_pod, SerializerSyntaxError
from wa.utils.types import toggle_set, counter, obj_dict
from wa.utils.misc import merge_config_values, isiterable
from wa.framework.configuration.tree import JobSpecSource
from typing import (TYPE_CHECKING, Dict, List, Any, cast, Union,
                    Tuple, Set, Optional)
if TYPE_CHECKING:
    from wa.framework.configuration.execution import ConfigManager, JobGenerator
    from wa.framework.configuration.core import ConfigurationPoint

logger: logging.Logger = logging.getLogger('config')


class ConfigParser(object):
    """
    Config file parser
    """
    def load_from_path(self, state: 'ConfigManager', filepath: str) -> List[str]:
        """
        Load config file from the specified path
        """
        raw, includes = _load_file(filepath, "Config")
        self.load(state, raw, filepath)
        return includes

    def load(self, state: 'ConfigManager', raw: Dict,
             source: str, wrap_exceptions: bool = True) -> None:  # pylint: disable=too-many-branches
        """
        load configuration from source file
        """
        logger.debug('Parsing config from "{}"'.format(source))
        log.indent()
        try:
            state.plugin_cache.add_source(cast(JobSpecSource, source))
            if 'run_name' in raw:
                msg: str = '"run_name" can only be specified in the config '\
                    'section of an agenda'
                raise ConfigError(msg)

            if 'id' in raw:
                raise ConfigError('"id" cannot be set globally')

            merge_augmentations(raw)

            # Get WA core configuration
            for cfg_point in state.settings.configuration.values():
                value = pop_aliased_param(cfg_point, raw)
                if value is not None:
                    logger.debug('Setting meta "{}" to "{}"'.format(cfg_point.name, value))
                    state.settings.set(cfg_point.name, value)

            # Get run specific configuration
            for cfg_point in state.run_config.configuration.values():
                value = pop_aliased_param(cfg_point, raw)
                if value is not None:
                    logger.debug('Setting run "{}" to "{}"'.format(cfg_point.name, value))
                    state.run_config.set(cfg_point.name, value)

            # Get global job spec configuration
            for cfg_point in JobSpec.configuration.values():
                value = pop_aliased_param(cfg_point, raw)
                if value is not None:
                    logger.debug('Setting global "{}" to "{}"'.format(cfg_point.name, value))
                    state.jobs_config.set_global_value(cfg_point.name, value)

            for name, values in raw.items():
                # Assume that all leftover config is for a plug-in or a global
                # alias it is up to PluginCache to assert this assumption
                logger.debug('Caching "{}" with "{}"'.format(identifier(name), values))
                state.plugin_cache.add_configs(identifier(name), values, cast(JobSpecSource, source))

        except ConfigError as e:
            if wrap_exceptions:
                raise ConfigError('Error in "{}":\n{}'.format(source, str(e)))
            else:
                raise e
        finally:
            log.dedent()


class AgendaParser(object):
    """
    Agenda Parser
    """
    def load_from_path(self, state: 'ConfigManager', filepath: str) -> List[str]:
        raw, includes = _load_file(filepath, 'Agenda')
        self.load(state, raw, filepath)
        return includes

    def load(self, state: 'ConfigManager', raw: Dict[str, List[Dict]], source: str) -> None:
        """
        load agenda from source
        """
        logger.debug('Parsing agenda from "{}"'.format(source))
        log.indent()
        try:
            if not isinstance(raw, dict):
                raise ConfigError('Invalid agenda, top level entry must be a dict')

            self._populate_and_validate_config(state, raw, source)
            sections: List[Dict] = self._pop_sections(raw)
            global_workloads: List = self._pop_workloads(raw)
            if not global_workloads:
                msg: str = 'No jobs avaliable. Please ensure you have specified at '\
                    'least one workload to run.'
                raise ConfigError(msg)

            if raw:
                msg = 'Invalid top level agenda entry(ies): "{}"'
                raise ConfigError(msg.format('", "'.join(list(raw.keys()))))

            sect_ids, wkl_ids = self._collect_ids(sections, global_workloads)
            self._process_global_workloads(state, global_workloads, wkl_ids)
            self._process_sections(state, sections, sect_ids, wkl_ids)

            state.agenda = source

        except (ConfigError, SerializerSyntaxError) as e:
            raise ConfigError('Error in "{}":\n\t{}'.format(source, str(e)))
        finally:
            log.dedent()

    def _populate_and_validate_config(self, state: 'ConfigManager',
                                      raw: Dict[str, Any], source: str) -> None:
        """
        populate the configuration and validate it
        config and global are dicts
        """
        for name in ['config', 'global']:
            entry: Optional[Dict] = raw.pop(name, None)
            if entry is None:
                continue

            if not isinstance(entry, dict):
                msg: str = 'Invalid entry "{}" - must be a dict'
                raise ConfigError(msg.format(name))

            if 'run_name' in entry:
                value = entry.pop('run_name')
                logger.debug('Setting run name to "{}"'.format(value))
                state.run_config.set('run_name', value)

            state.load_config(entry, '{}/{}'.format(source, name))

    def _pop_sections(self, raw: Dict[str, Any]) -> List[Dict]:
        """
        get sections from raw data
        sections is a List of dicts
        """
        sections: List[Dict] = raw.pop("sections", [])
        if not isinstance(sections, list):
            raise ConfigError('Invalid entry "sections" - must be a list')
        for section in sections:
            if not hasattr(section, 'items'):
                raise ConfigError('Invalid section "{}" - must be a dict'.format(section))
        return sections

    def _pop_workloads(self, raw: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        get workloads from raw data
        """
        workloads: List[Dict[str, Any]] = raw.pop("workloads", [])
        if not isinstance(workloads, list):
            raise ConfigError('Invalid entry "workloads" - must be a list')
        return workloads

    def _collect_ids(self, sections: List[Dict[str, Any]],
                     global_workloads: List[Dict[str, Any]]) -> Tuple[Set[str], Set[str]]:
        """
        collect section and workload ids and return them as a tuple of sets
        """
        seen_section_ids: Set[str] = set()
        seen_workload_ids: Set[str] = set()

        for workload in global_workloads:
            workload = _get_workload_entry(workload)
            _collect_valid_id(workload.get("id"), seen_workload_ids, "workload")

        for section in sections:
            _collect_valid_id(section.get("id"), seen_section_ids, "section")
            for workload in section["workloads"] if "workloads" in section else []:
                workload = _get_workload_entry(workload)
                _collect_valid_id(workload.get("id"), seen_workload_ids,
                                  "workload")

        return seen_section_ids, seen_workload_ids

    def _process_global_workloads(self, state: 'ConfigManager', global_workloads: List[Dict[str, Any]],
                                  seen_wkl_ids: Set[str]) -> None:
        """
        process global workload entries
        """
        for workload_entry in global_workloads:
            workload = _process_workload_entry(workload_entry, seen_wkl_ids,
                                               state.jobs_config)
            state.jobs_config.add_workload(cast(obj_dict, workload))

    def _process_sections(self, state: 'ConfigManager', sections: List[Dict[str, Any]],
                          seen_sect_ids: Set[str], seen_wkl_ids: Set[str]) -> None:
        """
        process sections in the configuration
        """
        for section in sections:
            workloads: List[Dict[str, Any]] = []
            for workload_entry in section.pop("workloads", []):
                workload = _process_workload_entry(workload_entry, seen_wkl_ids,
                                                   state.jobs_config)
                workloads.append(workload)

            if 'params' in section:
                if 'runtime_params' in section:
                    msg: str = 'both "params" and "runtime_params" specified in a '\
                        'section: "{}"'
                    raise ConfigError(msg.format(json.dumps(section, indent=None)))
                section['runtime_params'] = section.pop('params')

            group: str = section.pop('group', None)
            section = _construct_valid_entry(section, seen_sect_ids,
                                             "s", state.jobs_config)
            state.jobs_config.add_section(cast(obj_dict, section), cast(List[obj_dict], workloads), group)


########################
### Helper functions ###
########################

def pop_aliased_param(cfg_point: 'ConfigurationPoint', d: Dict[str, str], default: Any = None) -> Any:
    """
    Given a ConfigurationPoint and a dict, this function will search the dict for
    the ConfigurationPoint's name/aliases. If more than one is found it will raise
    a ConfigError. If one (and only one) is found then it will return the value
    for the ConfigurationPoint. If the name or aliases are present in the dict it will
    return the "default" parameter of this function.
    """
    aliases: List[str] = [cfg_point.name] + cfg_point.aliases
    alias_map: List[str] = [a for a in aliases if a in d]
    if len(alias_map) > 1:
        raise ConfigError('Duplicate entry: {}'.format(aliases))
    elif alias_map:
        return d.pop(alias_map[0])
    else:
        return default


def _load_file(filepath: str, error_name: str) -> Tuple[Dict[str, Any], List[str]]:
    """
    read raw data and includes information from file
    """
    if not os.path.isfile(filepath):
        raise ValueError("{} does not exist".format(filepath))
    try:
        raw: Dict[str, Any] = read_pod(filepath)
        includes: List[str] = _process_includes(raw, filepath, error_name)
    except SerializerSyntaxError as e:
        raise ConfigError('Error parsing {} {}: {}'.format(error_name, filepath, e))
    if not isinstance(raw, dict):
        message: str = '{} does not contain a valid {} structure; top level must be a dict.'
        raise ConfigError(message.format(filepath, error_name))
    return raw, includes


def _config_values_from_includes(filepath: str,
                                 include_path: Union[str, List[str]],
                                 error_name: str) -> Tuple[Dict[str, Any], List[str]]:
    """
    get the configuration values from the included files in the current configuration.
    it again calls _load_file -> _process_includes in all the subsequent includes.
    """
    source_dir: str = os.path.dirname(filepath)
    included_files: List[str] = []

    if isinstance(include_path, str):
        include_path = os.path.expanduser(os.path.join(source_dir, include_path))

        replace_value, includes = _load_file(include_path, error_name)

        included_files.append(include_path)
        included_files.extend(includes)
    elif isinstance(include_path, list):
        replace_value = {}

        for path in include_path:
            include_path = os.path.expanduser(os.path.join(source_dir, path))

            sub_replace_value, includes = _load_file(include_path, error_name)
            for key, val in sub_replace_value.items():
                replace_value[key] = merge_config_values(val, replace_value.get(key, None))

            included_files.append(include_path)
            included_files.extend(includes)
    else:
        message = "{} does not contain a valid {} structure; value for 'include#' must be a string or a list"
        raise ConfigError(message.format(filepath, error_name))

    return replace_value, included_files


def _process_includes(raw: Optional[Dict], filepath: str, error_name: str) -> List[str]:
    """
    It is possible to include other files in your config files and agendas. This is
    done by specifying ``include#`` (note the trailing hash) as a key in one of the
    mappings, with the value being the path to the file to be included. The path
    must be either absolute, or relative to the location of the file it is being
    included from (*not* to the current working directory). The path may also
    include ``~`` to indicate current user's home directory.

    The include is performed by removing the ``include#`` loading the contents of
    the specified into the mapping that contained it. In cases where the mapping
    already contains the key to be loaded, values will be merged using the usual
    merge method (for overwrites, values in the mapping take precedence over those
    from the included files).
    Some additional details about the implementation and its limitations:

    - The ``include#`` *must* be a key in a mapping, and the contents of the
    included file *must* be a mapping as well; it is not possible to include a
    list
    - Being a key in a mapping, there can only be one ``include#`` entry per block.
    - The included file *must* have a ``.yaml`` extension.
    - Nested inclusions *are* allowed. I.e. included files may themselves include
    files; in such cases the included paths must be relative to *that* file, and
    not the "main" file.
    """
    if not raw:
        return []

    included_files: List[str] = []
    replace_value: Optional[Dict[str, Any]] = None

    if hasattr(raw, 'items'):
        for key, value in cast(Dict, raw).items():
            if key == 'include#':
                replace_value, includes = _config_values_from_includes(filepath, value, error_name)
                included_files.extend(includes)
            elif hasattr(value, 'items') or isiterable(value):
                includes = _process_includes(value, filepath, error_name)
                included_files.extend(includes)
    elif isiterable(raw):
        for element in raw:
            if hasattr(element, 'items') or isiterable(element):
                includes = _process_includes(element, filepath, error_name)
                included_files.extend(includes)

    if replace_value is not None:
        del raw['include#']
        for key, value in replace_value.items():
            raw[key] = merge_config_values(value, raw.get(key, None))

    return included_files


def merge_augmentations(raw: Dict[str, Any]) -> None:
    """
    Since, from configuration perspective, output processors and instruments are
    handled identically, the configuration entries are now interchangeable. E.g. it is
    now valid to specify a output processor in an instruments list. This is to make things
    easier for the users, as, from their perspective, the distinction is somewhat arbitrary.

    For backwards compatibility, both entries are still valid, and this
    function merges them together into a single "augmentations" set, ensuring
    that there are no conflicts between the entries.

    """
    cfg_point: 'ConfigurationPoint' = JobSpec.configuration['augmentations']
    names: List[str] = [cfg_point.name, ] + cfg_point.aliases

    entries: List[toggle_set] = []
    for n in names:
        if n not in raw:
            continue
        value = raw.pop(n)
        try:
            entries.append(toggle_set(value))
        except TypeError as exc:
            msg: str = 'Invalid value "{}" for "{}": {}'
            raise ConfigError(msg.format(value, n, exc))

    # Make sure none of the specified aliases conflict with each other
    to_check: List[toggle_set] = list(entries)
    while len(to_check) > 1:
        check_entry: toggle_set = to_check.pop()
        for e in to_check:
            conflicts: List[str] = check_entry.conflicts_with(e)
            if conflicts:
                msg = '"{}" and "{}" have conflicting entries: {}'
                conflict_string = ', '.join('"{}"'.format(c.strip("~"))
                                            for c in conflicts)
                raise ConfigError(msg.format(check_entry, e, conflict_string))

    if entries:
        raw['augmentations'] = reduce(lambda x, y: cast(toggle_set, x.union(y)), entries)


def _pop_aliased(d: Dict[str, str], names: List[str], entry_id: str) -> Optional[str]:
    name_count = sum(1 for n in names if n in d)
    if name_count > 1:
        names_list = ', '.join(names)
        msg = 'Invalid workload entry "{}": at most one of ({}}) must be specified.'
        raise ConfigError(msg.format(entry_id, names_list))
    for name in names:
        if name in d:
            return d.pop(name)
    return None


def _construct_valid_entry(raw: Dict[str, Any], seen_ids: Set[str], prefix: str,
                           jobs_config: 'JobGenerator') -> Dict[str, Any]:
    workload_entry: Dict[str, Any] = {}
    """
    construct a valid workload entry from raw data read from file
    """
    # Generate an automatic ID if the entry doesn't already have one
    if 'id' not in raw:
        while True:
            new_id: str = '{}{}'.format(prefix, counter(name=prefix))
            if new_id not in seen_ids:
                break
        workload_entry['id'] = new_id
        seen_ids.add(new_id)
    else:
        workload_entry['id'] = raw.pop('id')

    # Process instruments
    merge_augmentations(raw)

    # Validate all workload_entry
    for name, cfg_point in JobSpec.configuration.items():
        value: Any = pop_aliased_param(cfg_point, raw)
        if value is not None and cfg_point.kind:
            value = cfg_point.kind(value)
            cfg_point.validate_value(name, value)
            workload_entry[name] = value

    if "augmentations" in workload_entry:
        if '~~' in workload_entry['augmentations']:
            msg: str = '"~~" can only be specfied in top-level config, and not for individual workloads/sections'
            raise ConfigError(msg)
        jobs_config.update_augmentations(workload_entry['augmentations'])

    # error if there are unknown workload_entry
    if raw:
        msg = 'Invalid entry(ies) in "{}": "{}"'
        raise ConfigError(msg.format(workload_entry['id'], ', '.join(list(raw.keys()))))

    return workload_entry


def _collect_valid_id(entry_id: Optional[Union[int, str]], seen_ids: Set[str], entry_type) -> None:
    if entry_id is None:
        return
    entry_id = str(entry_id)
    if entry_id in seen_ids:
        raise ConfigError('Duplicate {} ID "{}".'.format(entry_type, entry_id))
    # "-" is reserved for joining section and workload IDs
    if "-" in entry_id:
        msg: str = 'Invalid {} ID "{}"; IDs cannot contain a "-"'
        raise ConfigError(msg.format(entry_type, entry_id))
    if entry_id == "global":
        msg = 'Invalid {} ID "global"; is a reserved ID'
        raise ConfigError(msg.format(entry_type))
    seen_ids.add(entry_id)


def _get_workload_entry(workload: Union[Dict[str, Any], str]) -> Dict[str, Any]:
    if isinstance(workload, str):
        workload = {'name': workload}
    elif not isinstance(workload, dict):
        raise ConfigError('Invalid workload entry: "{}"')
    return workload


def _process_workload_entry(workload: Dict[str, Any], seen_workload_ids: Set[str],
                            jobs_config: 'JobGenerator') -> Dict[str, Any]:
    workload = _get_workload_entry(workload)
    workload = _construct_valid_entry(workload, seen_workload_ids,
                                      "wk", jobs_config)
    if "workload_name" not in workload:
        raise ConfigError('No workload name specified in entry {}'.format(workload['id']))
    return workload
