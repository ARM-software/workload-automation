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

try:
    import psycopg2  # type:ignore
    from psycopg2 import Error as Psycopg2Error  # type:ignore
    from psycopg2 import _psycopg   # type:ignore
except ImportError:
    psycopg2 = None
    Psycopg2Error = None

import logging
import os
import shutil
import tarfile
import tempfile
from collections import OrderedDict, defaultdict
from copy import copy, deepcopy
from datetime import datetime
from io import StringIO

import devlib

from wa.framework.configuration.core import (JobSpec, JobSpecProtocol, Status,
                                             RunConfigurationProtocol, MetaConfigurationProtocol)
from wa.framework.configuration.execution import CombinedConfig, ConfigManager
from wa.framework.exception import HostError, SerializerSyntaxError, ConfigError
from wa.framework.run import RunState, RunInfo
from wa.framework.target.info import TargetInfo
from wa.framework.version import get_wa_version_with_commit
from wa.utils.doc import format_simple_table
from wa.utils.misc import (touch, ensure_directory_exists, isiterable,
                           format_ordered_dict, safe_extract)
from wa.utils.postgres import get_schema_versions
from wa.utils.serializer import write_pod, read_pod, Podable, json
from wa.utils.types import enum, numeric
from uuid import UUID
from typing import (Optional, List, cast, Dict, Any, TYPE_CHECKING, Set,
                    Union, Generator, Tuple, DefaultDict)
if TYPE_CHECKING:
    from wa.framework.configuration.core import StatusType
    from wa.framework.job import Job


logger: logging.Logger = logging.getLogger('output')


class Output(object):
    """
    base class for run output and job output
    """
    kind: Optional[str] = None

    @property
    def resultfile(self) -> str:
        """
        result file
        """
        return os.path.join(self.basepath, 'result.json')

    @property
    def event_summary(self) -> str:
        """
        event summary
        """
        num_events: int = len(self.events)
        if num_events:
            lines: List[str] = self.events[0].message.split('\n')
            message: str = '({} event(s)): {}'
            if num_events > 1 or len(lines) > 1:
                message += '[...]'
            return message.format(num_events, lines[0])
        return ''

    @property
    def status(self) -> Optional['StatusType']:
        """
        output status
        """
        if self.result is None:
            return None
        return self.result.status

    @status.setter
    def status(self, value: 'StatusType') -> None:
        """
        output status setter
        """
        if self.result:
            self.result.status = value

    @property
    def metrics(self) -> List['Metric']:
        """
        list of metrics
        """
        if self.result is None:
            return []
        return self.result.metrics

    @property
    def artifacts(self) -> List['Artifact']:
        """
        list of artifacts
        """
        if self.result is None:
            return []
        return self.result.artifacts

    @property
    def classifiers(self) -> OrderedDict:
        """
        dict of classifiers
        """
        if self.result is None:
            return OrderedDict()
        return self.result.classifiers

    @classifiers.setter
    def classifiers(self, value: OrderedDict) -> None:
        """
        classifiers setter
        """
        if self.result is None:
            msg = 'Attempting to set classifiers before output has been set'
            raise RuntimeError(msg)
        self.result.classifiers = value

    @property
    def events(self) -> List['Event']:
        """
        list of events
        """
        if self.result is None:
            return []
        return self.result.events

    @property
    def metadata(self) -> OrderedDict:
        """
        output metadata
        """
        if self.result is None:
            return cast(OrderedDict, {})
        return self.result.metadata

    def __init__(self, path: str):
        self.basepath = path
        self.result: Optional[Result] = None

    def reload(self) -> None:
        """
        reload result
        """
        try:
            if os.path.isdir(self.basepath):
                pod = read_pod(self.resultfile)
                self.result = Result.from_pod(pod)
            else:
                self.result = Result()
                self.result.status = Status.PENDING
        except Exception as e:  # pylint: disable=broad-except
            self.result = Result()
            self.result.status = Status.UNKNOWN
            self.add_event(str(e))

    def write_result(self) -> None:
        """
        write result
        """
        if self.result:
            write_pod(self.result.to_pod(), self.resultfile)

    def get_path(self, subpath: str) -> str:
        """
        get path from subpath
        """
        return os.path.join(self.basepath, subpath.strip(os.sep))

    def add_metric(self, name: str, value: Any,
                   units: Optional[str] = None, lower_is_better: bool = False,
                   classifiers: Optional[Dict[str, Any]] = None) -> None:
        """
        add metric to workload execution result
        """
        if self.result:
            self.result.add_metric(name, value, units, lower_is_better, classifiers)

    def add_artifact(self, name: str, path: str, kind: str, description: Optional[str] = None,
                     classifiers: Optional[Dict[str, Any]] = None):
        """
        add artifact to workload execution result
        """
        if not os.path.exists(path):
            path = self.get_path(path)
        if not os.path.exists(path):
            msg = 'Attempting to add non-existing artifact: {}'
            raise HostError(msg.format(path))
        is_dir: bool = os.path.isdir(path)
        path = os.path.relpath(path, self.basepath)
        if self.result:
            self.result.add_artifact(name, path, kind, description, classifiers, is_dir)

    def add_event(self, message: str) -> None:
        """
        add event
        """
        if self.result:
            self.result.add_event(message)

    def get_metric(self, name: str) -> Optional['Metric']:
        """
        get metric
        """
        if self.result:
            return self.result.get_metric(name)
        return None

    def get_artifact(self, name: str) -> Optional['Artifact']:
        """
        get the specified artifact from workload execution result
        """
        if self.result:
            return self.result.get_artifact(name)
        return None

    def get_artifact_path(self, name: str) -> str:
        """
        get path to the specified artifact
        """
        artifact = self.get_artifact(name)
        return self.get_path(artifact.path if artifact else '')

    def add_classifier(self, name: str, value: Any, overwrite: bool = False) -> None:
        """
        add classifier to workload execution result
        """
        if self.result:
            self.result.add_classifier(name, value, overwrite)

    def add_metadata(self, key: str, *args, **kwargs) -> None:
        """
        add metadata to workload execution result
        """
        if self.result:
            self.result.add_metadata(key, *args, **kwargs)

    def update_metadata(self, key: str, *args) -> None:
        """
        update an existing metadata in workload execution result
        """
        if self.result:
            self.result.update_metadata(key, *args)

    def __repr__(self):
        return '<{} {}>'.format(self.__class__.__name__,
                                os.path.basename(self.basepath))

    def __str__(self):
        return os.path.basename(self.basepath)


class RunOutputCommon(object):
    ''' Split out common functionality to form a second base of
        the RunOutput classes
    '''
    @property
    def run_config(self) -> Optional[RunConfigurationProtocol]:
        """
        get run configuration
        """
        if cast('RunOutput', self)._combined_config:
            return cast(CombinedConfig, cast('RunOutput', self)._combined_config).run_config
        return None

    @property
    def settings(self) -> Optional[MetaConfigurationProtocol]:
        """
        metadata configurations of the run
        """
        if cast('RunOutput', self)._combined_config:
            return cast(CombinedConfig, cast('RunOutput', self)._combined_config).settings
        return None

    def get_job_spec(self, spec_id: str) -> Optional[JobSpecProtocol]:
        """
        get the job specifications
        """
        for spec in cast('RunOutput', self).job_specs:
            if spec.id == spec_id:
                return spec
        return None

    def list_workloads(self) -> List[str]:
        """
        list the workloads
        """
        workloads: List[str] = []
        for job in cast('RunOutput', self).jobs:
            if job.label not in workloads:
                workloads.append(job.label)
        return workloads


class RunOutput(Output, RunOutputCommon):

    kind: Optional[str] = 'run'

    @property
    def logfile(self) -> str:
        """
        log file path
        """
        return os.path.join(self.basepath, 'run.log')

    @property
    def metadir(self) -> str:
        """
        metadata directory
        """
        return os.path.join(self.basepath, '__meta')

    @property
    def infofile(self) -> str:
        """
        run info file
        """
        return os.path.join(self.metadir, 'run_info.json')

    @property
    def statefile(self) -> str:
        """
        run state file
        """
        return os.path.join(self.basepath, '.run_state.json')

    @property
    def configfile(self) -> str:
        """
        configuration file
        """
        return os.path.join(self.metadir, 'config.json')

    @property
    def targetfile(self) -> str:
        """
        target information file
        """
        return os.path.join(self.metadir, 'target_info.json')

    @property
    def jobsfile(self) -> str:
        """
        jobs file
        """
        return os.path.join(self.metadir, 'jobs.json')

    @property
    def raw_config_dir(self) -> str:
        """
        raw configuration file
        """
        return os.path.join(self.metadir, 'raw_config')

    @property
    def failed_dir(self) -> str:
        """
        failed info file
        """
        path = os.path.join(self.basepath, '__failed')
        return ensure_directory_exists(path)

    @property
    def augmentations(self) -> List:
        """
        augmentations on the run
        """
        run_augs: Set = set([])
        for job in self.jobs:
            for aug in cast(JobSpecProtocol, job.spec).augmentations:
                run_augs.add(aug)
        return list(run_augs)

    def __init__(self, path: str):
        super(RunOutput, self).__init__(path)
        self.info: Optional[RunInfo] = None
        self.state: Optional[RunState] = None
        self.result: Optional['Result'] = None
        self.target_info: Optional['TargetInfo'] = None
        self._combined_config: Optional[CombinedConfig] = None
        self.jobs: List[JobOutput] = []
        self.job_specs: List[JobSpecProtocol] = []
        if (not os.path.isfile(self.statefile)
                or not os.path.isfile(self.infofile)):
            msg: str = '"{}" does not exist or is not a valid WA output directory.'
            raise ValueError(msg.format(self.basepath))
        self.reload()

    def reload(self) -> None:
        super(RunOutput, self).reload()
        self.info = RunInfo.from_pod(read_pod(self.infofile))
        self.state = RunState.from_pod(read_pod(self.statefile))
        if os.path.isfile(self.configfile):
            self._combined_config = CombinedConfig.from_pod(read_pod(self.configfile))
        if os.path.isfile(self.targetfile):
            self.target_info = TargetInfo.from_pod(read_pod(self.targetfile))
        if os.path.isfile(self.jobsfile):
            self.job_specs = self.read_job_specs() or []

        for job_state in self.state.jobs.values():
            job_path: str = os.path.join(self.basepath, job_state.output_name)
            job = JobOutput(job_path, job_state.id,
                            job_state.label, job_state.iteration,
                            job_state.retries)
            job.status = job_state.status
            job.spec = self.get_job_spec(job.id)
            if job.spec is None:
                logger.warning('Could not find spec for job {}'.format(job.id))
            self.jobs.append(job)

    def write_info(self) -> None:
        """
        write run info to infofile
        """
        if self.info:
            write_pod(self.info.to_pod(), self.infofile)

    def write_state(self) -> None:
        """
        write run state into statefile
        """
        if self.state:
            write_pod(self.state.to_pod(), self.statefile)

    def write_config(self, config: CombinedConfig) -> None:
        """
        write config into config file
        """
        self._combined_config = config
        write_pod(config.to_pod(), self.configfile)

    def read_config(self) -> Optional[CombinedConfig]:
        """
        read combined config file
        """
        if not os.path.isfile(self.configfile):
            return None
        return CombinedConfig.from_pod(read_pod(self.configfile))

    def set_target_info(self, ti: TargetInfo) -> None:
        """
        set target info
        """
        self.target_info = ti
        write_pod(ti.to_pod(), self.targetfile)

    def write_job_specs(self, job_specs: List[JobSpecProtocol]) -> None:
        """
        write job specifications
        """
        job_specs[0].to_pod()
        js_pod = {'jobs': [js.to_pod() for js in job_specs]}
        write_pod(js_pod, self.jobsfile)

    def read_job_specs(self) -> Optional[List[JobSpecProtocol]]:
        """
        read job specifications
        """
        if not os.path.isfile(self.jobsfile):
            return None
        pod = read_pod(self.jobsfile)
        return cast(List[JobSpecProtocol], [JobSpec.from_pod(jp) for jp in pod['jobs']])

    def move_failed(self, job_output: 'JobOutput') -> None:
        """
        move output of failed jobs to failed file
        """
        name: str = os.path.basename(job_output.basepath)
        attempt: int = job_output.retry + 1
        failed_name: str = '{}-attempt{:02}'.format(name, attempt)
        failed_path: str = os.path.join(self.failed_dir, failed_name)
        if os.path.exists(failed_path):
            raise ValueError('Path {} already exists'.format(failed_path))
        shutil.move(job_output.basepath, failed_path)
        job_output.basepath = failed_path


class JobOutput(Output):

    kind = 'job'

    # pylint: disable=redefined-builtin
    def __init__(self, path: str, id: str, label: str, iteration: int, retry: int):
        super(JobOutput, self).__init__(path)
        self.id = id
        self.label = label
        self.iteration = iteration
        self.retry = retry
        self.result: Optional['Result'] = None
        self.spec: Optional[JobSpecProtocol] = None
        self.reload()

    @property
    def augmentations(self) -> List:
        """
        list of augmentations
        """
        job_augs = set([])
        if self.spec:
            for aug in self.spec.augmentations:
                job_augs.add(aug)
        return list(job_augs)


class Result(Podable):

    _pod_serialization_version: int = 1

    @staticmethod
    def from_pod(pod) -> 'Result':
        instance = cast('Result', super(Result, Result).from_pod(pod))
        instance.status = Status.from_pod(pod['status'])
        instance.metrics = [Metric.from_pod(m) for m in pod['metrics']]
        instance.artifacts = [Artifact.from_pod(a) for a in pod['artifacts']]
        instance.events = [Event.from_pod(e) for e in pod['events']]
        instance.classifiers = pod.get('classifiers', OrderedDict())
        instance.metadata = pod.get('metadata', OrderedDict())
        return instance

    def __init__(self) -> None:
        # pylint: disable=no-member
        super(Result, self).__init__()
        self.status: 'StatusType' = Status.NEW
        self.metrics: List['Metric'] = []
        self.artifacts: List['Artifact'] = []
        self.events: List['Event'] = []
        self.classifiers: OrderedDict = OrderedDict()
        self.metadata: OrderedDict = OrderedDict()

    def add_metric(self, name: str, value: Any,
                   units: Optional[str] = None, lower_is_better: bool = False,
                   classifiers: Optional[Dict[str, Any]] = None) -> None:
        """
        add a metric to the workload execution result
        """
        metric = Metric(name, value, units, lower_is_better, classifiers)
        logger.debug('Adding metric: {}'.format(metric))
        self.metrics.append(metric)

    def add_artifact(self, name: str, path: str, kind: str,
                     description: Optional[str] = None,
                     classifiers: Optional[Dict[str, Any]] = None,
                     is_dir: bool = False) -> None:
        """
        add artifact to the workload execution result
        """
        artifact = Artifact(name, path, kind, description=description,
                            classifiers=classifiers, is_dir=is_dir)
        logger.debug('Adding artifact: {}'.format(artifact))
        self.artifacts.append(artifact)

    def add_event(self, message: str):
        """
        add new event with the message into result
        """
        self.events.append(Event(message))

    def get_metric(self, name: str) -> Optional['Metric']:
        """
        get the specified metric from workload execution result
        """
        for metric in self.metrics:
            if metric.name == name:
                return metric
        return None

    def get_artifact(self, name: str) -> Optional['Artifact']:
        """
        get the specified artifact from workload execution result
        """
        for artifact in self.artifacts:
            if artifact.name == name:
                return artifact
        raise HostError('Artifact "{}" not found'.format(name))

    def add_classifier(self, name: str, value: Any,
                       overwrite: bool = False) -> None:
        """
        add classifier to the workload execution result and update the metrics and artifacts
        """
        if name in self.classifiers and not overwrite:
            raise ValueError('Cannot overwrite "{}" classifier.'.format(name))
        self.classifiers[name] = value

        for metric in self.metrics:
            if name in metric.classifiers and not overwrite:
                raise ValueError('Cannot overwrite "{}" classifier; clashes with {}.'.format(name, metric))
            metric.classifiers[name] = value

        for artifact in self.artifacts:
            if name in artifact.classifiers and not overwrite:
                raise ValueError('Cannot overwrite "{}" classifier; clashes with {}.'.format(name, artifact))
            artifact.classifiers[name] = value

    def add_metadata(self, key: str, *args, **kwargs) -> None:
        """
        add metadata to workload execution result
        """
        force: bool = kwargs.pop('force', False)
        if kwargs:
            msg: str = 'Unexpected keyword arguments: {}'
            raise ValueError(msg.format(kwargs))

        if key in self.metadata and not force:
            msg = 'Metadata with key "{}" already exists.'
            raise ValueError(msg.format(key))

        if len(args) == 1:
            value = args[0]
        elif len(args) == 2:
            value = {args[0]: args[1]}
        elif not args:
            value = None
        else:
            raise ValueError("Unexpected arguments: {}".format(args))

        self.metadata[key] = value

    def update_metadata(self, key: str, *args) -> None:
        """
        update an existing metadata in workload execution output
        """
        if not args or len(args) == 0:
            del self.metadata[key]
            return

        if key not in self.metadata:
            return self.add_metadata(key, *args)

        if hasattr(self.metadata[key], 'items'):
            if len(args) == 2:
                self.metadata[key][args[0]] = args[1]
            elif len(args) > 2:  # assume list of key-value pairs
                for k, v in args:
                    self.metadata[key][k] = v
            elif hasattr(args[0], 'items'):
                for k, v in args[0].items():
                    self.metadata[key][k] = v
            else:
                raise ValueError('Invalid value for key "{}": {}'.format(key, args))

        elif isiterable(self.metadata[key]):
            self.metadata[key].extend(args)
        else:   # scalar
            if len(args) > 1:
                raise ValueError('Invalid value for key "{}": {}'.format(key, args))
            self.metadata[key] = args[0]

    def to_pod(self):
        pod = super(Result, self).to_pod()
        pod['status'] = self.status.to_pod()
        pod['metrics'] = [m.to_pod() for m in self.metrics]
        pod['artifacts'] = [a.to_pod() for a in self.artifacts]
        pod['events'] = [e.to_pod() for e in self.events]
        pod['classifiers'] = copy(self.classifiers)
        pod['metadata'] = deepcopy(self.metadata)
        return pod

    @staticmethod
    def _pod_upgrade_v1(pod):
        pod['_pod_version'] = pod.get('_pod_version', 1)
        pod['status'] = Status(pod['status']).to_pod()
        return pod


ARTIFACT_TYPES: List[str] = ['log', 'meta', 'data', 'export', 'raw']
ArtifactType = enum(ARTIFACT_TYPES)


class Artifact(Podable):
    """
    This is an artifact generated during execution/post-processing of a
    workload.  Unlike metrics, this represents an actual artifact, such as a
    file, generated.  This may be "output", such as trace, or it could be "meta
    data" such as logs.  These are distinguished using the ``kind`` attribute,
    which also helps WA decide how it should be handled. Currently supported
    kinds are:

        :log: A log file. Not part of the "output" as such but contains
              information about the run/workload execution that be useful for
              diagnostics/meta analysis.
        :meta: A file containing metadata. This is not part of the "output", but
               contains information that may be necessary to reproduce the
               results (contrast with ``log`` artifacts which are *not*
               necessary).
        :data: This file contains new data, not available otherwise and should
               be considered part of the "output" generated by WA. Most traces
               would fall into this category.
        :export: Exported version of results or some other artifact. This
                 signifies that this artifact does not contain any new data
                 that is not available elsewhere and that it may be safely
                 discarded without losing information.
        :raw: Signifies that this is a raw dump/log that is normally processed
              to extract useful information and is then discarded. In a sense,
              it is the opposite of ``export``, but in general may also be
              discarded.

              .. note:: whether a file is marked as ``log``/``data`` or ``raw``
                        depends on how important it is to preserve this file,
                        e.g. when archiving, vs how much space it takes up.
                        Unlike ``export`` artifacts which are (almost) always
                        ignored by other exporters as that would never result
                        in data loss, ``raw`` files *may* be processed by
                        exporters if they decided that the risk of losing
                        potentially (though unlikely) useful data is greater
                        than the time/space cost of handling the artifact (e.g.
                        a database uploader may choose to ignore ``raw``
                        artifacts, where as a network filer archiver may choose
                        to archive them).

        .. note: The kind parameter is intended to represent the logical
                 function of a particular artifact, not it's intended means of
                 processing -- this is left entirely up to the output
                 processors.

    """

    _pod_serialization_version: int = 2

    @staticmethod
    def from_pod(pod) -> 'Artifact':
        pod = Artifact._upgrade_pod(pod)
        pod_version: int = pod.pop('_pod_version')
        pod['kind'] = ArtifactType(pod['kind'])
        instance = Artifact(**pod)
        instance._pod_version = pod_version  # pylint: disable =protected-access
        instance.is_dir = pod.pop('is_dir')
        return instance

    def __init__(self, name: str, path: str, kind: str,
                 description: Optional[str] = None,
                 classifiers: Optional[Dict[str, Any]] = None,
                 is_dir: bool = False):
        """"
        :param name: Name that uniquely identifies this artifact.
        :param path: The *relative* path of the artifact. Depending on the
                     ``level`` must be either relative to the run or iteration
                     output directory.  Note: this path *must* be delimited
                     using ``/`` irrespective of the
                     operating system.
        :param kind: The type of the artifact this is (e.g. log file, result,
                     etc.) this will be used as a hint to output processors. This
                     must be one of ``'log'``, ``'meta'``, ``'data'``,
                     ``'export'``, ``'raw'``.
        :param description: A free-form description of what this artifact is.
        :param classifiers: A set of key-value pairs to further classify this
                            metric beyond current iteration (e.g. this can be
                            used to identify sub-tests).
        """
        super(Artifact, self).__init__()
        self.name = name
        self.path = path.replace('/', os.sep) if path is not None else path
        try:
            self.kind = ArtifactType(kind)
        except ValueError:
            msg: str = 'Invalid Artifact kind: {}; must be in {}'
            raise ValueError(msg.format(kind, ARTIFACT_TYPES))
        self.description = description
        self.classifiers = classifiers or {}
        self.is_dir = is_dir

    def to_pod(self) -> Dict[str, Any]:
        pod = super(Artifact, self).to_pod()
        pod.update(self.__dict__)
        pod['kind'] = str(self.kind)
        pod['is_dir'] = self.is_dir
        return pod

    @staticmethod
    def _pod_upgrade_v1(pod: Dict[str, Any]) -> Dict[str, Any]:
        """
        pod upgrade function version 1
        """
        pod['_pod_version'] = pod.get('_pod_version', 1)
        return pod

    @staticmethod
    def _pod_upgrade_v2(pod: Dict[str, Any]) -> Dict[str, Any]:
        """
        pod upgrade function version 2
        """
        pod['is_dir'] = pod.get('is_dir', False)
        return pod

    def __str__(self):
        return self.path

    def __repr__(self):
        ft = 'dir' if self.is_dir else 'file'
        return '{} ({}) ({}): {}'.format(self.name, ft, self.kind, self.path)


class Metric(Podable):
    """
    This is a single metric collected from executing a workload.

    :param name: the name of the metric. Uniquely identifies the metric
                 within the results.
    :param value: The numerical value of the metric for this execution of a
                  workload. This can be either an int or a float.
    :param units: Units for the collected value. Can be None if the value
                  has no units (e.g. it's a count or a standardised score).
    :param lower_is_better: Boolean flag indicating where lower values are
                            better than higher ones. Defaults to False.
    :param classifiers: A set of key-value pairs to further classify this
                        metric beyond current iteration (e.g. this can be used
                        to identify sub-tests).

    """
    __slots__: List[str] = ['name', 'value', 'units', 'lower_is_better', 'classifiers']
    _pod_serialization_version: int = 1

    @staticmethod
    def from_pod(pod) -> 'Metric':
        pod = Metric._upgrade_pod(pod)
        pod_version: int = pod.pop('_pod_version')
        instance = Metric(**pod)
        instance._pod_version = pod_version  # pylint: disable =protected-access
        return instance

    @property
    def label(self) -> str:
        """
        label of the metric
        """
        parts = ['{}={}'.format(n, v) for n, v in self.classifiers.items()]
        parts.insert(0, self.name)
        return '/'.join(parts)

    def __init__(self, name: str, value: Any, units: Optional[str] = None,
                 lower_is_better: bool = False,
                 classifiers: Optional[Dict[str, Any]] = None):
        super(Metric, self).__init__()
        self.name = name
        self.value: Union[int, float] = numeric(value)
        self.units = units
        self.lower_is_better = lower_is_better
        self.classifiers = classifiers or {}

    def to_pod(self) -> Dict[str, Any]:
        pod = super(Metric, self).to_pod()
        pod['name'] = self.name
        pod['value'] = self.value
        pod['units'] = self.units
        pod['lower_is_better'] = self.lower_is_better
        pod['classifiers'] = self.classifiers
        return pod

    @staticmethod
    def _pod_upgrade_v1(pod: Dict[str, Any]) -> Dict[str, Any]:
        """
        pod upgrade function version 1
        """
        pod['_pod_version'] = pod.get('_pod_version', 1)
        return pod

    def __str__(self) -> str:
        result: str = '{}: {}'.format(self.name, self.value)
        if self.units:
            result += ' ' + self.units
        result += ' ({})'.format('-' if self.lower_is_better else '+')
        return result

    def __repr__(self) -> str:
        text: str = self.__str__()
        if self.classifiers:
            return '<{} {}>'.format(text, format_ordered_dict(self.classifiers))
        else:
            return '<{}>'.format(text)


class Event(Podable):
    """
    An event that occured during a run.
    """

    __slots__: List[str] = ['timestamp', 'message']
    _pod_serialization_version: int = 1

    @staticmethod
    def from_pod(pod) -> 'Event':
        pod = Event._upgrade_pod(pod)
        pod_version: int = pod.pop('_pod_version')
        instance = Event(pod['message'])
        instance.timestamp = pod['timestamp']
        instance._pod_version = pod_version  # pylint: disable =protected-access
        return instance

    @property
    def summary(self) -> str:
        """
        summary of the event
        """
        lines: List[str] = self.message.split('\n')
        result: str = lines[0]
        if len(lines) > 1:
            result += '[...]'
        return result

    def __init__(self, message: str):
        super(Event, self).__init__()
        self.timestamp: datetime = datetime.utcnow()
        self.message = str(message)

    def to_pod(self) -> Dict[str, Any]:
        pod = super(Event, self).to_pod()
        pod['timestamp'] = self.timestamp
        pod['message'] = self.message
        return pod

    @staticmethod
    def _pod_upgrade_v1(pod: Dict[str, Any]) -> Dict[str, Any]:
        """
        pod upgrade function version 1
        """
        pod['_pod_version'] = pod.get('_pod_version', 1)
        return pod

    def __str__(self):
        return '[{}] {}'.format(self.timestamp, self.message)

    __repr__ = __str__


def init_run_output(path: str, wa_state: ConfigManager,
                    force: bool = False) -> RunOutput:
    """
    initialize run output
    """
    if os.path.exists(path):
        if force:
            logger.info('Removing existing output directory.')
            shutil.rmtree(os.path.abspath(path))
        else:
            raise RuntimeError('path exists: {}'.format(path))

    logger.info('Creating output directory.')
    os.makedirs(path)
    meta_dir: str = os.path.join(path, '__meta')
    os.makedirs(meta_dir)
    _save_raw_config(meta_dir, wa_state)
    touch(os.path.join(path, 'run.log'))

    info = RunInfo(
        run_name=wa_state.run_config.run_name,
        project=wa_state.run_config.project,
        project_stage=wa_state.run_config.project_stage or '',
    )
    write_pod(info.to_pod(), os.path.join(meta_dir, 'run_info.json'))
    write_pod(RunState().to_pod(), os.path.join(path, '.run_state.json'))
    write_pod(Result().to_pod(), os.path.join(path, 'result.json'))

    ro = RunOutput(path)
    ro.update_metadata('versions', 'wa', get_wa_version_with_commit())
    ro.update_metadata('versions', 'devlib', devlib.__full_version__)

    return ro


def init_job_output(run_output: RunOutput, job: 'Job') -> JobOutput:
    """
    initialize job output
    """
    output_name: str = '{}-{}-{}'.format(job.id, job.spec.label, job.iteration)
    path: str = os.path.join(run_output.basepath, output_name)
    ensure_directory_exists(path)
    write_pod(Result().to_pod(), os.path.join(path, 'result.json'))
    job_output = JobOutput(path, job.id or '', job.label, job.iteration, job.retries)
    job_output.spec = job.spec
    job_output.status = job.status
    run_output.jobs.append(job_output)
    return job_output


def discover_wa_outputs(path: str) -> Generator[RunOutput, Any, None]:
    """
    discover workload automation outputs
    """
    # Use topdown=True to allow pruning dirs
    for root, dirs, _ in os.walk(path, topdown=True):
        if '__meta' in dirs:
            yield RunOutput(root)
            # Avoid recursing into the artifact as it can be very lengthy if a
            # large number of file is present (sysfs dump)
            dirs.clear()


def _save_raw_config(meta_dir: str, state: 'ConfigManager') -> None:
    """
    save raw configuration
    """
    raw_config_dir: str = os.path.join(meta_dir, 'raw_config')
    os.makedirs(raw_config_dir)

    for i, source in enumerate(state.loaded_config_sources):
        if not os.path.isfile(source):
            continue
        basename: str = os.path.basename(source)
        dest_path: str = os.path.join(raw_config_dir, 'cfg{}-{}'.format(i, basename))
        shutil.copy(source, dest_path)


class DatabaseOutput(Output):

    kind: Optional[str] = None

    @property
    def resultfile(self) -> Optional[Dict[str, Any]]:  # type:ignore
        if self.conn is None or self.oid is None:
            return {}
        pod = self._get_pod_version()
        if pod:
            pod['metrics'] = self._get_metrics()
            pod['status'] = self._get_status()
            pod['classifiers'] = self._get_classifiers(self.oid, 'run')
            pod['events'] = self._get_events()
            pod['artifacts'] = self._get_artifacts()
        return pod

    @staticmethod
    def _build_command(columns: List[str], tables: List[str],
                       conditions: Optional[List[str]] = None,
                       joins: Optional[List[Tuple[str, str]]] = None) -> str:
        """
        build command
        """
        cmd: str = '''SELECT\n\t{}\nFROM\n\t{}'''.format(',\n\t'.join(columns), ',\n\t'.join(tables))
        if joins:
            for join in joins:
                cmd += '''\nLEFT JOIN {} ON {}'''.format(join[0], join[1])
        if conditions:
            cmd += '''\nWHERE\n\t{}'''.format('\nAND\n\t'.join(conditions))
        return cmd + ';'

    def __init__(self, conn: Optional['_psycopg.connection'],
                 oid: Optional[UUID] = None, reload: bool = True):  # pylint: disable=super-init-not-called
        self.conn = conn
        self.oid = oid
        self.result: Optional[Result] = None
        if reload:
            self.reload()

    def __repr__(self):
        return '<{} {}>'.format(self.__class__.__name__, self.oid)

    def __str__(self):
        return self.oid

    def reload(self):
        try:
            self.result = Result.from_pod(self.resultfile)
        except Exception as e:  # pylint: disable=broad-except
            self.result = Result()
            self.result.status = Status.UNKNOWN
            self.add_event(str(e))

    def get_artifact_path(self, name: str) -> str:
        artifact = self.get_artifact(name)
        if artifact and artifact.is_dir:
            return self._read_dir_artifact(artifact)
        else:
            return cast(str, self._read_file_artifact(artifact))

    def _read_dir_artifact(self, artifact: Artifact) -> str:
        """
        read directory artifact
        """
        artifact_path = tempfile.mkdtemp(prefix='wa_')
        if self.conn:
            with tarfile.open(fileobj=self.conn.lobject(int(artifact.path), mode='b'),
                              mode=cast(tarfile._FileCreationModes, 'r|gz')) as tar_file:  # type:ignore
                safe_extract(tar_file, artifact_path)
            self.conn.commit()
        return artifact_path

    def _read_file_artifact(self, artifact: Optional[Artifact]) -> StringIO:
        """
        read file artifact
        """
        artifact_ = StringIO(self.conn.lobject(int(artifact.path if artifact else '')).read() if self.conn else '')
        if self.conn:
            self.conn.commit()
        return artifact_

    # pylint: disable=too-many-locals
    def _read_db(self, columns: List[Union[str, Tuple[str, str]]], tables: List[str],
                 conditions: Optional[List[str]] = None, join: Optional[List[Tuple[str, str]]] = None,
                 as_dict: bool = True) -> List[Dict]:
        # Automatically remove table name from column when using column names as keys or
        # allow for column names to be aliases when retrieving the data,
        # (db_column_name, alias)
        db_columns: List[str] = []
        aliases_colunms: List[str] = []
        for column in columns:
            if isinstance(column, tuple):
                db_columns.append(column[0])
                aliases_colunms.append(column[1])
            else:
                db_columns.append(column)
                aliases_colunms.append(column.rsplit('.', 1)[-1])

        cmd: str = self._build_command(db_columns, tables, conditions, join)

        logger.debug(cmd)
        if self.conn:
            with self.conn.cursor() as cursor:
                cursor.execute(cmd)
                results = cursor.fetchall()
            self.conn.commit()

        if not as_dict:
            return cast(List[Dict[Any, Any]], results)

        # Format the output dict using column names as keys
        output: List[Dict] = []
        for result in results:
            entry = {}
            for k, v in zip(aliases_colunms, result):
                entry[k] = v
            output.append(entry)
        return output

    def _get_pod_version(self) -> Optional[Dict]:
        """
        get pod version from database
        """
        columns: List[Union[str, Tuple[str, str]]] = ['_pod_version', '_pod_serialization_version']
        tables: List[str] = ['{}s'.format(self.kind)]
        conditions = ['{}s.oid = \'{}\''.format(self.kind, self.oid)]
        results = self._read_db(columns, tables, conditions)
        if results:
            return results[0]
        else:
            return None

    def _populate_classifers(self, pod: List[Dict], kind: str) -> List[Dict]:
        """
        populate classifiers
        """
        for entry in pod:
            oid = entry.pop('oid')
            entry['classifiers'] = self._get_classifiers(oid, kind)
        return pod

    def _get_classifiers(self, oid: UUID, kind: str) -> Dict:
        """
        get classifiers from database. Classifiers are used to annotate generated
        metrics and artifacts in order to assist post-processing tools in sorting
        through them.
        """
        columns: List[Union[str, Tuple[str, str]]] = ['classifiers.key', 'classifiers.value']
        tables: List[str] = ['classifiers']
        conditions: List[str] = ['{}_oid = \'{}\''.format(kind, oid)]
        results = self._read_db(columns, tables, conditions, as_dict=False)
        classifiers = {}
        for (k, v) in results:
            classifiers[k] = v
        return classifiers

    def _get_metrics(self) -> List[Dict]:
        """
        get metrics from database
        """
        columns: List[Union[str, Tuple[str, str]]] = ['metrics.name', 'metrics.value', 'metrics.units',
                                                      'metrics.lower_is_better',
                                                      'metrics.oid', 'metrics._pod_version',
                                                      'metrics._pod_serialization_version']
        tables: List[str] = ['metrics']
        joins: List[Tuple[str, str]] = [('classifiers', 'classifiers.metric_oid = metrics.oid')]
        conditions: List[str] = ['metrics.{}_oid  = \'{}\''.format(self.kind, self.oid)]
        pod: List[Dict] = self._read_db(columns, tables, conditions, joins)
        return self._populate_classifers(pod, 'metric')

    def _get_status(self) -> Any:
        """
        get status from database
        """
        columns: List[Union[str, Tuple[str, str]]] = ['{}s.status'.format(self.kind)]
        tables: List[str] = ['{}s'.format(self.kind)]
        conditions: List[str] = ['{}s.oid = \'{}\''.format(self.kind, self.oid)]
        results: List[Dict] = self._read_db(columns, tables, conditions, as_dict=False)
        if results:
            return results[0][0]
        else:
            return None

    def _get_artifacts(self) -> List[Dict]:
        """
        get artifacts from database
        """
        columns: List[Union[str, Tuple[str, str]]] = ['artifacts.name', 'artifacts.description', 'artifacts.kind',
                                                      ('largeobjects.lo_oid', 'path'), 'artifacts.oid', 'artifacts.is_dir',
                                                      'artifacts._pod_version', 'artifacts._pod_serialization_version']
        tables: List[str] = ['largeobjects', 'artifacts']
        joins: List[Tuple[str, str]] = [('classifiers', 'classifiers.artifact_oid = artifacts.oid')]
        conditions: List[str] = ['artifacts.{}_oid = \'{}\''.format(self.kind, self.oid),
                                 'artifacts.large_object_uuid = largeobjects.oid']
        # If retrieving run level artifacts we want those that don't also belong to a job
        if self.kind == 'run':
            conditions.append('artifacts.job_oid IS NULL')
        pod: List[Dict] = self._read_db(columns, tables, conditions, joins)
        for artifact in pod:
            artifact['path'] = str(artifact['path'])
        return self._populate_classifers(pod, 'metric')

    def _get_events(self) -> List[Dict]:
        """
        get events from database
        """
        columns: List[Union[str, Tuple[str, str]]] = ['events.message', 'events.timestamp']
        tables: List[str] = ['events']
        conditions: List[str] = ['events.{}_oid = \'{}\''.format(self.kind, self.oid)]
        return self._read_db(columns, tables, conditions)


def kernel_config_from_db(raw: Any) -> Dict:
    """
    get kernel configuration from database
    """
    kernel_config: Dict = {}
    if raw:
        for k, v in zip(raw[0], raw[1]):
            kernel_config[k] = v
    return kernel_config


class RunDatabaseOutput(DatabaseOutput, RunOutputCommon):

    kind: str = 'run'

    @property
    def basepath(self):
        """
        get base path of database
        """
        return 'db:({})-{}@{}:{}'.format(self.dbname, self.user,
                                         self.host, self.port)

    @property
    def augmentations(self) -> List:
        """
        get augmentations for run output from databse
        """
        columns: List[Union[str, Tuple[str, str]]] = ['augmentations.name']
        tables: List[str] = ['augmentations']
        conditions: List[str] = ['augmentations.run_oid = \'{}\''.format(self.oid)]
        results: List[Dict] = self._read_db(columns, tables, conditions, as_dict=False)
        return [a for augs in results for a in augs]

    @property
    def _db_infofile(self) -> Dict:
        """
        get run info file from db
        """
        columns: List[Union[str, Tuple[str, str]]] = ['start_time', 'project', ('run_uuid', 'uuid'), 'end_time',
                                                      'run_name', 'duration', '_pod_version', '_pod_serialization_version']
        tables = ['runs']
        conditions = ['runs.run_uuid = \'{}\''.format(self.run_uuid)]
        pod = self._read_db(columns, tables, conditions)
        if not pod:
            return {}
        return pod[0]

    @property
    def _db_targetfile(self) -> Dict:
        """
        get database target file
        """
        columns: List[Union[str, Tuple[str, str]]] = ['os', 'is_rooted', 'target', 'modules', 'abi', 'cpus', 'os_version',
                                                      'hostid', 'hostname', 'kernel_version', 'kernel_release',
                                                      'kernel_sha1', 'kernel_config', 'sched_features', 'page_size_kb',
                                                      'system_id', 'screen_resolution', 'prop', 'android_id',
                                                      '_pod_version', '_pod_serialization_version']
        tables: List[str] = ['targets']
        conditions: List[str] = ['targets.run_oid = \'{}\''.format(self.oid)]
        pod_: List[Dict] = self._read_db(columns, tables, conditions)
        if not pod_:
            return {}
        pod: Dict = pod_[0]
        try:
            pod['cpus'] = [json.loads(cpu) for cpu in pod.pop('cpus')]
        except SerializerSyntaxError:
            pod['cpus'] = []
            logger.debug('Failed to deserialize target cpu information')
        pod['kernel_config'] = kernel_config_from_db(pod['kernel_config'])
        return pod

    @property
    def _db_statefile(self) -> Dict:
        """
        get state file from database
        """
        # Read overall run information
        columns: List[Union[str, Tuple[str, str]]] = ['runs.state']
        tables: List[str] = ['runs']
        conditions: List[str] = ['runs.run_uuid = \'{}\''.format(self.run_uuid)]
        pod_: List[Dict] = self._read_db(columns, tables, conditions)
        pod = pod_[0].get('state')
        if not pod:
            return {}

        # Read job information
        columns = ['jobs.job_id', 'jobs.oid']
        tables = ['jobs']
        conditions = ['jobs.run_oid = \'{}\''.format(self.oid)]
        job_oids: List[Dict] = self._read_db(columns, tables, conditions)

        # Match job oid with jobs from state file
        for job in pod.get('jobs', []):
            for job_oid in job_oids:
                if job['id'] == job_oid['job_id']:
                    job['oid'] = job_oid['oid']
                    break
        return pod

    @property
    def _db_jobsfile(self) -> List[Dict]:
        """
        get jobs file from database
        """
        workload_params: Dict = self._get_parameters('workload')
        runtime_params: Dict = self._get_parameters('runtime')

        columns: List[Union[str, Tuple[str, str]]] = [('jobs.job_id', 'id'), 'jobs.label', 'jobs.workload_name',
                                                      'jobs.oid', 'jobs._pod_version', 'jobs._pod_serialization_version']
        tables: List[str] = ['jobs']
        conditions: List[str] = ['jobs.run_oid = \'{}\''.format(self.oid)]
        jobs: List[Dict] = self._read_db(columns, tables, conditions)

        for job in jobs:
            job['augmentations'] = self._get_job_augmentations(job['oid'])
            job['workload_parameters'] = workload_params.pop(job['oid'], {})
            job['runtime_parameters'] = runtime_params.pop(job['oid'], {})
            job.pop('oid')
        return jobs

    @property
    def _db_run_config(self) -> Union[Dict, DefaultDict]:
        """
        get run configuration from database
        """
        pod: DefaultDict = defaultdict(dict)
        parameter_types: List[str] = ['augmentation', 'resource_getter']
        for parameter_type in parameter_types:
            columns: List[Union[str, Tuple[str, str]]] = ['parameters.name', 'parameters.value',
                                                          'parameters.value_type',
                                                          ('{}s.name'.format(parameter_type),
                                                           '{}'.format(parameter_type))]
            tables: List[str] = ['parameters', '{}s'.format(parameter_type)]
            conditions: List[str] = ['parameters.run_oid = \'{}\''.format(self.oid),
                                     'parameters.type = \'{}\''.format(parameter_type),
                                     'parameters.{0}_oid = {0}s.oid'.format(parameter_type)]
            configs: List[Dict] = self._read_db(columns, tables, conditions)
            for config_t in configs:
                entry: Dict = {config_t['name']: json.loads(config_t['value'])}
                pod['{}s'.format(parameter_type)][config_t.pop(parameter_type)] = entry

        # run config
        columns = ['runs.max_retries', 'runs.allow_phone_home',
                   'runs.bail_on_init_failure', 'runs.retry_on_status']
        tables = ['runs']
        conditions = ['runs.oid = \'{}\''.format(self.oid)]
        config_ = self._read_db(columns, tables, conditions)
        if not config_:
            return {}

        config = config_[0]
        # Convert back into a string representation of an enum list
        config['retry_on_status'] = config['retry_on_status'][1:-1].split(',')
        pod.update(config)
        return pod

    def __init__(self,
                 password: Optional[str] = None,
                 dbname: str = 'wa',
                 host: str = 'localhost',
                 port: str = '5432',
                 user: str = 'postgres',
                 run_uuid: Optional[UUID] = None,
                 list_runs: bool = False):

        if psycopg2 is None:
            msg: str = 'Please install the psycopg2 in order to connect to postgres databases'
            raise HostError(msg)

        self.dbname = dbname
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.run_uuid = run_uuid
        self.conn: Optional[_psycopg.connection] = None

        self.info: Optional[RunInfo] = None
        self.state: Optional[RunState] = None
        self.result: Optional[Result] = None
        self.target_info: Optional[TargetInfo] = None
        self._combined_config: Optional[CombinedConfig] = None
        self.jobs: List['JobDatabaseOutput'] = []
        self.job_specs: List[JobSpecProtocol] = []

        self.connect()
        super(RunDatabaseOutput, self).__init__(conn=self.conn, reload=False)

        local_schema_version, db_schema_version = get_schema_versions(self.conn)
        if local_schema_version != db_schema_version:
            self.disconnect()
            msg = 'The current database schema is v{} however the local ' \
                  'schema version is v{}. Please update your database ' \
                  'with the create command'
            raise HostError(msg.format(db_schema_version, local_schema_version))

        if list_runs:
            print('Available runs are:')
            self._list_runs()
            self.disconnect()
            return
        if not self.run_uuid:
            print('Please specify "Run uuid"')
            self._list_runs()
            self.disconnect()
            return

        if not self.oid:
            self.oid = self._get_oid()
        self.reload()

    def read_job_specs(self) -> List[JobSpecProtocol]:
        """
        read job specifications
        """
        job_specs: List[JobSpecProtocol] = []
        for job in self._db_jobsfile:
            job_specs.append(cast(JobSpecProtocol, JobSpec.from_pod(job)))
        return job_specs

    def connect(self) -> None:
        """
        connect to database
        """
        if self.conn and not self.conn.closed:
            return
        try:
            self.conn = psycopg2.connect(dbname=self.dbname,
                                         user=self.user,
                                         host=self.host,
                                         password=self.password,
                                         port=self.port) if psycopg2 else None
        except Psycopg2Error or Exception as e:
            raise HostError('Unable to connect to the Database: "{}'.format(e.args[0]))

    def disconnect(self) -> None:
        """
        disconnect from database
        """
        if self.conn:
            self.conn.commit()
            self.conn.close()

    def reload(self) -> None:
        super(RunDatabaseOutput, self).reload()
        info_pod: Dict = self._db_infofile
        state_pod: Dict = self._db_statefile
        if not info_pod or not state_pod:
            msg: str = '"{}" does not appear to be a valid WA Database Output.'
            raise ValueError(msg.format(self.oid))

        self.info = RunInfo.from_pod(info_pod)
        self.state = RunState.from_pod(state_pod)
        self._combined_config = CombinedConfig.from_pod({'run_config': self._db_run_config})
        self.target_info = TargetInfo.from_pod(self._db_targetfile)
        self.job_specs = self.read_job_specs()

        for job_state in self._db_statefile['jobs']:
            job = JobDatabaseOutput(self.conn, job_state.get('oid'), job_state['id'],
                                    job_state['label'], job_state['iteration'],
                                    job_state['retries'])
            job.status = job_state['status']
            job.spec = self.get_job_spec(job.id)
            if job.spec is None:
                logger.warning('Could not find spec for job {}'.format(job.id))
            self.jobs.append(job)

    def _get_oid(self) -> UUID:
        """
        get database oid
        """
        columns: List[Union[str, Tuple[str, str]]] = ['{}s.oid'.format(self.kind)]
        tables: List[str] = ['{}s'.format(self.kind)]
        conditions: List[str] = ['runs.run_uuid = \'{}\''.format(self.run_uuid)]
        oid: List[Dict] = self._read_db(columns, tables, conditions, as_dict=False)
        if not oid:
            raise ConfigError('No matching run entries found for run_uuid {}'.format(self.run_uuid))
        if len(oid) > 1:
            raise ConfigError('Multiple entries found for run_uuid: {}'.format(self.run_uuid))
        return oid[0][0]

    def _get_parameters(self, param_type: str) -> Dict:
        """
        get database parameters
        """
        columns: List[Union[str, Tuple[str, str]]] = ['parameters.job_oid', 'parameters.name', 'parameters.value']
        tables: List[str] = ['parameters']
        conditions: List[str] = ['parameters.type = \'{}\''.format(param_type),
                                 'parameters.run_oid = \'{}\''.format(self.oid)]
        params: List[Dict] = self._read_db(columns, tables, conditions, as_dict=False)
        parm_dict: DefaultDict = defaultdict(dict)
        for (job_oid, k, v) in params:
            try:
                parm_dict[job_oid][k] = json.loads(v)
            except SerializerSyntaxError:
                logger.debug('Failed to deserialize job_oid:{}-"{}":"{}"'.format(job_oid, k, v))
        return parm_dict

    def _get_job_augmentations(self, job_oid: UUID) -> List:
        """
        get job augmentations
        """
        columns: List[Union[str, Tuple[str, str]]] = ['jobs_augs.augmentation_oid', 'augmentations.name',
                                                      'augmentations.oid', 'jobs_augs.job_oid']
        tables: List[str] = ['jobs_augs', 'augmentations']
        conditions: List[str] = ['jobs_augs.job_oid = \'{}\''.format(job_oid),
                                 'jobs_augs.augmentation_oid = augmentations.oid']
        augmentations: List[Dict] = self._read_db(columns, tables, conditions)
        return [aug['name'] for aug in augmentations]

    def _list_runs(self) -> None:
        """
        list runs
        """
        columns: List[Union[str, Tuple[str, str]]] = ['runs.run_uuid', 'runs.run_name', 'runs.project',
                                                      'runs.project_stage', 'runs.status',
                                                      'runs.start_time', 'runs.end_time']
        tables: List[str] = ['runs']
        pod: List[Dict] = self._read_db(columns, tables)
        if pod:
            headers: List[str] = ['Run Name', 'Project', 'Project Stage', 'Start Time', 'End Time',
                                  'run_uuid']
            run_list: List = []
            for entry in pod:
                # Format times to display better
                start_time = entry['start_time']
                end_time = entry['end_time']
                if start_time:
                    start_time = start_time.strftime("%Y-%m-%d %H:%M:%S")
                if end_time:
                    end_time = end_time.strftime("%Y-%m-%d %H:%M:%S")

                run_list.append([
                                entry['run_name'],
                                entry['project'],
                                entry['project_stage'],
                                start_time,
                                end_time,
                                entry['run_uuid']])

            print(format_simple_table(run_list, headers))
        else:
            print('No Runs Found')


class JobDatabaseOutput(DatabaseOutput):

    kind: str = 'job'

    def __init__(self, conn: Optional['_psycopg.connection'], oid: UUID,
                 job_id: str, label: str, iteration: int, retry: int):
        super(JobDatabaseOutput, self).__init__(conn, oid=oid)
        self.id = job_id
        self.label = label
        self.iteration = iteration
        self.retry = retry
        self.result: Optional[Result] = None
        self.spec: Optional[JobSpecProtocol] = None
        self.reload()

    def __repr__(self):
        return '<{} {}-{}-{}>'.format(self.__class__.__name__,
                                      self.id, self.label, self.iteration)

    def __str__(self):
        return '{}-{}-{}'.format(self.id, self.label, self.iteration)

    @property
    def augmentations(self) -> List:
        """
        augmentations
        """
        job_augs: Set = set([])
        if self.spec:
            for aug in self.spec.augmentations:
                job_augs.add(aug)
        return list(job_augs)
