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
import re
from abc import ABC, abstractmethod
from copy import deepcopy
from functools import reduce  # pylint: disable=redefined-builtin
from math import inf

from devlib.utils.types import identifier

from wa.framework.configuration.core import JobSpec
from wa.framework.exception import ConfigError
from wa.utils import log
from wa.utils.serializer import json, read_pod, SerializerSyntaxError
from wa.utils.types import toggle_set, counter, sweep
from wa.utils.misc import merge_config_values, isiterable


logger = logging.getLogger('config')


class ConfigParser(object):

    def load_from_path(self, state, filepath):
        raw, includes = _load_file(filepath, "Config")
        self.load(state, raw, filepath)
        return includes

    def load(self, state, raw, source, wrap_exceptions=True):  # pylint: disable=too-many-branches
        logger.debug('Parsing config from "{}"'.format(source))
        log.indent()
        try:
            state.plugin_cache.add_source(source)
            if 'run_name' in raw:
                msg = '"run_name" can only be specified in the config '\
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
                state.plugin_cache.add_configs(identifier(name), values, source)

        except ConfigError as e:
            if wrap_exceptions:
                raise ConfigError('Error in "{}":\n{}'.format(source, str(e)))
            else:
                raise e
        finally:
            log.dedent()


class AgendaParser(object):

    def load_from_path(self, state, filepath):
        raw, includes = _load_file(filepath, 'Agenda')
        self.load(state, raw, filepath)
        return includes

    def load(self, state, raw, source):
        logger.debug('Parsing agenda from "{}"'.format(source))
        log.indent()
        try:
            if not isinstance(raw, dict):
                raise ConfigError('Invalid agenda, top level entry must be a dict')

            sections = self._pop_sections(raw)
            global_workloads = self._pop_workloads(raw)
            if not global_workloads:
                msg = 'No jobs avaliable. Please ensure you have specified at '\
                      'least one workload to run.'
                raise ConfigError(msg)

            sect_ids, wkl_ids = self._collect_ids(sections, global_workloads)
            self._populate_and_validate_config(state, raw, source, sect_ids)

            if raw:
                msg = 'Invalid top level agenda entry(ies): "{}"'
                raise ConfigError(msg.format('", "'.join(list(raw.keys()))))

            self._process_global_workloads(state, global_workloads, wkl_ids)
            self._process_sections(state, sections, sect_ids, wkl_ids)

            state.agenda = source

        except (ConfigError, SerializerSyntaxError) as e:
            raise ConfigError('Error in "{}":\n\t{}'.format(source, str(e)))
        finally:
            log.dedent()

    def _populate_and_validate_config(self, state, raw, source, sect_ids):
        for name in ['config', 'global']:
            entry = raw.pop(name, None)
            if entry is None:
                continue

            if not isinstance(entry, dict):
                msg = 'Invalid entry "{}" - must be a dict'
                raise ConfigError(msg.format(name))

            # Want to take this entry and add any sweeps in a section
            self._extract_global_sweeps(state, entry, sect_ids)

            if 'run_name' in entry:
                value = entry.pop('run_name')
                logger.debug('Setting run name to "{}"'.format(value))
                state.run_config.set('run_name', value)

            state.load_config(entry, '{}/{}'.format(source, name))

    def _pop_sections(self, raw):
        sections = raw.pop("sections", [])
        if not isinstance(sections, list):
            raise ConfigError('Invalid entry "sections" - must be a list')
        for section in sections:
            if not hasattr(section, 'items'):
                raise ConfigError('Invalid section "{}" - must be a dict'.format(section))
        return sections

    def _pop_workloads(self, raw):
        workloads = raw.pop("workloads", [])
        if not isinstance(workloads, list):
            raise ConfigError('Invalid entry "workloads" - must be a list')
        return workloads

    def _collect_ids(self, sections, global_workloads):
        seen_section_ids = set()
        seen_workload_ids = set()

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

    def _process_global_workloads(self, state, global_workloads, seen_wkl_ids):
        for workload_entry in global_workloads:
            find_sweeps(workload_entry, convert=True) # Replace sweep text with sweep type
            workload = _process_workload_entry(workload_entry, seen_wkl_ids,
                                               state.jobs_config)
            state.jobs_config.add_workload(workload)

    def _process_sections(self, state, sections, seen_sect_ids, seen_wkl_ids):
        for section in sections:
            find_sweeps(section, convert=True)  # Replace sweep text with sweep type
            workloads = []
            for workload_entry in section.pop("workloads", []):
                workload = _process_workload_entry(workload_entry, seen_wkl_ids,
                                                   state.jobs_config)
                workloads.append(workload)

            if 'params' in section:
                if 'runtime_params' in section:
                    msg = 'both "params" and "runtime_params" specified in a '\
                          'section: "{}"'
                    raise ConfigError(msg.format(json.dumps(section, indent=None)))
                section['runtime_params'] = section.pop('params')

            group = section.pop('group', None)
            section = _construct_valid_entry(section, seen_sect_ids,
                                             "s", state.jobs_config)
            state.jobs_config.add_section(section, workloads, group)

    def _extract_global_sweeps(self, state, entry, seen_sect_ids):
        # Find any sweeps in global config
        # If there are any sweeps, add them as config inside a new section
        sweep_keychains = find_sweeps(entry, convert=True)

        extracted_config = {}
        for keychain in sweep_keychains:
            # For each sweep found
            structure = entry
            for key in keychain[:-1]:
                structure = structure[key]
            # Pop the sweep
            sweep = structure.pop(keychain[-1])

            # Add the sweep location to the new config
            dictn = extracted_config
            for key in keychain[:-1]:
                dictn = dictn.setdefault(key, {})
            dictn[keychain[-1]] = sweep

        if extracted_config:
            # Ensure unique name
            id_ctr = counter('global_sweeps')
            extracted_config['id'] = 'global_sweeps{}'.format(
                '' if id_ctr == 1 else '_{}'.format(id_ctr)
            )
            grp_ctr = counter('global_sweeps')
            group = 'global_sweeps{}'.format(
                '' if grp_ctr == 1 else '_{}'.format(grp_ctr)
            )

            glbl_sweeps = _construct_valid_entry(
                                                 extracted_config,
                                                 seen_sect_ids,
                                                 None,
                                                 state.jobs_config
                                                 )
            state.jobs_config.add_section(glbl_sweeps, [], group)

########################
### Helper functions ###
########################

def pop_aliased_param(cfg_point, d, default=None):
    """
    Given a ConfigurationPoint and a dict, this function will search the dict for
    the ConfigurationPoint's name/aliases. If more than one is found it will raise
    a ConfigError. If one (and only one) is found then it will return the value
    for the ConfigurationPoint. If the name or aliases are present in the dict it will
    return the "default" parameter of this function.
    """
    aliases = [cfg_point.name] + cfg_point.aliases
    alias_map = [a for a in aliases if a in d]
    if len(alias_map) > 1:
        raise ConfigError('Duplicate entry: {}'.format(aliases))
    elif alias_map:
        return d.pop(alias_map[0])
    else:
        return default


def _load_file(filepath, error_name):
    if not os.path.isfile(filepath):
        raise ValueError("{} does not exist".format(filepath))
    try:
        raw = read_pod(filepath)
        includes = _process_includes(raw, filepath, error_name)
    except SerializerSyntaxError as e:
        raise ConfigError('Error parsing {} {}: {}'.format(error_name, filepath, e))
    if not isinstance(raw, dict):
        message = '{} does not contain a valid {} structure; top level must be a dict.'
        raise ConfigError(message.format(filepath, error_name))
    return raw, includes


def _config_values_from_includes(filepath, include_path, error_name):
    source_dir = os.path.dirname(filepath)
    included_files = []

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


def _process_includes(raw, filepath, error_name):
    if not raw:
        return []

    included_files = []
    replace_value = None

    if hasattr(raw, 'items'):
        for key, value in raw.items():
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


def merge_augmentations(raw):
    """
    Since, from configuration perspective, output processors and instruments are
    handled identically, the configuration entries are now interchangeable. E.g. it is
    now valid to specify a output processor in an instruments list. This is to make things
    easier for the users, as, from their perspective, the distinction is somewhat arbitrary.

    For backwards compatibility, both entries are still valid, and this
    function merges them together into a single "augmentations" set, ensuring
    that there are no conflicts between the entries.

    """
    cfg_point = JobSpec.configuration['augmentations']
    names = [cfg_point.name, ] + cfg_point.aliases

    entries = []
    for n in names:
        if n not in raw:
            continue
        value = raw.pop(n)
        try:
            entries.append(toggle_set(value))
        except TypeError as exc:
            msg = 'Invalid value "{}" for "{}": {}'
            raise ConfigError(msg.format(value, n, exc))

    # Make sure none of the specified aliases conflict with each other
    to_check = list(entries)
    while len(to_check) > 1:
        check_entry = to_check.pop()
        for e in to_check:
            conflicts = check_entry.conflicts_with(e)
            if conflicts:
                msg = '"{}" and "{}" have conflicting entries: {}'
                conflict_string = ', '.join('"{}"'.format(c.strip("~"))
                                            for c in conflicts)
                raise ConfigError(msg.format(check_entry, e, conflict_string))

    if entries:
        raw['augmentations'] = reduce(lambda x, y: x.union(y), entries)


def _pop_aliased(d, names, entry_id):
    name_count = sum(1 for n in names if n in d)
    if name_count > 1:
        names_list = ', '.join(names)
        msg = 'Invalid workload entry "{}": at most one of ({}}) must be specified.'
        raise ConfigError(msg.format(entry_id, names_list))
    for name in names:
        if name in d:
            return d.pop(name)
    return None


def _construct_valid_entry(raw, seen_ids, prefix, jobs_config):
    workload_entry = {}

    # Generate an automatic ID if the entry doesn't already have one
    if 'id' not in raw:
        while True:
            new_id = '{}{}'.format(prefix, counter(name=prefix))
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
        value = pop_aliased_param(cfg_point, raw)
        if value is not None:
            if isinstance(value, sweep) and not value.auto:
                # If values have already been specified, check the kind
                value = sweep(values=map(cfg_point.kind, value))
            else:
                value = cfg_point.kind(value)
            cfg_point.validate_value(name, value)
            workload_entry[name] = value

    if "augmentations" in workload_entry:
        if '~~' in workload_entry['augmentations']:
            msg = '"~~" can only be specfied in top-level config, and not for individual workloads/sections'
            raise ConfigError(msg)
        jobs_config.update_augmentations(workload_entry['augmentations'])

    # error if there are unknown workload_entry
    if raw:
        msg = 'Invalid entry(ies) in "{}": "{}"'
        raise ConfigError(msg.format(workload_entry['id'], ', '.join(list(raw.keys()))))

    return workload_entry


def _collect_valid_id(entry_id, seen_ids, entry_type):
    if entry_id is None:
        return
    entry_id = str(entry_id)
    if entry_id in seen_ids:
        raise ConfigError('Duplicate {} ID "{}".'.format(entry_type, entry_id))
    # "-" is reserved for joining section and workload IDs
    if "-" in entry_id:
        msg = 'Invalid {} ID "{}"; IDs cannot contain a "-"'
        raise ConfigError(msg.format(entry_type, entry_id))
    if entry_id == "global":
        msg = 'Invalid {} ID "global"; is a reserved ID'
        raise ConfigError(msg.format(entry_type))
    seen_ids.add(entry_id)


def _get_workload_entry(workload):
    if isinstance(workload, str):
        workload = {'name': workload}
    elif not isinstance(workload, dict):
        raise ConfigError('Invalid workload entry: "{}"')
    return workload


def _process_workload_entry(workload, seen_workload_ids, jobs_config):
    workload = _get_workload_entry(workload)
    workload = _construct_valid_entry(workload, seen_workload_ids,
                                      "wk", jobs_config)
    if "workload_name" not in workload:
        raise ConfigError('No workload name specified in entry {}'.format(workload['id']))
    return workload


def find_sweeps(raw, convert=False):
    keychain = []
    if isinstance(raw, dict):
        to_convert = {}
        for k, v in raw.items():
            if _is_sweep(k):
                if convert:
                    sweep = _create_sweep(_sweep_handler_name(k), raw.get(k))
                    to_convert[k] = sweep
                    keychain.append((sweep.param_name, ))
                else:
                    keychain.append((k,))
            elif isinstance(v, dict) or isinstance(v, list):
                subkeys = find_sweeps(v, convert=convert)
                keychain.extend(map(lambda subkey: (k,) + subkey, subkeys))

        for k, sweep in to_convert.items():
            raw[sweep.param_name] = sweep
            raw.pop(k)

    elif isinstance(raw, list):
        for index, v in enumerate(raw):
            if not isinstance(v, dict):
                continue
            subkeys = find_sweeps(v, convert=convert)
            keychain.extend(map(lambda subkey: (index,) + subkey, subkeys))

    return keychain


def _is_sweep(name):
    return name[:6] == 'sweep(' and name[-1] == ')'


def _sweep_handler_name(name):
    return name[6:-1]


range_syntax = r'([0-9]+-[0-9]+)(,[0-9]+)?'


def _create_sweep(handler_name, raw_definition):
    try:
        handler_kind = _sweep_handlers[handler_name]
    except KeyError:
        msg = '{} is not a valid sweep handler'
        raise ConfigError(msg.format(handler_name))
    else:
        return sweep(handler=handler_kind(raw_definition))


class SweepHandler(ABC):
    '''
    Handles any functionality required for a sweep
    '''
    auto = False
    def __init__(self, raw_value: dict):
        self.raw = deepcopy(raw_value)
        self.plugin = None
        self.param_name = None
        self.values = None
        self.parse()

    @abstractmethod
    def parse(self):
        """
        Extract all information required from ``self.raw``, the
        value associated with the sweep key in the config
        """
        pass


class RangeHandler(SweepHandler):

    def parse(self):
        # Only require a param name and values
        # Other arguments ignored
        if not len(self.raw) == 1:
            msg = 'Too many entries for range sweep'
            raise ConfigError(msg)

        self.param_name, vals = tuple(self.raw.items())[0]
        if isinstance(vals, list):
            self.values = vals
            if not self.values:
                msg = 'At least 1 value must be specified in list for range '\
                      'sweep {}'
                raise ConfigError(msg.format(self.param_name))
        elif isinstance(vals, str):
            vals = ''.join(vals.split())
            match = re.match(range_syntax, vals)
            if match:
                start, stop = match[1].split('-')
                step = match[2][1:] if match[2] else 1
                start, stop, step = int(start), int(stop), int(step)
                self.values = list(range(start, stop, step))
            else:
                msg = 'Invalid range sweep format for param {}'
                raise ConfigError(msg.format(self.param_name))
        else:
            msg = 'Invalid range sweep format for param {}'
            raise ConfigError(msg.format(self.param_name))


class AutoSweepHandler(SweepHandler):

    auto = True

    def __init__(self, raw_value):
        self.min = None
        self.max = None
        super().__init__(raw_value)

    def parse(self):
        # This ``parse`` method, if called, must be called *after* any child
        # parse methods that pop from raw, as it assumes that raw should be
        # empty by the end
        if self.raw:
            try:
                min = self.raw.pop('min', None)
                max = self.raw.pop('max', None)
                if min is not None:
                    self.min = float(min)
                if max is not None:
                    self.max = float(max)
            except ValueError:
                min_msg = 'minimum {} '.format(min) if min else ''
                max_msg = 'maximum {} '.format(max) if max else ''
                connective = 'and ' if min_msg and max_msg else ''
                raise ConfigError('Sweep {}{}{}must be numeric'.format(
                    min_msg, connective, max_msg
                ))
            else:
                # If either is specified, both must be
                if min and not max:
                    self.max = inf
                elif max and not min:
                    self.min = -inf

            self.param_name = self.raw.pop('param', None)
            self.plugin = self.raw.pop('plugin', None)

        if self.raw:
            msg = 'Too many arguments to sweep definition'
            raise ConfigError(msg)

    @abstractmethod
    def resolve_auto_sweep(self, tm, pc):
        """
        Convert the auto sweep found in ``self.raw`` to
        a list of values, to be stored in ``self.values``
        
        :param tm: TargetManager
        :param pc: PluginCache
        """
        pass


class FreqHandler(AutoSweepHandler):

    def parse(self):
        super().parse()
        self.param_name = self.param_name if self.param_name is not None else 'frequency'

    def resolve_auto_sweep(self, tm, pc):
        freq_cfg = tm.rpm.get_cfg_point(self.param_name)
        allowed_values = None
        if hasattr(freq_cfg, 'kind') and hasattr(freq_cfg.kind, 'values'):
            allowed_values = freq_cfg.kind.values
        elif hasattr(freq_cfg, 'allowed_values'):
            allowed_values = freq_cfg.allowed_values
        else:
            msg = 'Runtime config parameter {} can not be swept'
            raise ConfigError(msg.format(self.param_name))
        if self.min:
            self.values = list(filter(lambda x: self.min < x < self.max, allowed_values))
        else:
            self.values = allowed_values


class ParamHandler(AutoSweepHandler):
    """
    For auto sweeps of any parameter that specifies
    ``allowed_values``
    """
    def parse(self):
        super().parse()
        # Both plugin and param name must be specified
        if self.plugin is None or self.param_name is None:
            msg = 'autoparam sweeps require both the plugin ' \
                  'and parameter name to be specified'
            raise ConfigError(msg)

    def resolve_auto_sweep(self, tm, pc):
        params = pc.get_plugin_parameters(self.plugin)
        cfg_pt = params[self.param_name]
        if cfg_pt.allowed_values is None:
            msg = 'Parameter \'{}\' does not specify allowed values to sweep'
            raise ConfigError(msg.format(self.param_name))
        
        # If min is not None, then the values are numeric, and both min and max
        # will be numeric values
        if self.min is not None:
            self.values = list(filter(lambda x: self.min < x < self.max, cfg_pt.allowed_values))
        else:
            self.values = cfg_pt.allowed_values


_sweep_handlers = {
    'range': RangeHandler,
    'autofreq': FreqHandler,
    'autoparam': ParamHandler,
}
