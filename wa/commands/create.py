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


import os
import sys
import stat
import shutil
import string
import re
import uuid
import getpass
from collections import OrderedDict

from devlib.utils.types import identifier
try:
    import psycopg2     # type: ignore
    from psycopg2 import connect, OperationalError, extras, _psycopg  # type: ignore
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT      # type: ignore
except ImportError as e:
    psycopg2 = None
    import_error_msg = e.args[0] if e.args else str(e)

from wa import ComplexCommand, SubCommand, pluginloader, settings
from wa.framework.target.descriptor import list_target_descriptions
from wa.framework.exception import ConfigError, CommandError
from wa.instruments.energy_measurement import EnergyInstrumentBackend
from wa.utils.misc import (ensure_directory_exists as _d, capitalize,
                           ensure_file_directory_exists as _f)
from wa.utils.postgres import get_schema, POSTGRES_SCHEMA_DIR
from wa.utils.serializer import yaml
from typing import (Optional, TYPE_CHECKING, cast, OrderedDict as od, Any, IO,
                    Dict, Tuple, Pattern, List, Callable, Type)
from typing_extensions import TypedDict
from argparse import Namespace
from typing_extensions import Required
from uuid import UUID
if TYPE_CHECKING:
    from wa.framework.pluginloader import __LoaderWrapper
    from wa.framework.plugin import Plugin
    from wa.framework.execution import ExecutionContext, ConfigManager
    from wa.framework.target.descriptor import TargetDescriptionProtocol


if sys.version_info >= (3, 8):
    def copy_tree(src, dst):
        from shutil import copy, copytree  # pylint: disable=import-outside-toplevel
        copytree(
            src,
            dst,
            # dirs_exist_ok=True only exists in Python >= 3.8
            dirs_exist_ok=True,
            # Align with devlib and only copy the content without metadata
            copy_function=copy
        )
else:
    def copy_tree(src, dst):
        # pylint: disable=import-outside-toplevel, redefined-outer-name
        from distutils.dir_util import copy_tree
        # Align with devlib and only copy the content without metadata
        copy_tree(src, dst, preserve_mode=False, preserve_times=False)


TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), 'templates')


class PostgresType(TypedDict, total=False):
    host: str
    port: int
    dbname: str
    username: str
    password: str


class CreateDatabaseSubcommand(SubCommand):

    name: str = 'database'
    description: str = """
    Create a Postgresql database which is compatible with the WA Postgres
    output processor.
    """

    schemafilepath: str = os.path.join(POSTGRES_SCHEMA_DIR, 'postgres_schema.sql')
    schemaupdatefilepath: str = os.path.join(POSTGRES_SCHEMA_DIR, 'postgres_schema_update_v{}.{}.sql')

    def __init__(self, *args, **kwargs) -> None:
        super(CreateDatabaseSubcommand, self).__init__(*args, **kwargs)
        self.sql_commands: Optional[str] = None
        self.schema_major: Optional[int] = None
        self.schema_minor: Optional[int] = None
        self.postgres_host: Optional[str] = None
        self.postgres_port: Optional[int] = None
        self.username: Optional[str] = None
        self.password: Optional[str] = None
        self.dbname: Optional[str] = None
        self.config_file: Optional[str] = None
        self.force: Optional[bool] = None

    def initialize(self, context: Optional['ExecutionContext']) -> None:
        self.parser.add_argument(
            '-a', '--postgres-host', default='localhost',
            help='The host on which to create the database.')
        self.parser.add_argument(
            '-k', '--postgres-port', default='5432',
            help='The port on which the PostgreSQL server is running.')
        self.parser.add_argument(
            '-u', '--username', default='postgres',
            help='The username with which to connect to the server.')
        self.parser.add_argument(
            '-p', '--password',
            help='The password for the user account.')
        self.parser.add_argument(
            '-d', '--dbname', default='wa',
            help='The name of the database to create.')
        self.parser.add_argument(
            '-f', '--force', action='store_true',
            help='Force overwrite the existing database if one exists.')
        self.parser.add_argument(
            '-F', '--force-update-config', action='store_true',
            help='Force update the config file if an entry exists.')
        self.parser.add_argument(
            '-r', '--config-file', default=settings.user_config_file,
            help='Path to the config file to be updated.')
        self.parser.add_argument(
            '-x', '--schema-version', action='store_true',
            help='Display the current schema version.')
        self.parser.add_argument(
            '-U', '--upgrade', action='store_true',
            help='Upgrade the database to use the latest schema version.')

    def execute(self, state: 'ConfigManager', args: Namespace) -> None:  # pylint: disable=too-many-branches
        if not psycopg2:
            raise CommandError(
                'The module psycopg2 is required for the wa '
                + 'create database command.')

        if args.dbname == 'postgres':
            raise ValueError('Databasename to create cannot be postgres.')

        self._parse_args(args)
        self.schema_major, self.schema_minor, self.sql_commands = get_schema(self.schemafilepath)

        # Display the version if needed and exit
        if args.schema_version:
            self.logger.info(
                'The current schema version is {}.{}'.format(self.schema_major,
                                                             self.schema_minor))
            return

        if args.upgrade:
            self.update_schema()
            return

        # Open user configuration
        with open(self.config_file or '', 'r') as config_file:
            config: Dict[str, Any] = yaml.load(config_file)
            if 'postgres' in config and not args.force_update_config:
                raise CommandError(
                    "The entry 'postgres' already exists in the config file. "
                    + "Please specify the -F flag to force an update.")

        possible_connection_errors: List[Tuple[Pattern[str], str]] = [
            (
                re.compile('FATAL:  role ".*" does not exist'),
                'Username does not exist or password is incorrect'
            ),
            (
                re.compile('FATAL:  password authentication failed for user'),
                'Password was incorrect'
            ),
            (
                re.compile('fe_sendauth: no password supplied'),
                'Passwordless connection is not enabled. '
                'Please enable trust in pg_hba for this host '
                'or use a password'
            ),
            (
                re.compile('FATAL:  no pg_hba.conf entry for'),
                'Host is not allowed to connect to the specified database '
                'using this user according to pg_hba.conf. Please change the '
                'rules in pg_hba or your connection method'
            ),
            (
                re.compile('FATAL:  pg_hba.conf rejects connection'),
                'Connection was rejected by pg_hba.conf'
            ),
        ]

        def predicate(error: OperationalError, handle: Tuple[Pattern[str], str]) -> None:
            """
            raise appropriate exception
            """
            if handle[0].match(str(error)):
                raise CommandError(handle[1] + ': \n' + str(error))

        # Attempt to create database
        try:
            self.create_database()
        except OperationalError as e:
            for handle in possible_connection_errors:
                predicate(e, handle)
            raise e

        # Update the configuration file
        self._update_configuration_file(config)

    def create_database(self) -> None:
        """
        create postgresql database
        """
        self._validate_version()

        self._check_database_existence()

        self._create_database_postgres()

        self._apply_database_schema(self.sql_commands, self.schema_major, self.schema_minor)

        self.logger.info(
            "Successfully created the database {}".format(self.dbname))

    def update_schema(self) -> None:
        """
        update database schema
        """
        self._validate_version()
        schema_major, schema_minor, _ = get_schema(self.schemafilepath)
        meta_oid, current_major, current_minor = self._get_database_schema_version() or (None, None, None)

        while not (schema_major == current_major and schema_minor == current_minor):
            current_minor = self._update_schema_minors(current_major or 0, current_minor or 0, meta_oid)
            current_major, current_minor = self._update_schema_major(current_major or 0, current_minor, meta_oid)
        msg = "Database schema update of '{}' to v{}.{} complete"
        self.logger.info(msg.format(self.dbname, schema_major, schema_minor))

    def _update_schema_minors(self, major: int, minor: int, meta_oid: Optional[UUID]) -> int:
        """
        update schema minor versions
        """
        # Upgrade all available minor versions
        while True:

            minor += 1

            schema_update = os.path.join(POSTGRES_SCHEMA_DIR,
                                         self.schemaupdatefilepath.format(major, minor))
            if not os.path.exists(schema_update):
                break

            _, _, sql_commands = get_schema(schema_update)
            self._apply_database_schema(sql_commands, major, minor, meta_oid)
            msg: str = "Updated the database schema to v{}.{}"
            self.logger.debug(msg.format(major, minor))

        # Return last existing update file version
        return minor - 1

    def _update_schema_major(self, current_major: int, current_minor: int,
                             meta_oid: Optional[UUID]) -> Tuple[int, int]:
        """
        update schema major versions
        """
        current_major += 1
        schema_update: str = os.path.join(POSTGRES_SCHEMA_DIR,
                                          self.schemaupdatefilepath.format(current_major, 0))
        if not os.path.exists(schema_update):
            return (current_major - 1, current_minor)

        # Reset minor to 0 with major version bump
        current_minor = 0
        _, _, sql_commands = get_schema(schema_update)
        self._apply_database_schema(sql_commands, current_major, current_minor, meta_oid)
        msg = "Updated the database schema to v{}.{}"
        self.logger.debug(msg.format(current_major, current_minor))
        return (current_major, current_minor)

    def _validate_version(self) -> None:
        """
        validate schema version
        """
        conn: _psycopg.connection = connect(user=self.username,
                                            password=self.password, host=self.postgres_host,
                                            port=self.postgres_port)
        if conn.server_version < 90400:
            msg = 'Postgres version too low. Please ensure that you are using atleast v9.4'
            raise CommandError(msg)

    def _get_database_schema_version(self) -> Optional[Tuple[UUID, int, int]]:
        """
        get database schema version
        """
        conn: _psycopg.connection = connect(dbname=self.dbname, user=self.username,
                                            password=self.password, host=self.postgres_host,
                                            port=self.postgres_port)
        cursor: _psycopg.cursor = conn.cursor()
        cursor.execute('''SELECT
                                DatabaseMeta.oid,
                                DatabaseMeta.schema_major,
                                DatabaseMeta.schema_minor
                          FROM
                                DatabaseMeta;''')
        return cursor.fetchone()

    def _check_database_existence(self) -> None:
        """
        check whether database exists
        """
        try:
            connect(dbname=self.dbname, user=self.username,
                    password=self.password, host=self.postgres_host, port=self.postgres_port)
        except OperationalError as e:
            # Expect an operational error (database's non-existence)
            if not re.compile('FATAL:  database ".*" does not exist').match(str(e)):
                raise e
        else:
            if not self.force:
                raise CommandError(
                    "Database {} already exists. ".format(self.dbname)
                    + "Please specify the -f flag to create it from afresh."
                )

    def _create_database_postgres(self) -> None:
        """
        create a postgresql database
        """
        conn: _psycopg.connection = connect(dbname='postgres', user=self.username,
                                            password=self.password, host=self.postgres_host,
                                            port=self.postgres_port)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor: _psycopg.cursor = conn.cursor()
        cursor.execute('DROP DATABASE IF EXISTS ' + (self.dbname or ''))
        cursor.execute('CREATE DATABASE ' + (self.dbname or ''))
        conn.commit()
        cursor.close()
        conn.close()

    def _apply_database_schema(self, sql_commands: Optional[str], schema_major: Optional[int],
                               schema_minor: Optional[int],
                               meta_uuid: Optional[UUID] = None) -> None:
        """
        apply database schema
        """
        conn: _psycopg.connection = connect(dbname=self.dbname, user=self.username,
                                            password=self.password, host=self.postgres_host,
                                            port=self.postgres_port)
        cursor: _psycopg.cursor = conn.cursor()
        if sql_commands:
            cursor.execute(sql_commands)

        if not meta_uuid:
            extras.register_uuid()
            meta_uuid = uuid.uuid4()
            cursor.execute("INSERT INTO DatabaseMeta VALUES (%s, %s, %s)",
                           (meta_uuid,
                            schema_major,
                            schema_minor
                            ))
        else:
            cursor.execute("UPDATE DatabaseMeta SET schema_major = %s, schema_minor = %s WHERE oid = %s;",
                           (schema_major,
                            schema_minor,
                            meta_uuid
                            ))

        conn.commit()
        cursor.close()
        conn.close()

    def _update_configuration_file(self, config: Dict[str, PostgresType]):
        ''' Update the user configuration file with the newly created database's
            configuration.
            '''
        config['postgres'] = cast(PostgresType, OrderedDict(
            [('host', self.postgres_host), ('port', self.postgres_port),
             ('dbname', self.dbname), ('username', self.username), ('password', self.password)]))
        with open(self.config_file or '', 'w+') as config_file:
            yaml.dump(config, config_file)

    def _parse_args(self, args: Namespace) -> None:
        self.postgres_host = args.postgres_host
        self.postgres_port = args.postgres_port
        self.username = args.username
        self.password = args.password
        self.dbname = args.dbname
        self.config_file = args.config_file
        self.force = args.force


class ConfigType(TypedDict, total=False):
    device: str
    device_config: Dict[str, Any]
    augmentations: Required[List[str]]
    energy_measurement: Required[Dict[str, Any]]
    """more keys can be pulled in from loaded plugins"""


class WorkloadEntryType(TypedDict, total=False):
    name: Optional[str]
    label: str
    params: Optional[Dict[str, Any]]


class AgendaType(TypedDict, total=False):
    config: ConfigType
    workloads: List


class CreateAgendaSubcommand(SubCommand):

    name = 'agenda'
    description = """
    Create an agenda with the specified extensions enabled. And parameters set
    to their default values.
    """

    def initialize(self, context: Optional['ExecutionContext']):
        self.parser.add_argument('plugins', nargs='+',
                                 help='Plugins to be added to the agendas')
        self.parser.add_argument('-i', '--iterations', type=int, default=1,
                                 help='Sets the number of iterations for all workloads')
        self.parser.add_argument('-o', '--output', metavar='FILE',
                                 help='Output file. If not specfied, STDOUT will be used instead.')

    # pylint: disable=too-many-branches
    def execute(self, state: 'ConfigManager', args: Namespace) -> None:
        agenda: AgendaType = cast(AgendaType, OrderedDict())
        agenda['config'] = cast(ConfigType, OrderedDict(augmentations=[], iterations=args.iterations))
        agenda['workloads'] = []
        target_desc: Optional['TargetDescriptionProtocol'] = None

        targets: Dict[str, 'TargetDescriptionProtocol'] = {td.name: td for td in list_target_descriptions()}

        for name in args.plugins:
            if name in targets:
                if target_desc is not None:
                    raise ConfigError('Specifying multiple devices: {} and {}'.format(target_desc.name, name))
                target_desc = targets[name]
                agenda['config']['device'] = name
                agenda['config']['device_config'] = target_desc.get_default_config()
                continue

            extcls: Type[Plugin] = cast('__LoaderWrapper', pluginloader).get_plugin_class(name)
            config: Optional[Dict[str, Any]] = cast('__LoaderWrapper', pluginloader).get_default_config(name)

            # Handle special case for EnergyInstrumentBackends
            if issubclass(extcls, EnergyInstrumentBackend):
                if 'energy_measurement' not in agenda['config']['augmentations']:
                    energy_config = cast('__LoaderWrapper', pluginloader).get_default_config('energy_measurement')
                    agenda['config']['augmentations'].append('energy_measurement')
                    agenda['config']['energy_measurement'] = cast(Dict[str, Any], energy_config)
                agenda['config']['energy_measurement']['instrument'] = cast(EnergyInstrumentBackend, extcls).name
                agenda['config']['energy_measurement']['instrument_parameters'] = config
            elif cast(Plugin, extcls).kind == 'workload':
                entry: WorkloadEntryType = cast(WorkloadEntryType, OrderedDict())
                entry['name'] = cast(Plugin, extcls).name
                if name != cast(Plugin, extcls).name:
                    entry['label'] = name
                entry['params'] = config
                agenda['workloads'].append(entry)
            else:
                if cast(Plugin, extcls).kind in ('instrument', 'output_processor'):
                    if cast(Plugin, extcls).name not in agenda['config']['augmentations']:
                        agenda['config']['augmentations'].append(cast(Plugin, extcls).name or '')

                if cast(Plugin, extcls).name not in agenda['config']:
                    # type error saying that the key should be one of those in the typeddict ConfigType
                    # but here it is assigning new keys from loaded plugin. so can be any name.
                    # so ignoring the type error
                    agenda['config'][cast(Plugin, extcls).name or ''] = config   # type:ignore

        if args.output:
            wfh: IO = open(args.output, 'w')
        else:
            wfh = sys.stdout
        yaml.dump(agenda, wfh, indent=4, default_flow_style=False)
        if args.output:
            wfh.close()


class CreateWorkloadSubcommand(SubCommand):

    name: str = 'workload'
    description: str = '''Create a new workload. By default, a basic workload template will be
                     used but you can specify the `KIND` to choose a different template.'''

    def initialize(self, context: Optional['ExecutionContext']) -> None:
        self.parser.add_argument('name', metavar='NAME',
                                 help='Name of the workload to be created')
        self.parser.add_argument('-p', '--path', metavar='PATH', default=None,
                                 help='The location at which the workload will be created. If not specified, '
                                      + 'this defaults to "~/.workload_automation/plugins".')
        self.parser.add_argument('-f', '--force', action='store_true',
                                 help='Create the new workload even if a workload with the specified '
                                      + 'name already exists.')
        self.parser.add_argument('-k', '--kind', metavar='KIND', default='basic', choices=list(create_funcs.keys()),
                                 help='The type of workload to be created. The available options '
                                      + 'are: {}'.format(', '.join(list(create_funcs.keys()))))

    def execute(self, state: 'ConfigManager', args: Namespace) -> None:  # pylint: disable=R0201
        where: str = args.path or 'local'
        check_name: bool = not args.force

        try:
            create_workload(args.name, args.kind, where, check_name)
        except CommandError as e:
            self.logger.error('ERROR: {}'.format(e))


class CreatePackageSubcommand(SubCommand):

    name: str = 'package'
    description: str = '''Create a new empty Python package for WA extensions. On installation,
                     this package will "advertise" itself to WA so that Plugins within it will
                     be loaded by WA when it runs.'''

    def initialize(self, context: Optional['ExecutionContext']) -> None:
        self.parser.add_argument('name', metavar='NAME',
                                 help='Name of the package to be created')
        self.parser.add_argument('-p', '--path', metavar='PATH', default=None,
                                 help='The location at which the new package will be created. If not specified, '
                                      + 'current working directory will be used.')
        self.parser.add_argument('-f', '--force', action='store_true',
                                 help='Create the new package even if a file or directory with the same name '
                                      'already exists at the specified location.')

    def execute(self, state: 'ConfigManager', args: Namespace) -> None:  # pylint: disable=R0201
        package_dir: str = args.path or os.path.abspath('.')
        template_path: str = os.path.join(TEMPLATES_DIR, 'setup.template')
        self.create_extensions_package(package_dir, args.name, template_path, args.force)

    def create_extensions_package(self, location: str, name: str, setup_template_path: str,
                                  overwrite: bool = False) -> None:
        """
        create extensions package
        """
        package_path: str = os.path.join(location, name)
        if os.path.exists(package_path):
            if overwrite:
                self.logger.info('overwriting existing "{}"'.format(package_path))
                shutil.rmtree(package_path)
            else:
                raise CommandError('Location "{}" already exists.'.format(package_path))
        actual_package_path: str = os.path.join(package_path, name)
        os.makedirs(actual_package_path)
        setup_text: str = render_template(setup_template_path, {'package_name': name, 'user': getpass.getuser()})
        with open(os.path.join(package_path, 'setup.py'), 'w') as wfh:
            wfh.write(setup_text)
        touch(os.path.join(actual_package_path, '__init__.py'))


class CreateCommand(ComplexCommand):

    name: str = 'create'
    description: str = '''
    Used to create various WA-related objects (see positional arguments list
    for what objects may be created).\n\nUse "wa create <object> -h" for
    object-specific arguments.
    '''
    subcmd_classes = [
        CreateDatabaseSubcommand,
        CreateWorkloadSubcommand,
        CreateAgendaSubcommand,
        CreatePackageSubcommand,
    ]


def create_workload(name: str, kind: str = 'basic', where: str = 'local',
                    check_name: bool = True, **kwargs) -> None:
    """
    create workload
    """

    if check_name:
        if name in [wl.name for wl in cast('__LoaderWrapper', pluginloader).list_plugins('workload')]:
            raise CommandError('Workload with name "{}" already exists.'.format(name))

    class_name: str = get_class_name(name)
    if where == 'local':
        workload_dir: str = _d(os.path.join(settings.plugins_directory, name))
    else:
        workload_dir = _d(os.path.join(where, name))

    try:
        # Note: `create_funcs` mapping is listed below
        create_funcs[kind](workload_dir, name, kind, class_name, **kwargs)
    except KeyError:
        raise CommandError('Unknown workload type: {}'.format(kind))

    # pylint: disable=superfluous-parens
    print('Workload created in {}'.format(workload_dir))


def create_template_workload(path: str, name: str, kind: str,
                             class_name: str) -> None:
    """
    create template workload
    """
    source_file: str = os.path.join(path, '__init__.py')
    with open(source_file, 'w') as wfh:
        wfh.write(render_template('{}_workload'.format(kind), {'name': name, 'class_name': class_name}))


def create_uiautomator_template_workload(path: str, name: str, kind: str,
                                         class_name: str) -> None:
    """
    create ui automator template workload
    """
    uiauto_path: str = os.path.join(path, 'uiauto')
    create_uiauto_project(uiauto_path, name)
    create_template_workload(path, name, kind, class_name)


def create_uiauto_project(path: str, name: str) -> None:
    """
    create ui automator project
    """
    package_name: str = 'com.arm.wa.uiauto.' + name.lower()

    copy_tree(os.path.join(TEMPLATES_DIR, 'uiauto', 'uiauto_workload_template'), path)

    manifest_path: str = os.path.join(path, 'app', 'src', 'main')
    mainifest: str = os.path.join(_d(manifest_path), 'AndroidManifest.xml')
    with open(mainifest, 'w') as wfh:
        wfh.write(render_template(os.path.join('uiauto', 'uiauto_AndroidManifest.xml'),
                                  {'package_name': package_name}))

    build_gradle_path: str = os.path.join(path, 'app')
    build_gradle: str = os.path.join(_d(build_gradle_path), 'build.gradle')
    with open(build_gradle, 'w') as wfh:
        wfh.write(render_template(os.path.join('uiauto', 'uiauto_build.gradle'),
                                  {'package_name': package_name}))

    build_script: str = os.path.join(path, 'build.sh')
    with open(build_script, 'w') as wfh:
        wfh.write(render_template(os.path.join('uiauto', 'uiauto_build_script'),
                                  {'package_name': package_name}))
    os.chmod(build_script, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

    source_file: str = _f(os.path.join(path, 'app', 'src', 'main', 'java',
                                       os.sep.join(package_name.split('.')[:-1]),
                                       'UiAutomation.java'))
    with open(source_file, 'w') as wfh:
        wfh.write(render_template(os.path.join('uiauto', 'UiAutomation.java'),
                                  {'name': name, 'package_name': package_name}))


# Mapping of workload types to their corresponding creation method
create_funcs: Dict[str, Callable[[str, str, str, str], None]] = {
    'basic': create_template_workload,
    'apk': create_template_workload,
    'revent': create_template_workload,
    'apkrevent': create_template_workload,
    'uiauto': create_uiautomator_template_workload,
    'apkuiauto': create_uiautomator_template_workload,
}


# Utility functions
def render_template(name: str, params: Dict[str, Any]) -> str:
    """
    render template
    """
    filepath: str = os.path.join(TEMPLATES_DIR, name)
    with open(filepath) as fh:
        text: str = fh.read()
        template = string.Template(text)
        return template.substitute(params)


def get_class_name(name: str, postfix='') -> str:
    """
    get class name
    """
    name = identifier(name)
    return ''.join(map(capitalize, name.split('_'))) + postfix


def touch(path: str):
    """
    clear file contents
    """
    with open(path, 'w') as _: # NOQA
        pass
