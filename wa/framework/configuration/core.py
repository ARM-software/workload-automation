#    Copyright 2014-2018 ARM Limited
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

import os
import logging
from copy import copy, deepcopy
from collections import OrderedDict, defaultdict

from wa.framework.exception import ConfigError, NotFoundError
from wa.framework.configuration.tree import SectionNode, JobSpecSource
from wa.utils import log
from wa.utils.misc import (get_article, merge_config_values)
from wa.utils.types import (identifier, integer, boolean, list_of_strings,
                            list_of, toggle_set, obj_dict, enum)
from wa.utils.serializer import is_pod, Podable
from typing import (Optional, Any, List, Dict, Union, Callable, cast,
                    Tuple, TYPE_CHECKING, DefaultDict, OrderedDict as od,
                    Set)
from typing_extensions import Protocol
if TYPE_CHECKING:
    from wa.framework.configuration.plugin_cache import PluginCache
    from wa.framework.plugin import Plugin
    from wa.framework.target.manager import TargetManager
    from wa.framework.workload import Workload
    from wa.framework.instrument import Instrument
    from wa.framework.output_processor import OutputProcessor
    # When type-checking, pretend StatusType is a standard Enum
    # (or anything you want the type checker to see).
    import enum as en

    class StatusType(en.Enum):
        UNKNOWN = 0
        NEW = 1
        PENDING = 2
        STARTED = 3
        CONNECTED = 4
        INITIALIZED = 5
        RUNNING = 6
        OK = 7
        PARTIAL = 8
        FAILED = 9
        ABORTED = 10
        SKIPPED = 11

        @classmethod
        def from_pod(cls, pod: Dict[str, Any]) -> 'Podable':
            ...

        def to_pod(self) -> Dict[str, Any]:
            ...

# Mapping for kind conversion; see docs for convert_types below
KIND_MAP: Dict[Callable, Callable] = {
    int: integer,
    bool: boolean,
    dict: od,
}

Status = enum(['UNKNOWN', 'NEW', 'PENDING',
               'STARTED', 'CONNECTED', 'INITIALIZED', 'RUNNING',
               'OK', 'PARTIAL', 'FAILED', 'ABORTED', 'SKIPPED'])

logger: logging.Logger = logging.getLogger('config')


##########################
### CONFIG POINT TYPES ###
##########################


class RebootPolicy(object):
    """
    Represents the reboot policy for the execution -- at what points the device
    should be rebooted. This, in turn, is controlled by the policy value that is
    passed in on construction and would typically be read from the user's settings.
    Valid policy values are:

    :never: The device will never be rebooted.
    :as_needed: Only reboot the device if it becomes unresponsive, or needs to be flashed, etc.
    :initial: The device will be rebooted when the execution first starts, just before
              executing the first workload spec.
    :each_spec: The device will be rebooted before running a new workload spec.
    :each_iteration: The device will be rebooted before each new iteration.
    :run_completion: The device will be rebooted after the run has been completed.

    """

    valid_policies: List[str] = ['never', 'as_needed', 'initial', 'each_spec', 'each_job', 'run_completion']

    @staticmethod
    def from_pod(pod: Podable) -> 'RebootPolicy':
        return RebootPolicy(pod)

    def __init__(self, policy: Union['RebootPolicy', str, Podable]):
        if isinstance(policy, RebootPolicy):
            policy = policy.policy
        policy = cast(str, policy).strip().lower().replace(' ', '_')
        if policy not in self.valid_policies:
            message = 'Invalid reboot policy {}; must be one of {}'.format(policy, ', '.join(self.valid_policies))
            raise ConfigError(message)
        self.policy: str = policy

    @property
    def can_reboot(self) -> bool:
        """
        True if reboot policy is not 'never'
        """
        return self.policy != 'never'

    @property
    def perform_initial_reboot(self) -> bool:
        """
        True if reboot policy is 'initial'
        """
        return self.policy == 'initial'

    @property
    def reboot_on_each_job(self) -> bool:
        """
        True if reboot policy is 'each_job'
        """
        return self.policy == 'each_job'

    @property
    def reboot_on_each_spec(self) -> bool:
        """
        True if reboot policy is 'each_spec'
        """
        return self.policy == 'each_spec'

    @property
    def reboot_on_run_completion(self):
        """
        True if reboot policy is 'run_completion'
        """
        return self.policy == 'run_completion'

    def __str__(self):
        return self.policy

    __repr__ = __str__

    def __eq__(self, other):
        if isinstance(other, RebootPolicy):
            return self.policy == other.policy
        else:
            return self.policy == other

    def to_pod(self) -> str:
        return self.policy


class status_list(list):

    def append(self, item: Any):
        list.append(self, str(item).upper())


class LoggingConfig(Podable, dict):
    """
     WA logging configuration. This should be a dict with a subset
    of the following keys::

        :normal_format: Logging format used for console output
        :verbose_format: Logging format used for verbose console output
        :file_format: Logging format used for run.log
        :color: If ``True`` (the default), console logging output will
                contain bash color escape codes. Set this to ``False`` if
                console output will be piped somewhere that does not know
                how to handle those.
    """
    _pod_serialization_version: int = 1

    defaults: Dict[str, Union[str, bool]] = {
        'file_format': '%(asctime)s %(levelname)-8s %(name)s: %(message)s',
        'verbose_format': '%(asctime)s %(levelname)-8s %(name)s: %(message)s',
        'regular_format': '%(levelname)-8s %(message)s',
        'color': True,
    }

    @staticmethod
    def from_pod(pod: Dict) -> 'LoggingConfig':
        pod = LoggingConfig._upgrade_pod(pod)
        pod_version: int = cast(Dict[str, int], pod).pop('_pod_version')
        instance = LoggingConfig(pod)
        instance._pod_version = pod_version  # pylint: disable=protected-access
        return instance

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super(LoggingConfig, self).__init__()
        dict.__init__(self)
        if isinstance(config, dict):
            config = {identifier(k.lower()): v for k, v in config.items()}
            self['regular_format'] = config.pop('regular_format', self.defaults['regular_format'])
            self['verbose_format'] = config.pop('verbose_format', self.defaults['verbose_format'])
            self['file_format'] = config.pop('file_format', self.defaults['file_format'])
            self['color'] = config.pop('colour_enabled', self.defaults['color'])  # legacy
            self['color'] = config.pop('color', self.defaults['color'])
            if config:
                message = 'Unexpected logging configuration parameters: {}'
                raise ValueError(message.format(bad_vals=', '.join(list(config.keys()))))
        elif config is None:
            for k, v in self.defaults.items():
                self[k] = v
        else:
            raise ValueError(config)

    def to_pod(self) -> Dict:
        pod = super(LoggingConfig, self).to_pod()
        pod.update(self)
        return pod

    @staticmethod
    def _pod_upgrade_v1(pod: Dict) -> Dict:
        pod['_pod_version'] = pod.get('_pod_version', 1)
        return pod


def expanded_path(path: str) -> str:
    """
    Ensure that the provided path has been expanded if applicable
    """
    return os.path.expanduser(str(path))


def get_type_name(kind) -> str:
    """
    get the type name
    """
    typename = str(kind)
    if '\'' in typename:
        typename = typename.split('\'')[1]
    elif typename.startswith('<function'):
        typename = typename.split()[1]
    return typename


class ConfigurationPoint(object):
    """
    This defines a generic configuration point for workload automation. This is
    used to handle global settings, plugin parameters, etc.

    """

    def __init__(self, name: str,
                 kind: Optional[Callable] = None,
                 mandatory: Optional[bool] = None,
                 default: Any = None,
                 override: bool = False,
                 allowed_values: Optional[List[Any]] = None,
                 description: Optional[str] = None,
                 constraint: Optional[Union[Callable[..., bool], Tuple[Callable[..., bool], str]]] = None,
                 merge: bool = False,
                 aliases: Optional[List[str]] = None,
                 global_alias: Optional[str] = None,
                 deprecated: bool = False):
        """
        Create a new Parameter object.

        :param name: The name of the parameter. This will become an instance
                     member of the plugin object to which the parameter is
                     applied, so it must be a valid python  identifier. This
                     is the only mandatory parameter.
        :param kind: The type of parameter this is. This must be a callable
                     that takes an arbitrary object and converts it to the
                     expected type, or raised ``ValueError`` if such conversion
                     is not possible. Most Python standard types -- ``str``,
                     ``int``, ``bool``, etc. -- can be used here. This
                     defaults to ``str`` if not specified.
        :param mandatory: If set to ``True``, then a non-``None`` value for
                          this parameter *must* be provided on plugin
                          object construction, otherwise ``ConfigError``
                          will be raised.
        :param default: The default value for this parameter. If no value
                        is specified on plugin construction, this value
                        will be used instead. (Note: if this is specified
                        and is not ``None``, then ``mandatory`` parameter
                        will be ignored).
        :param override: A ``bool`` that specifies whether a parameter of
                         the same name further up the hierarchy should
                         be overridden. If this is ``False`` (the
                         default), an exception will be raised by the
                         ``AttributeCollection`` instead.
        :param allowed_values: This should be the complete list of allowed
                               values for this parameter.  Note: ``None``
                               value will always be allowed, even if it is
                               not in this list.  If you want to disallow
                               ``None``, set ``mandatory`` to ``True``.
        :param constraint: If specified, this must be a callable that takes
                           the parameter value as an argument and return a
                           boolean indicating whether the constraint has been
                           satisfied. Alternatively, can be a two-tuple with
                           said callable as the first element and a string
                           describing the constraint as the second.
        :param merge: The default behaviour when setting a value on an object
                      that already has that attribute is to overrided with
                      the new value. If this is set to ``True`` then the two
                      values will be merged instead. The rules by which the
                      values are merged will be determined by the types of
                      the existing and new values -- see
                      ``merge_config_values`` documentation for details.
        :param aliases: Alternative names for the same configuration point.
                        These are largely for backwards compatibility.
        :param global_alias: An alias for this parameter that can be specified at
                            the global level. A global_alias can map onto many
                            ConfigurationPoints.
        :param deprecated: Specify that this parameter is deprecated and its
                           config should be ignored. If supplied WA will display
                           a warning to the user however will continue execution.
        """
        self.name = identifier(name)
        kind = KIND_MAP.get(kind, kind) if kind else None
        if kind is not None and not callable(kind):
            raise ValueError('Kind must be callable.')
        self.kind = kind
        self.mandatory = mandatory
        if not is_pod(default):
            msg = "The default for '{}' must be a Plain Old Data type, but it is of type '{}' instead."
            raise TypeError(msg.format(self.name, type(default)))
        self.default = default
        self.override = override
        self.allowed_values = allowed_values
        self.description = description
        if self.kind is None and not self.override:
            self.kind = str
        if constraint is not None and not callable(constraint) and not isinstance(constraint, tuple):
            raise ValueError('Constraint must be callable or a (callable, str) tuple.')
        self.constraint = constraint
        self.merge = merge
        self.aliases = aliases or []
        self.global_alias = global_alias
        self.deprecated = deprecated

        if self.default is not None:
            try:
                self.validate_value("init", self.default)
            except ConfigError:
                raise ValueError('Default value "{}" is not valid'.format(self.default))

    def match(self, name: str) -> bool:
        """
        check whether name is matching the config point name or its aliases
        """
        if name == self.name or name in self.aliases:
            return True
        elif name == self.global_alias:
            return True
        return False

    def set_value(self, obj: Union['Configuration', obj_dict, 'Plugin'], value: Any = None,
                  check_mandatory: bool = True) -> None:
        """
        set the value to the configuration
        """
        if self.deprecated:
            if value is not None:
                msg: str = 'Depreciated parameter supplied for "{}" in "{}". The value will be ignored.'
                logger.warning(msg.format(self.name, obj.name))
            return
        if value is None:
            if self.default is not None:
                if self.kind:
                    value = self.kind(self.default)
            elif check_mandatory and self.mandatory:
                msg = 'No values specified for mandatory parameter "{}" in {}'
                raise ConfigError(msg.format(self.name, obj.name))
        else:
            try:
                if self.kind:
                    value = self.kind(value)
            except (ValueError, TypeError):
                typename: str = get_type_name(self.kind)
                msg = 'Bad value "{}" for {}; must be {} {}'
                article = get_article(typename)
                raise ConfigError(msg.format(value, self.name, article, typename))
        if value is not None:
            self.validate_value(self.name, value)
        if self.merge and hasattr(obj, self.name):
            value = merge_config_values(getattr(obj, self.name), value)
        setattr(obj, self.name, value)

    def validate(self, obj: Union['Configuration', 'Plugin'], check_mandatory: bool = True) -> None:
        """
        validate the value and deprecated as well as mandatory status
        """
        if self.deprecated:
            return
        value = getattr(obj, self.name, None)
        if value is not None:
            self.validate_value(obj.name or '', value)
        else:
            if check_mandatory and self.mandatory:
                msg = 'No value specified for mandatory parameter "{}" in {}.'
                raise ConfigError(msg.format(self.name, obj.name))

    def validate_value(self, name: str, value: Any) -> None:
        """
        validate the value against allowed values or constraints
        """
        if self.allowed_values:
            self.validate_allowed_values(name, value)
        if self.constraint:
            self.validate_constraint(name, value)

    def validate_allowed_values(self, name: str, value: Any) -> None:
        """
        validate against allowed values
        """
        if 'list' in str(self.kind):
            for v in value:
                if self.allowed_values and v not in self.allowed_values:
                    msg = 'Invalid value {} for {} in {}; must be in {}'
                    raise ConfigError(msg.format(v, self.name, name, self.allowed_values))
        else:
            if self.allowed_values and value not in self.allowed_values:
                msg = 'Invalid value {} for {} in {}; must be in {}'
                raise ConfigError(msg.format(value, self.name, name, self.allowed_values))

    def validate_constraint(self, name: str, value: Any) -> None:
        """
        validate against the constraints
        """
        msg_vals: Dict[str, Any] = {'value': value, 'param': self.name, 'plugin': name}
        if isinstance(self.constraint, tuple) and len(self.constraint) == 2:
            constraint, msg = self.constraint  # pylint: disable=unpacking-non-sequence
        elif callable(self.constraint):
            constraint = self.constraint
            msg = '"{value}" failed constraint validation for "{param}" in "{plugin}".'
        else:
            raise ValueError('Invalid constraint for "{}": must be callable or a 2-tuple'.format(self.name))
        if not constraint(value):
            raise ConfigError(value, msg.format(**msg_vals))

    def __repr__(self):
        d = copy(self.__dict__)
        del d['description']
        return 'ConfigurationPoint({})'.format(d)

    __str__ = __repr__


#####################
### Configuration ###
#####################


def _to_pod(cfg_point: ConfigurationPoint, value: Any) -> Any:
    """
    convert value to a plain old datatype (pod)
    """
    if is_pod(value):
        return value
    if hasattr(cfg_point.kind, 'to_pod'):
        return cast(Podable, value).to_pod()
    msg: str = '{} value "{}" is not serializable'
    raise ValueError(msg.format(cfg_point.name, value))


class Configuration(Podable):
    """
    configure the behaviour of WA and how a run as a whole will behave.
    The most common options that that you may want to specify are:

    :device: The name of the 'device' that you wish to perform the run
            on. This name is a combination of a devlib
            `Platform <http://devlib.readthedocs.io/en/latest/platform.html>`_ and
            `Target <http://devlib.readthedocs.io/en/latest/target.html>`_. To
            see the available options please use ``wa list targets``.
    :device_config: The is a dict mapping allowing you to configure which target
                    to connect to  (e.g. ``host`` for an SSH connection or
                    ``device`` to specific an ADB name) as well as configure other
                    options for the device for example the ``working_directory``
                    or the list of ``modules`` to be loaded onto the device. (For
                    more information please see
                    :ref:`here <android-general-device-setup>`)
    :execution_order: Defines the order in which the agenda spec will be executed.
    :reboot_policy: Defines when during execution of a run a Device will be rebooted.
    :max_retries: The maximum number of times failed jobs will be retried before giving up.
    :allow_phone_home: Prevent running any workloads that are marked with ‘phones_home’.
    """
    _pod_serialization_version: int = 1
    config_points: List[ConfigurationPoint] = []
    name: str = ''

    # The below line must be added to all subclasses
    configuration: Dict[str, ConfigurationPoint] = {cp.name: cp for cp in config_points}

    @classmethod
    def from_pod(cls, pod: Dict[str, Any]) -> 'Configuration':
        """
        create Configuration object from a plain old datastructure
        """
        instance = cast('Configuration', super(Configuration, cls).from_pod(pod))
        for cfg_point in cls.config_points:
            if cfg_point.name in pod:
                value = pod.pop(cfg_point.name)
                if hasattr(cfg_point.kind, 'from_pod'):
                    value = cast(Podable, cfg_point.kind).from_pod(value)
                cfg_point.set_value(instance, value)
        if pod:
            msg = 'Invalid entry(ies) for "{}": "{}"'
            raise ValueError(msg.format(cls.name, '", "'.join(list(pod.keys()))))
        return instance

    def __init__(self):
        super(Configuration, self).__init__()
        for confpoint in self.config_points:
            confpoint.set_value(self, check_mandatory=False)

    def set(self, name: str, value: Any, check_mandatory: bool = True) -> None:
        """
        set the value to the configuration point with the given name
        """
        if name not in self.configuration:
            raise ConfigError('Unknown {} configuration "{}"'.format(self.name,
                                                                     name))
        try:
            self.configuration[name].set_value(self, value,
                                               check_mandatory=check_mandatory)
        except (TypeError, ValueError, ConfigError) as e:
            msg = 'Invalid value "{}" for "{}": {}'
            raise ConfigError(msg.format(value, name, e))

    def update_config(self, values: Any, check_mandatory: bool = True) -> None:
        """
        update configuration with new values
        """
        for k, v in values.items():
            self.set(k, v, check_mandatory=check_mandatory)

    def validate(self) -> None:
        """
        validate all the configuration points in the configuration
        """
        for cfg_point in self.config_points:
            cfg_point.validate(self)

    def to_pod(self) -> Dict[str, Any]:
        """
        convert Configuration to a plain old datastructure
        """
        pod = super(Configuration, self).to_pod()
        for cfg_point in self.config_points:
            value = getattr(self, cfg_point.name, None)
            pod[cfg_point.name] = _to_pod(cfg_point, value)
        return pod

    @staticmethod
    def _pod_upgrade_v1(pod: Dict[str, Any]) -> Dict[str, Any]:
        """
        pod upgrade function for Configuration class
        """
        pod['_pod_version'] = pod.get('_pod_version', 1)
        return pod


class MetaConfigurationProtocol(Protocol):
    plugin_packages: List[str]
    dependencies_directory: str
    plugins_directory: str
    cache_directory: str
    plugin_paths: List[str]
    user_config_file: str
    additional_packages_file: str
    target_info_cache_file: str
    apk_info_cache_file: str
    user_directory: str
    assets_repository: str
    logging: LoggingConfig
    verbosity: int
    default_output_directory: str
    extra_plugin_paths: List[str]
    configuration: Dict[str, ConfigurationPoint]

    def to_pod(self) -> Dict[str, Any]:
        ...

    def set(self, name: str, value: Any, check_mandatory: bool = True) -> None:
        ...


# This configuration for the core WA framework
class MetaConfiguration(Configuration):
    """
    There are also a couple of settings are used to provide additional metadata
    for a run. These may get picked up by instruments or output processors to
    attach context to results.
    """
    name: str = "Meta Configuration"

    core_plugin_packages: List[str] = [
        'wa.commands',
        'wa.framework.getters',
        'wa.framework.target.descriptor',
        'wa.instruments',
        'wa.output_processors',
        'wa.workloads',
    ]

    config_points: List[ConfigurationPoint] = [
        ConfigurationPoint(
            'user_directory',
            description="""
            Path to the user directory. This is the location WA will look for
            user configuration, additional plugins and plugin dependencies.
            """,
            kind=expanded_path,
            default=os.path.join(os.path.expanduser('~'), '.workload_automation'),
        ),
        ConfigurationPoint(
            'assets_repository',
            description="""
            The local mount point for the filer hosting WA assets.
            """,
            default=''
        ),
        ConfigurationPoint(
            'logging',
            kind=LoggingConfig,
            default=LoggingConfig.defaults,
            description="""
            WA logging configuration. This should be a dict with a subset
            of the following keys::

                :normal_format: Logging format used for console output
                :verbose_format: Logging format used for verbose console output
                :file_format: Logging format used for run.log
                :color: If ``True`` (the default), console logging output will
                        contain bash color escape codes. Set this to ``False`` if
                        console output will be piped somewhere that does not know
                        how to handle those.
            """,
        ),
        ConfigurationPoint(
            'verbosity',
            kind=int,
            default=0,
            description="""
            Verbosity of console output.
            """,
        ),
        ConfigurationPoint(  # TODO: Needs some format for dates etc/ comes from cfg
            'default_output_directory',
            default="wa_output",
            description="""
            The default output directory that will be created if not
            specified when invoking a run.
            """,
        ),
        ConfigurationPoint(
            'extra_plugin_paths',
            kind=list_of_strings,
            description="""
            A list of additional paths to scan for plugins.
            """,
        ),
    ]
    configuration: Dict[str, ConfigurationPoint] = {cp.name: cp for cp in config_points}

    @property
    def dependencies_directory(self) -> str:
        """
        dependencies directory, typically ``~/.workload_automation/dependencies/<workload_name>``
        """
        return os.path.join(cast(MetaConfigurationProtocol, self).user_directory, 'dependencies')

    @property
    def plugins_directory(self) -> str:
        """
        plugins directory
        """
        return os.path.join(cast(MetaConfigurationProtocol, self).user_directory, 'plugins')

    @property
    def cache_directory(self) -> str:
        """
        cache directory
        """
        return os.path.join(cast(MetaConfigurationProtocol, self).user_directory, 'cache')

    @property
    def plugin_paths(self) -> List[str]:
        """
        list of plugin paths
        """
        return [self.plugins_directory] + (cast(MetaConfigurationProtocol, self).extra_plugin_paths or [])

    @property
    def user_config_file(self) -> str:
        """
        user configuration file
        """
        return os.path.join(cast(MetaConfigurationProtocol, self).user_directory, 'config.yaml')

    @property
    def additional_packages_file(self) -> str:
        """
        Additional packages file
        """
        return os.path.join(cast(MetaConfigurationProtocol, self).user_directory, 'packages')

    @property
    def target_info_cache_file(self) -> str:
        """
        target information cache file
        """
        return os.path.join(self.cache_directory, 'targets.json')

    @property
    def apk_info_cache_file(self) -> str:
        """
        apk information cache file
        """
        return os.path.join(self.cache_directory, 'apk_info.json')

    def __init__(self, environ: Optional[os._Environ] = None):
        super(MetaConfiguration, self).__init__()
        if environ is None:
            environ = os.environ
        user_directory: str = environ.pop('WA_USER_DIRECTORY', '')
        if user_directory:
            self.set('user_directory', user_directory)

        extra_plugin_paths: str = environ.pop('WA_PLUGIN_PATHS', '')
        if extra_plugin_paths:
            self.set('extra_plugin_paths', extra_plugin_paths.split(os.pathsep))

        self.plugin_packages: List[str] = copy(self.core_plugin_packages)
        if os.path.isfile(self.additional_packages_file):
            with open(self.additional_packages_file) as fh:
                extra_packages = [p.strip() for p in fh.read().split('\n') if p.strip()]
                self.plugin_packages.extend(extra_packages)


class RunConfigurationProtocol(Protocol):
    device_config: Optional[obj_dict]
    augmentations: Dict[str, Dict[str, Optional[ConfigurationPoint]]]
    resource_getters: Dict[str, Dict[str, Optional[ConfigurationPoint]]]
    run_name: str
    project: str
    project_stage: Union[Dict, str]
    execution_order: str
    reboot_policy: RebootPolicy
    device: str
    retry_on_status: List
    max_retries: int
    bail_on_init_failure: bool
    bail_on_job_failure: bool
    allow_phone_home: bool
    name: str
    meta_data: List[ConfigurationPoint]
    config_points: List[ConfigurationPoint]
    configuration: Dict[str, ConfigurationPoint]

    def set(self, name: str, value: Any, check_mandatory: bool = True) -> None:
        ...

    def add_augmentation(self, aug: 'Plugin') -> None:
        ...

    def add_resource_getter(self, getter: 'Plugin') -> None:
        ...

    def to_pod(self) -> Dict[str, Any]:
        ...

    def merge_device_config(self, plugin_cache: 'PluginCache') -> None:
        ...


# This is generic top-level configuration for WA runs.
class RunConfiguration(Configuration):
    """
    In addition to specifying run execution parameters through an agenda, the
    behaviour of WA can be modified through configuration file(s). The default
    configuration file is ``~/.workload_automation/config.yaml``  (the location can
    be changed by setting ``WA_USER_DIRECTORY`` environment variable.
    This file will be created when you first run WA if it does not already exist.
    This file must always exist and will always be loaded. You can add to or override
    the contents of that file on invocation of Workload Automation by specifying an
    additional configuration file using ``--config`` option. Variables with specific
    names  will be picked up by the framework and used to modify the behaviour of
    Workload automation e.g. the ``iterations`` variable might be specified to tell
    WA how many times to run each workload.
    """
    name: str = "Run Configuration"

    # Metadata is separated out because it is not loaded into the auto
    # generated config file
    meta_data: List[ConfigurationPoint] = [
        ConfigurationPoint(
            'run_name',
            kind=str,
            description='''
            A string that labels the WA run that is being performed. This would
            typically be set in the ``config`` section of an agenda (see
            :ref:`configuration in an agenda <configuration_in_agenda>`) rather
            than in the config file.
            ''',
        ),
        ConfigurationPoint(
            'project',
            kind=str,
            description='''
            A string naming the project for which data is being collected. This
            may be useful, e.g. when uploading data to a shared database that
            is populated from multiple projects.
            ''',
        ),
        ConfigurationPoint(
            'project_stage',
            kind=dict,
            description='''
            A dict or a string that allows adding additional identifier. This
            is may be useful for long-running projects.
            ''',
        ),
    ]
    config_points: List[ConfigurationPoint] = [
        ConfigurationPoint(
            'execution_order',
            kind=str,
            default='by_iteration',
            allowed_values=['by_iteration', 'by_section', 'by_workload', 'random'],
            description='''
            Defines the order in which the agenda spec will be executed. At the
            moment, the following execution orders are supported:

            ``"by_iteration"``
                The first iteration of each workload spec is executed one after
                the other, so all workloads are executed before proceeding on
                to the second iteration.  E.g. A1 B1 C1 A2 C2 A3. This is the
                default if no order is explicitly specified.

                In case of multiple sections, this will spread them out, such
                that specs from the same section are further part. E.g. given
                sections X and Y, global specs A and B, and two iterations,
                this will run ::

                        X.A1, Y.A1, X.B1, Y.B1, X.A2, Y.A2, X.B2, Y.B2

            ``"by_section"``
                Same  as ``"by_iteration"``, however this will group specs from
                the same section together, so given sections X and Y, global
                specs A and B, and two iterations, this will run ::

                        X.A1, X.B1, Y.A1, Y.B1, X.A2, X.B2, Y.A2, Y.B2

            ``"by_workload"``
                All iterations of the first spec are executed before moving on
                to the next spec. E.g::

                        X.A1, X.A2, Y.A1, Y.A2, X.B1, X.B2, Y.B1, Y.B2

            ``"random"``
                Execution order is entirely random.
            ''',
        ),
        ConfigurationPoint(
            'reboot_policy',
            kind=RebootPolicy,
            default='as_needed',
            allowed_values=RebootPolicy.valid_policies,
            description='''
            This defines when during execution of a run the Device will be
            rebooted. The possible values are:

            ``"as_needed"``
                The device will only be rebooted if the need arises (e.g. if it
                becomes unresponsive.

            ``"never"``
                The device will never be rebooted.

            ``"initial"``
                The device will be rebooted when the execution first starts,
                just before executing the first workload spec.

            ``"each_job"``
                The device will be rebooted before each new job.

            ``"each_spec"``
                The device will be rebooted before running a new workload spec.

                .. note:: This acts the same as ``each_job`` when execution order
                          is set to by_iteration

            ``"run_completion"``
                 The device will be rebooted after the run has been completed.
            '''),
        ConfigurationPoint(
            'device',
            kind=str,
            default='generic_android',
            description='''
            This setting defines what specific ``Device`` subclass will be used to
            interact the connected device. Obviously, this must match your
            setup.
            ''',
        ),
        ConfigurationPoint(
            'retry_on_status',
            kind=list_of(Status),
            default=['FAILED', 'PARTIAL'],
            allowed_values=Status.levels[Status.RUNNING.value:],
            description='''
            This is list of statuses on which a job will be considered to have
            failed and will be automatically retried up to ``max_retries``
            times. This defaults to ``["FAILED", "PARTIAL"]`` if not set.
            Possible values are:

            ``"OK"``
                This iteration has completed and no errors have been detected

            ``"PARTIAL"``
                One or more instruments have failed (the iteration may still be
                running).

            ``"FAILED"``
                The workload itself has failed.

            ``"ABORTED"``
                The user interrupted the workload.
            ''',
        ),
        ConfigurationPoint(
            'max_retries',
            kind=int,
            default=2,
            description='''
            The maximum number of times failed jobs will be retried before
            giving up.

            .. note:: This number does not include the original attempt
            ''',
        ),
        ConfigurationPoint(
            'bail_on_init_failure',
            kind=bool,
            default=True,
            description='''
            When jobs fail during their main setup and run phases, WA will
            continue attempting to run the remaining jobs. However, by default,
            if they fail during their early initialization phase, the entire run
            will end without continuing to run jobs. Setting this to ``False``
            means that WA will instead skip all the jobs from the job spec that
            failed, but continue attempting to run others.
            '''
        ),
        ConfigurationPoint(
            'bail_on_job_failure',
            kind=bool,
            default=False,
            description='''
            When a job fails during its run phase, WA will attempt to retry the
            job, then continue with remaining jobs after. Setting this to
            ``True`` means WA will skip remaining jobs and end the run if a job
            has retried the maximum number of times, and still fails.
            '''
        ),
        ConfigurationPoint(
            'allow_phone_home',
            kind=bool, default=True,
            description='''
            Setting this to ``False`` prevents running any workloads that are marked
            with 'phones_home', meaning they are at risk of exposing information
            about the device to the outside world. For example, some benchmark
            applications upload device data to a database owned by the
            maintainers.

            This can be used to minimise the risk of accidentally running such
            workloads when testing confidential devices.
            '''),
    ]
    configuration: Dict[str, ConfigurationPoint] = {cp.name: cp for cp in config_points + meta_data}

    @classmethod
    def from_pod(cls, pod: Dict[str, Any]) -> 'RunConfiguration':
        """
        create a RunConfiguration object from a plain old datastructure
        """
        meta_pod: Dict[str, Any] = {}
        for cfg_point in cls.meta_data:
            meta_pod[cfg_point.name] = pod.pop(cfg_point.name, None)

        device_config: Optional[obj_dict] = pod.pop('device_config', None)
        augmentations: Dict[str, Dict[str, Optional[ConfigurationPoint]]] = pod.pop('augmentations', {})
        getters: Dict[str, Dict[str, Optional[ConfigurationPoint]]] = pod.pop('resource_getters', {})
        instance = cast('RunConfiguration', super(RunConfiguration, cls).from_pod(pod))
        instance.device_config = device_config
        instance.augmentations = augmentations
        instance.resource_getters = getters
        for cfg_point in cls.meta_data:
            cfg_point.set_value(instance, meta_pod[cfg_point.name])

        return instance

    def __init__(self) -> None:
        super(RunConfiguration, self).__init__()
        for confpoint in self.meta_data:
            confpoint.set_value(self, check_mandatory=False)
        self.device_config: Optional[obj_dict] = None
        self.augmentations: Dict[str, Dict[str, Optional[ConfigurationPoint]]] = {}
        self.resource_getters: Dict[str, Dict[str, Optional[ConfigurationPoint]]] = {}

    def merge_device_config(self, plugin_cache: 'PluginCache') -> None:
        """
        Merges global device config and validates that it is correct for the
        selected device.
        """
        # pylint: disable=no-member
        if cast(RunConfigurationProtocol, self).device is None:
            msg = 'Attempting to merge device config with unspecified device'
            raise RuntimeError(msg)
        self.device_config = plugin_cache.get_plugin_config(cast(RunConfigurationProtocol, self).device,
                                                            generic_name="device_config")

    def add_augmentation(self, aug: 'Plugin') -> None:
        """
        add an augmentation to the run configuration
        """
        if aug.name in self.augmentations:
            raise ValueError('Augmentation "{}" already added.'.format(aug.name))
        if aug.name:
            self.augmentations[aug.name] = aug.get_config()

    def add_resource_getter(self, getter: 'Plugin') -> None:
        """
        add a resource getter to the run configuration
        """
        if getter.name in self.resource_getters:
            raise ValueError('Resource getter "{}" already added.'.format(getter.name))
        if getter.name:
            self.resource_getters[getter.name] = getter.get_config()

    def to_pod(self) -> Dict[str, Any]:
        """
        Convert Run Configuration to a plain old datastructure
        """
        pod = super(RunConfiguration, self).to_pod()
        pod['device_config'] = dict(self.device_config or {})
        pod['augmentations'] = self.augmentations
        pod['resource_getters'] = self.resource_getters
        return pod


class JobSpecProtocol(Protocol):
    id: Optional[str]
    section_id: Optional[str]
    workload_id: Optional[str]
    iterations: int
    workload_name: str
    workload_parameters: obj_dict
    runtime_parameters: obj_dict
    boot_parameters: obj_dict
    label: str
    augmentations: toggle_set
    flash: Dict
    classifiers: od[str, str]
    _sources: List[JobSpecSource]

    @classmethod
    def from_pod(cls, pod: Dict[str, Any]) -> 'Podable':
        ...

    def to_pod(self) -> Dict[str, Any]:
        ...


class JobSpec(Configuration):
    # pylint: disable=access-member-before-definition,attribute-defined-outside-init
    """
    Job specification
    """
    name: str = "Job Spec"

    config_points: List[ConfigurationPoint] = [
        ConfigurationPoint('iterations', kind=int, default=1,
                           description='''
                           How many times to repeat this workload spec
                           '''),
        ConfigurationPoint('workload_name', kind=str, mandatory=True,
                           aliases=["name"],
                           description='''
                           The name of the workload to run.
                           '''),
        ConfigurationPoint('workload_parameters', kind=obj_dict, merge=True,
                           aliases=["params", "workload_params", "parameters"],
                           description='''
                           Parameter to be passed to the workload
                           '''),
        ConfigurationPoint('runtime_parameters', kind=obj_dict, merge=True,
                           aliases=["runtime_params"],
                           description='''
                           Runtime parameters to be set prior to running
                           the workload.
                           '''),
        ConfigurationPoint('boot_parameters', kind=obj_dict,
                           aliases=["boot_params"],
                           description='''
                           Parameters to be used when rebooting the target
                           prior to running the workload.
                           '''),
        ConfigurationPoint('label', kind=str,
                           description='''
                           Similar to IDs but do not have the uniqueness restriction.
                           If specified, labels will be used by some output
                           processors instead of (or in addition to) the workload
                           name. For example, the csv output processor will put
                           the label in the "workload" column of the CSV file.
                           '''),
        ConfigurationPoint('augmentations', kind=toggle_set, merge=True,
                           aliases=["instruments", "processors", "instrumentation",
                                    "output_processors", "augment", "result_processors"],
                           description='''
                           The instruments and output processors to enable (or
                           disabled using a ~) during this workload spec. This combines the
                           "instrumentation" and "result_processors" from
                           previous versions of WA (the old entries are now
                           aliases for this).
                           '''),
        ConfigurationPoint('flash', kind=dict, merge=True,
                           description='''

                           '''),
        ConfigurationPoint('classifiers', kind=dict, merge=True,
                           description='''
                           Classifiers allow you to tag metrics from this workload
                           spec to help in post processing them. Theses are often
                           used to help identify what runtime_parameters were used
                           for results when post processing.
                           '''),
    ]
    configuration: Dict[str, ConfigurationPoint] = {cp.name: cp for cp in config_points}

    @classmethod
    def from_pod(cls, pod: Dict[str, Any]) -> 'JobSpec':
        """
        Create a JobSpec object from a plain old datastructure
        """
        job_id: str = pod.pop('id')
        instance = cast('JobSpec', super(JobSpec, cls).from_pod(pod))
        instance.id = job_id
        return instance

    @property
    def section_id(self) -> Optional[str]:
        """
        section id
        """
        if self.id is not None:
            return self.id.rsplit('-', 1)[0]
        return None

    @property
    def workload_id(self) -> Optional[str]:
        """
        workload id
        """
        if self.id is not None:
            return self.id.rsplit('-', 1)[-1]
        return None

    def __init__(self) -> None:
        super(JobSpec, self).__init__()
        if self.classifiers is None:
            self.classifiers: od[str, str] = OrderedDict()
        self.to_merge: DefaultDict[str, Dict[JobSpecSource, Any]] = defaultdict(OrderedDict)
        self._sources: List[JobSpecSource] = []
        self.id: Optional[str] = None
        if self.boot_parameters is None:
            self.boot_parameters: obj_dict = obj_dict()
        if self.runtime_parameters is None:
            self.runtime_parameters: obj_dict = obj_dict()

    def to_pod(self) -> Dict[str, Any]:
        """
        Convert JobSpec to a plain old datastructure
        """
        pod = super(JobSpec, self).to_pod()
        pod['id'] = self.id
        return pod

    # FIXME - the base class update_config seems to have the second argument as a Dict[str,Any]
    # but the inherited class Jobspec implements it with second arg as a JobSpecSource type.
    # currently keeping the type as Any in the base class works, but may not be the right thing to do.
    def update_config(self, source: JobSpecSource, check_mandatory: bool = True):  # pylint: disable=arguments-differ
        self._sources.append(source)
        values = source.config
        for k, v in values.items():
            if k == "id":
                continue
            elif cast(str, k).endswith('_parameters'):
                if v:
                    self.to_merge[k][source] = copy(v)
            else:
                try:
                    self.set(k, v, check_mandatory=check_mandatory)
                except ConfigError as e:
                    msg: str = 'Error in {}:\n\t{}'
                    raise ConfigError(msg.format(source.name, e.message))

    def merge_workload_parameters(self, plugin_cache: 'PluginCache') -> None:
        """
        merge the workload parameters
        """
        # merge global generic and specific config
        workload_params: obj_dict = plugin_cache.get_plugin_config(cast(JobSpecProtocol, self).workload_name,
                                                                   generic_name="workload_parameters",
                                                                   is_final=False)

        cfg_points: Dict[str, ConfigurationPoint] = plugin_cache.get_plugin_parameters(cast(JobSpecProtocol, self).workload_name)
        for source in self._sources:
            config = dict(self.to_merge["workload_parameters"].get(source, {}))
            if not config:
                continue

            for name, cfg_point in cfg_points.items():
                if name in config:
                    value = config.pop(name)
                    cfg_point.set_value(workload_params, value,
                                        check_mandatory=False)
            if config:
                msg = 'Unexpected config "{}" for "{}"'
                raise ConfigError(msg.format(config, cast(JobSpecProtocol, self).workload_name))

        self.workload_parameters = workload_params

    def merge_runtime_parameters(self, plugin_cache: 'PluginCache', target_manager: 'TargetManager') -> None:
        """
        merge the runtime parameters
        """
        # Order global runtime parameters
        runtime_parameters: od[JobSpecSource, Dict[str, ConfigurationPoint]] = OrderedDict()
        try:
            global_runtime_params: Union[obj_dict, Dict[JobSpecSource, Any]] = plugin_cache.get_plugin_config("runtime_parameters")
        except NotFoundError:
            global_runtime_params = {}
        for source in plugin_cache.sources:
            if source in global_runtime_params:
                runtime_parameters[source] = global_runtime_params[source]  # type:ignore

        # Add runtime parameters from JobSpec
        for source, values in self.to_merge['runtime_parameters'].items():
            runtime_parameters[source] = values

        # Merge
        self.runtime_parameters = cast(obj_dict, target_manager.merge_runtime_parameters(runtime_parameters))

    def finalize(self) -> None:
        """
        finakize jobspec creation
        """
        self.id = "-".join([str(source.config['id'])
                            for source in self._sources[1:]])  # ignore first id, "global"

        # ensure *_parameters are always obj_dict's
        self.boot_parameters = obj_dict(list((self.boot_parameters or {}).items()))
        self.runtime_parameters = obj_dict(list((self.runtime_parameters or {}).items()))
        self.workload_parameters = obj_dict(list((self.workload_parameters or {}).items()))

        if cast(JobSpecProtocol, self).label is None:
            self.label = cast(JobSpecProtocol, self).workload_name


# This is used to construct the list of Jobs WA will run
class JobGenerator(object):
    """
    construct the list of jobs WA will run
    """
    name: str = "Jobs Configuration"

    def __init__(self, plugin_cache: 'PluginCache'):
        self.plugin_cache = plugin_cache
        self.ids_to_run: List[str] = []
        self.workloads: List['Workload'] = []
        self._enabled_augmentations = toggle_set()
        self._enabled_instruments: Optional[List[str]] = None
        self._enabled_processors: Optional[List[str]] = None
        self._read_augmentations: bool = False
        self.disabled_augmentations: Set[str] = set()

        self.job_spec_template: obj_dict = obj_dict(not_in_dict=['name'])
        self.job_spec_template.name = "globally specified job spec configuration"
        self.job_spec_template.id = "global"
        # Load defaults
        for cfg_point in JobSpec.configuration.values():
            cfg_point.set_value(self.job_spec_template, check_mandatory=False)

        self.root_node = SectionNode(self.job_spec_template)

    @property
    def enabled_instruments(self) -> List[str]:
        """
        get the enabled instruments for the job
        """
        self._read_augmentations = True
        if self._enabled_instruments is None:
            self._enabled_instruments = []
            for entry in list(self._enabled_augmentations.merge_with(self.disabled_augmentations).values()):
                entry_cls = self.plugin_cache.get_plugin_class(entry)
                if entry_cls and entry_cls.kind == 'instrument':
                    self._enabled_instruments.append(entry)
        return self._enabled_instruments

    @property
    def enabled_processors(self) -> List[str]:
        """
        get the enabled output processors for the job
        """
        self._read_augmentations = True
        if self._enabled_processors is None:
            self._enabled_processors = []
            for entry in list(self._enabled_augmentations.merge_with(self.disabled_augmentations).values()):
                entry_cls = self.plugin_cache.get_plugin_class(entry)
                if entry_cls and entry_cls.kind == 'output_processor':
                    self._enabled_processors.append(entry)
        return self._enabled_processors

    def set_global_value(self, name: str, value: Any) -> None:
        """
        set value to a global job spec configuration or augmentations
        """
        JobSpec.configuration[name].set_value(self.job_spec_template, value,
                                              check_mandatory=False)
        if name == "augmentations":
            self.update_augmentations(value)

    def add_section(self, section: obj_dict, workloads: List[obj_dict], group: str) -> None:
        """
        Add a new section to the job tree
        """
        new_node: SectionNode = self.root_node.add_section(section, group)
        with log.indentcontext():
            for workload in workloads:
                new_node.add_workload(workload)

    def add_workload(self, workload: obj_dict) -> None:
        """
        add a workload to the job tree
        """
        self.root_node.add_workload(workload)

    def disable_augmentations(self, augmentations: toggle_set):
        """
        disable augmentations
        """
        for entry in augmentations:
            if entry == '~~':
                continue
            if entry.startswith('~'):
                entry = entry[1:]
            try:
                self.plugin_cache.get_plugin_class(entry)
            except NotFoundError:
                raise ConfigError('Error disabling unknown augmentation: "{}"'.format(entry))
        self.disabled_augmentations = self.disabled_augmentations.union(augmentations)

    def update_augmentations(self, value: Any) -> None:
        """
        update augmentations
        """
        if self._read_augmentations:
            msg = 'Cannot update augmentations after they have been accessed'
            raise RuntimeError(msg)
        self._enabled_augmentations = self._enabled_augmentations.merge_with(value)

    def only_run_ids(self, ids: Union[str, List[str]]) -> None:
        """
        List of ids of the only jobs to run
        """
        if isinstance(ids, str):
            ids = [ids]
        self.ids_to_run = ids

    def generate_job_specs(self, target_manager: 'TargetManager') -> List[JobSpecProtocol]:
        """
        generate job specifications
        """
        specs: List[JobSpecProtocol] = []
        for leaf in self.root_node.leaves():
            workload_entries = leaf.workload_entries
            sections: List[SectionNode] = [leaf]
            for ancestor in leaf.ancestors():
                workload_entries = ancestor.workload_entries + workload_entries
                sections.insert(0, ancestor)

            for workload_entry in workload_entries:
                job_spec: JobSpecProtocol = create_job_spec(deepcopy(workload_entry), sections,
                                                            target_manager, self.plugin_cache,
                                                            self.disabled_augmentations)
                if self.ids_to_run:
                    for job_id in self.ids_to_run:
                        if job_spec.id and job_id in job_spec.id:
                            break
                    else:
                        continue
                self.update_augmentations(list(cast(JobSpecProtocol, job_spec).augmentations.values()))
                specs.append(job_spec)
        return specs


def create_job_spec(workload_entry: JobSpecSource, sections: List[SectionNode],
                    target_manager: 'TargetManager', plugin_cache: 'PluginCache',
                    disabled_augmentations: Set[str]) -> JobSpecProtocol:
    """
    create the job specification
    """
    job_spec = JobSpec()

    # PHASE 2.1: Merge general job spec configuration
    for section in sections:
        job_spec.update_config(section, check_mandatory=False)

        # Add classifiers for any present groups
        if section.id == 'global' or section.group is None:
            # Ignore global config and default group
            continue
        job_spec.classifiers[section.group] = section.id
    job_spec.update_config(workload_entry, check_mandatory=False)

    # PHASE 2.2: Merge global, section and workload entry "workload_parameters"
    job_spec.merge_workload_parameters(plugin_cache)

    # TODO: PHASE 2.3: Validate device runtime/boot parameters
    job_spec.merge_runtime_parameters(plugin_cache, target_manager)
    target_manager.validate_runtime_parameters(job_spec.runtime_parameters)

    # PHASE 2.4: Disable globally disabled augmentations
    job_spec.set("augmentations", disabled_augmentations)
    job_spec.finalize()

    return cast(JobSpecProtocol, job_spec)


def get_config_point_map(params: List[ConfigurationPoint]) -> Dict[str, ConfigurationPoint]:
    """
    get map of configuration points
    """
    pmap: Dict[str, ConfigurationPoint] = {}
    for p in params:
        pmap[p.name] = p
        for alias in p.aliases:
            pmap[alias] = p
    return pmap


settings = cast(MetaConfigurationProtocol, MetaConfiguration(os.environ))
