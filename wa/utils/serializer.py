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

"""
This module contains wrappers for Python serialization modules for
common formats that make it easier to serialize/deserialize WA
Plain Old Data structures (serilizable WA classes implement
``to_pod()``/``from_pod()`` methods for converting between POD
structures and Python class instances).

The modifications to standard serilization procedures are:

    - mappings are deserialized as ``OrderedDict`` 's rather than standard
      Python ``dict`` 's. This allows for cleaner syntax in certain parts
      of WA configuration (e.g. values to be written to files can be specified
      as a dict, and they will be written in the order specified in the config).
    - regular expressions are automatically encoded/decoded. This allows for
      configuration values to be transparently specified as strings or regexes
      in the POD config.

This module exports the "wrapped" versions of serialization libraries,
and this should be imported and used instead of importing the libraries
directly. i.e. ::

    from wa.utils.serializer import yaml
    pod = yaml.load(fh)

instead of ::

    import yaml
    pod = yaml.load(fh)

It's also possible to use the serializer directly::

    from wa.utils import serializer
    pod = serializer.load(fh)

This can also be used to ``dump()`` POD structures. By default,
``dump()`` will produce JSON, but ``fmt`` parameter may be used to
specify an alternative format (``yaml`` or ``python``). ``load()`` will
use the file plugin to guess the format, but ``fmt`` may also be used
to specify it explicitly.

"""
# pylint: disable=unused-argument

import os
import re
import json as _json
from collections import OrderedDict
from collections.abc import Hashable
from datetime import datetime
import dateutil.parser  # type:ignore
import yaml as _yaml  # pylint: disable=wrong-import-order
from yaml import MappingNode, Dumper, Node, ScalarNode
try:
    from yaml import FullLoader as _yaml_loader
except ImportError:
    from yaml import Loader as _yaml_loader
from yaml.constructor import ConstructorError  # type:ignore

from wa.framework.exception import SerializerSyntaxError
from wa.utils.misc import isiterable
from wa.utils.types import regex_type, none_type, level, cpu_mask
from typing import (Dict, Any, Callable, Optional, IO, Union,
                    List, Type, cast, Pattern)

__all__: List[str] = [
    'json',
    'yaml',
    'read_pod',
    'dump',
    'load',
    'is_pod',
    'POD_TYPES',
]

POD_TYPES: List[Type] = [
    list,
    tuple,
    dict,
    set,
    str,
    int,
    float,
    bool,
    OrderedDict,
    datetime,
    regex_type,
    none_type,
    level,
    cpu_mask,
]


class WAJSONEncoder(_json.JSONEncoder):
    """
    Json encoder for WA
    """
    def default(self, obj: Any) -> str:  # pylint: disable=method-hidden,arguments-differ
        if isinstance(obj, regex_type):
            return 'REGEX:{}:{}'.format(obj.flags, obj.pattern)
        elif isinstance(obj, datetime):
            return 'DATET:{}'.format(obj.isoformat())
        elif isinstance(obj, level):
            return 'LEVEL:{}:{}'.format(obj.name, obj.value)
        elif isinstance(obj, cpu_mask):
            return 'CPUMASK:{}'.format(obj.mask())
        else:
            return _json.JSONEncoder.default(self, obj)


class WAJSONDecoder(_json.JSONDecoder):
    """
    Json decoder for WA
    """
    def decode(self, s, **kwargs):  # pylint: disable=arguments-differ
        d = _json.JSONDecoder.decode(self, s, **kwargs)

        def try_parse_object(v: Any) -> Any:
            if isinstance(v, str):
                if v.startswith('REGEX:'):
                    _, flags, pattern = v.split(':', 2)
                    return re.compile(pattern, int(flags or 0))
                elif v.startswith('DATET:'):
                    _, pattern = v.split(':', 1)
                    return dateutil.parser.parse(pattern)
                elif v.startswith('LEVEL:'):
                    _, name, value = v.split(':', 2)
                    return level(name, value)
                elif v.startswith('CPUMASK:'):
                    _, value = v.split(':', 1)
                    return cpu_mask(value)

            return v

        def load_objects(d: Dict) -> Union[Dict, OrderedDict]:
            if not hasattr(d, 'items'):
                return d
            pairs: List = []
            for k, v in d.items():
                if hasattr(v, 'items'):
                    pairs.append((k, load_objects(v)))
                elif isiterable(v):
                    pairs.append((k, [try_parse_object(i) for i in v]))
                else:
                    pairs.append((k, try_parse_object(v)))
            return OrderedDict(pairs)

        return load_objects(d)


class json(object):

    @staticmethod
    def dump(o: Any, wfh: IO, indent: int = 4, *args, **kwargs) -> None:
        """
        serialize o as json formatted stream to wfh
        """
        return _json.dump(o, wfh, cls=WAJSONEncoder, indent=indent, *args, **kwargs)

    @staticmethod
    def dumps(o: Any, indent: Optional[int] = 4, *args, **kwargs) -> str:
        """
        serialize o to json formatted string
        """
        return _json.dumps(o, cls=WAJSONEncoder, indent=indent, *args, **kwargs)

    @staticmethod
    def load(fh: IO, *args, **kwargs) -> Any:
        """
        deserialize json from file
        """
        try:
            return _json.load(fh, cls=WAJSONDecoder, object_pairs_hook=OrderedDict, *args, **kwargs)
        except ValueError as e:
            raise SerializerSyntaxError(e.args[0])

    @staticmethod
    def loads(s: str, *args, **kwargs) -> Any:
        """
        deserialize json string to python object
        """
        try:
            return _json.loads(s, cls=WAJSONDecoder, object_pairs_hook=OrderedDict, *args, **kwargs)
        except ValueError as e:
            raise SerializerSyntaxError(e.args[0])


_mapping_tag: str = _yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG
_regex_tag: str = 'tag:wa:regex'
_level_tag: str = 'tag:wa:level'
_cpu_mask_tag: str = 'tag:wa:cpu_mask'


def _wa_dict_representer(dumper: Dumper, data: OrderedDict) -> Any:
    """
    represent ordered dict in dumped json
    """
    return dumper.represent_mapping(_mapping_tag, iter(data.items()))


def _wa_regex_representer(dumper: Dumper, data: re.Pattern) -> Any:
    """
    represent regex in dumped json
    """
    text: str = '{}:{}'.format(data.flags, data.pattern)
    return dumper.represent_scalar(_regex_tag, text)


def _wa_level_representer(dumper: Dumper, data: level) -> Any:
    """
    represent level in dumped json
    """
    text = '{}:{}'.format(data.name, data.level)  # type: ignore
    return dumper.represent_scalar(_level_tag, text)


def _wa_cpu_mask_representer(dumper: Dumper, data: cpu_mask) -> Any:
    """
    represent cpu mask in dumped json
    """
    return dumper.represent_scalar(_cpu_mask_tag, data.mask())


def _wa_regex_constructor(loader: _yaml_loader, node: Node) -> Pattern[str]:
    """
    regex constructor
    """
    value: str = cast(str, loader.construct_scalar(cast(ScalarNode, node)))
    flags, pattern = value.split(':', 1)
    return re.compile(pattern, int(flags or 0))


def _wa_level_constructor(loader: _yaml_loader, node: Node) -> level:
    """
    level constructor
    """
    value = loader.construct_scalar(cast(ScalarNode, node))
    name, value = cast(str, value).split(':', 1)
    return level(name, value)


def _wa_cpu_mask_constructor(loader: _yaml_loader, node: Node) -> cpu_mask:
    value = cast(str, loader.construct_scalar(cast(ScalarNode, node)))
    return cpu_mask(value)


class _WaYamlLoader(_yaml_loader):  # pylint: disable=too-many-ancestors
    """
    yaml loader for WA
    """

    def construct_mapping(self, node: Type[Node], deep: bool = False) -> OrderedDict:
        """
        construct mapping
        """
        if isinstance(node, MappingNode):
            self.flatten_mapping(node)
        if not isinstance(node, MappingNode):
            raise ConstructorError(None, None,
                                   "expected a mapping node, but found %s" % node.id,  # type:ignore
                                   node.start_mark)
        mapping = OrderedDict()
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, Hashable):
                raise ConstructorError("while constructing a mapping", node.start_mark,
                                       "found unhashable key", key_node.start_mark)
            value = self.construct_object(value_node, deep=deep)
            mapping[key] = value
        return mapping


_yaml.add_representer(OrderedDict, _wa_dict_representer)
_yaml.add_representer(regex_type, _wa_regex_representer)
_yaml.add_representer(level, _wa_level_representer)
_yaml.add_representer(cpu_mask, _wa_cpu_mask_representer)
_yaml.add_constructor(_regex_tag, _wa_regex_constructor, Loader=_WaYamlLoader)
_yaml.add_constructor(_level_tag, _wa_level_constructor, Loader=_WaYamlLoader)
_yaml.add_constructor(_cpu_mask_tag, _wa_cpu_mask_constructor, Loader=_WaYamlLoader)
_yaml.add_constructor(_mapping_tag, _WaYamlLoader.construct_yaml_map, Loader=_WaYamlLoader)


class yaml(object):

    @staticmethod
    def dump(o: Any, wfh: IO, *args, **kwargs) -> None:
        """
        serialize object into yaml format and dump into file
        """
        return _yaml.dump(o, wfh, *args, **kwargs)

    @staticmethod
    def load(fh: IO, *args, **kwargs) -> Any:
        """
        deserialize yaml from file and create python object
        """
        try:
            return _yaml.load(fh, *args, Loader=_WaYamlLoader, **kwargs)
        except _yaml.YAMLError as e:
            lineno = None
            if hasattr(e, 'problem_mark'):
                lineno = e.problem_mark.line  # pylint: disable=no-member
            message = e.args[0] if (e.args and e.args[0]) else str(e)
            raise SerializerSyntaxError(message, lineno)

    loads = load


class python(object):

    @staticmethod
    def dump(o: Any, wfh: IO, *args, **kwargs):
        """
        serialize object and dump into file
        """
        raise NotImplementedError()

    @classmethod
    def load(cls: Type, fh: IO, *args, **kwargs) -> Dict[str, Any]:
        """
        load object from file
        """
        return cls.loads(fh.read())

    @staticmethod
    def loads(s: str, *args, **kwargs) -> Dict[str, Any]:
        """
        load object from string
        """
        pod: Dict[str, Any] = {}
        try:
            exec(s, pod)  # pylint: disable=exec-used
        except SyntaxError as e:
            raise SerializerSyntaxError(e.msg, e.lineno)
        for k in list(pod.keys()):  # pylint: disable=consider-iterating-dictionary
            if k.startswith('__'):
                del pod[k]
        return pod


def read_pod(source: Union[str, IO], fmt: Optional[str] = None) -> Dict[str, Any]:
    """
    read plain old datastructure from file.
    source -> file handle or a file path
    fmt -> file type - py, json or yaml
    """
    if isinstance(source, str):
        with open(source) as fh:
            return _read_pod(fh, fmt)
    elif hasattr(source, 'read') and (hasattr(source, 'name') or fmt):
        return _read_pod(source, fmt)
    else:
        message: str = 'source must be a path or an open file handle; got {}'
        raise ValueError(message.format(type(source)))


def write_pod(pod: Dict[str, Any], dest: Union[str, IO], fmt: Optional[str] = None) -> None:
    """
    write pod into string or file
    """
    if isinstance(dest, str):
        with open(dest, 'w') as wfh:
            return _write_pod(pod, wfh, fmt)
    elif hasattr(dest, 'write') and (hasattr(dest, 'name') or fmt):
        return _write_pod(pod, dest, fmt)
    else:
        message: str = 'dest must be a path or an open file handle; got {}'
        raise ValueError(message.format(type(dest)))


def dump(o: Any, wfh: IO, fmt: str = 'json', *args, **kwargs):
    serializer = {'yaml': yaml,
                  'json': json,
                  'python': python,
                  'py': python,
                  }.get(fmt)
    if serializer is None:
        raise ValueError('Unknown serialization format: "{}"'.format(fmt))
    serializer.dump(o, wfh, *args, **kwargs)  # type:ignore


def load(s: str, fmt: str = 'json', *args, **kwargs):
    """
    load from string into python object
    """
    return read_pod(s, fmt=fmt)


def _read_pod(fh: IO, fmt: Optional[str] = None) -> Dict[str, Any]:
    """
    read pod from file
    """
    if fmt is None:
        fmt = os.path.splitext(fh.name)[1].lower().strip('.')
        if fmt == '':
            # Special case of no given file extension
            message = ("Could not determine format "
                       "from file extension for \"{}\". "
                       "Please specify it or modify the fmt parameter.")
            raise ValueError(message.format(getattr(fh, 'name', '<none>')))
    if fmt == 'yaml':
        return yaml.load(fh)
    elif fmt == 'json':
        return json.load(fh)
    elif fmt == 'py':
        return python.load(fh)
    else:
        raise ValueError('Unknown format "{}": {}'.format(fmt, getattr(fh, 'name', '<none>')))


def _write_pod(pod: Dict[str, Any], wfh: IO, fmt: Optional[str] = None) -> None:
    """
    write pod into file
    """
    if fmt is None:
        fmt = os.path.splitext(wfh.name)[1].lower().strip('.')
    if fmt == 'yaml':
        return yaml.dump(pod, wfh)
    elif fmt == 'json':
        return json.dump(pod, wfh)
    elif fmt == 'py':
        raise ValueError('Serializing to Python is not supported')
    else:
        raise ValueError('Unknown format "{}": {}'.format(fmt, getattr(wfh, 'name', '<none>')))


def is_pod(obj: Any) -> bool:
    """
    check if object is podable
    """
    if type(obj) not in POD_TYPES:  # pylint: disable=unidiomatic-typecheck
        return False
    if hasattr(obj, 'items'):
        for k, v in obj.items():
            if not (is_pod(k) and is_pod(v)):
                return False
    elif isiterable(obj):
        for v in obj:
            if not is_pod(v):
                return False
    return True


class Podable(object):

    _pod_serialization_version: int = 0

    @classmethod
    def from_pod(cls: Type, pod: Dict[str, Any]) -> 'Podable':
        """
        create a cls object with a plain old datastructure
        """
        pod = cls._upgrade_pod(pod)
        instance = cls()
        instance._pod_version = pod.pop('_pod_version')  # pylint: disable=protected-access
        return instance

    @classmethod
    def _upgrade_pod(cls: Type, pod: Dict[str, Any]) -> Dict[str, Any]:
        """
        upgrade pod version and access the highest implemented upgrade function to do the upgrade
        """
        _pod_serialization_version = pod.pop('_pod_serialization_version', None) or 0
        while _pod_serialization_version < cls._pod_serialization_version:
            _pod_serialization_version += 1
            upgrade: Callable = getattr(cls, '_pod_upgrade_v{}'.format(_pod_serialization_version))
            pod = upgrade(pod)
        return pod

    def __init__(self):
        self._pod_version = self._pod_serialization_version

    def to_pod(self) -> Dict[str, Any]:
        """
        convert the cls to a plain old datastructure
        """
        pod = {}
        pod['_pod_version'] = self._pod_version
        pod['_pod_serialization_version'] = self._pod_serialization_version
        return pod
