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

# Because of use of Enum (dynamic attrs)
# pylint: disable=no-member

import uuid
from collections import OrderedDict, Counter
from copy import copy
from datetime import datetime, timedelta

from wa.framework.configuration.core import Status
from wa.utils.serializer import Podable
from typing import (cast, TYPE_CHECKING, OrderedDict as od, Tuple,
                    Optional, Dict, Any, Union)
if TYPE_CHECKING:
    from wa.framework.job import Job
    from wa.framework.configuration.core import StatusType


class RunInfo(Podable):
    """
    Information about the current run, such as its unique ID, run
    time, etc.

    The :class:`RunInfo` provides general run information. It has the following
    attributes:

    ``uuid``
        A unique identifier for that particular run.

    ``run_name``
        The name of the run (if provided)

    ``project``
        The name of the project the run belongs to (if provided)

    ``project_stage``
        The project stage the run is associated with (if provided)

    ``duration``
        The length of time the run took to complete.

    ``start_time``
        The time the run was stared.

    ``end_time``
        The time at which the run finished.

    """
    _pod_serialization_version: int = 1

    @staticmethod
    def from_pod(pod: Dict[str, Any]) -> 'RunInfo':
        """
        create Runinfo from pod
        """
        pod = RunInfo._upgrade_pod(pod)
        uid: str = pod.pop('uuid')
        _pod_version = pod.pop('_pod_version')
        duration = pod.pop('duration')
        if uid is not None:
            uid_ = uuid.UUID(uid)
        instance = RunInfo(**pod)
        instance._pod_version = _pod_version  # pylint: disable=protected-access
        instance.uuid = uid_
        instance.duration = duration if duration is None else timedelta(seconds=duration)
        return instance

    def __init__(self, run_name: Optional[str] = None, project: Optional[str] = None,
                 project_stage: Optional[Union[Dict, str]] = None, start_time: Optional[datetime] = None,
                 end_time: Optional[datetime] = None, duration: Optional[timedelta] = None):
        super(RunInfo, self).__init__()
        self.uuid = uuid.uuid4()
        self.run_name = run_name
        self.project = project
        self.project_stage = project_stage
        self.start_time = start_time
        self.end_time = end_time
        self.duration = duration

    def to_pod(self) -> Dict[str, Any]:
        """
        create pod from RunInfo
        """
        d: Dict[str, Any] = super(RunInfo, self).to_pod()
        d.update(copy(self.__dict__))
        d['uuid'] = str(self.uuid)
        if self.duration is None:
            d['duration'] = self.duration
        else:
            d['duration'] = self.duration.total_seconds()
        return d

    @staticmethod
    def _pod_upgrade_v1(pod: Dict[str, Any]) -> Dict[str, Any]:
        """
        pod upgrade function version 1
        """
        pod['_pod_version'] = pod.get('_pod_version', 1)
        return pod


class RunState(Podable):
    """
    Represents the state of a WA run.

    """
    _pod_serialization_version: int = 1

    @staticmethod
    def from_pod(pod) -> 'RunState':
        """
        create RunState from pod
        """
        instance = cast('RunState', super(RunState, RunState).from_pod(pod))
        instance.status = Status.from_pod(pod['status'])
        instance.timestamp = pod['timestamp']
        jss = [JobState.from_pod(j) for j in pod['jobs']]
        instance.jobs = OrderedDict(((js.id, js.iteration), js) for js in jss)
        return instance

    @property
    def num_completed_jobs(self) -> int:
        """
        number of completed jobs in the current run
        """
        return sum(1 for js in self.jobs.values()
                   if js.status > Status.RUNNING)

    def __init__(self) -> None:
        super(RunState, self).__init__()
        self.jobs: od[Tuple[str, int], 'JobState'] = OrderedDict()
        self.status: 'StatusType' = Status.NEW
        self.timestamp = datetime.utcnow()

    def add_job(self, job: 'Job') -> None:
        """
        add job to the run state
        """
        self.jobs[(job.state.id, job.state.iteration)] = job.state

    def get_status_counts(self) -> Counter:
        """
        get status counter
        """
        counter: Counter = Counter()
        for job_state in self.jobs.values():
            counter[job_state.status] += 1
        return counter

    def to_pod(self) -> Dict[str, Any]:
        """
        convert RunState to pod
        """
        pod = super(RunState, self).to_pod()
        pod['status'] = self.status.to_pod()
        pod['timestamp'] = self.timestamp
        pod['jobs'] = [j.to_pod() for j in self.jobs.values()]
        return pod

    @staticmethod
    def _pod_upgrade_v1(pod: Dict[str, Any]) -> Dict[str, Any]:
        """
        pod upgrade function version 1
        """
        pod['_pod_version'] = pod.get('_pod_version', 1)
        pod['status'] = Status(pod['status']).to_pod()
        return pod


class JobState(Podable):
    """
    state of the running job
    """
    _pod_serialization_version: int = 1

    @staticmethod
    def from_pod(pod: Dict[str, Any]) -> 'JobState':
        """
        create a JobState from pod
        """
        pod = JobState._upgrade_pod(pod)
        instance = JobState(pod['id'], pod['label'], pod['iteration'],
                            Status.from_pod(pod['status']))
        instance.retries = pod['retries']
        instance.timestamp = pod['timestamp']
        return instance

    @property
    def output_name(self) -> str:
        return '{}-{}-{}'.format(self.id, self.label, self.iteration)

    def __init__(self, id: str, label: str, iteration: int, status: 'StatusType'):
        # pylint: disable=redefined-builtin
        super(JobState, self).__init__()
        self.id = id
        self.label = label
        self.iteration = iteration
        self.status = status
        self.retries = 0
        self.timestamp = datetime.utcnow()

    def to_pod(self) -> Dict[str, Any]:
        """
        convert JobState to pod
        """
        pod = super(JobState, self).to_pod()
        pod['id'] = self.id
        pod['label'] = self.label
        pod['iteration'] = self.iteration
        pod['status'] = cast(Podable, self.status).to_pod()
        pod['retries'] = self.retries
        pod['timestamp'] = self.timestamp
        return pod

    @staticmethod
    def _pod_upgrade_v1(pod: Dict[str, Any]) -> Dict[str, Any]:
        """
        pod upgrade function version 1
        """
        pod['_pod_version'] = pod.get('_pod_version', 1)
        pod['status'] = Status(pod['status']).to_pod()
        return pod
