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

# pylint: disable=no-member

import hashlib
import logging
import os
import shutil
from copy import copy
from datetime import datetime
from collections import Counter

import wa.framework.signal as signal
from wa.framework import instrument as instrumentation
from wa.framework.configuration.core import Status
from wa.framework.exception import TargetError, HostError, WorkloadError, ExecutionError
from wa.framework.exception import TargetNotRespondingError, TimeoutError  # pylint: disable=redefined-builtin
from wa.framework.job import Job
from wa.framework.output import init_job_output, Output, RunOutput, Metric, Artifact
from wa.framework.output_processor import ProcessorManager
from wa.framework.resource import ResourceResolver, Resource
from wa.framework.target.manager import TargetManager
from wa.utils import log
from wa.utils.misc import merge_config_values, format_duration
from typing import (Optional, Dict, Any, TYPE_CHECKING, cast, List, Type)
from devlib.target import AndroidTarget, Target
from types import ModuleType
if TYPE_CHECKING:
    from wa.framework.configuration.execution import ConfigManager
    from wa.framework.configuration.core import RunConfigurationProtocol, RebootPolicy, ConfigurationPoint
    from wa.framework.signal import Signal
    from wa.framework.workload import Workload
    from wa.framework.target.info import TargetInfo
    from wa.framework.plugin import Plugin
    from wa.framework.configuration.core import StatusType
    from louie.dispatcher import Anonymous  # type:ignore


class ExecutionContext(object):

    @property
    def previous_job(self) -> Optional[Job]:
        """
        previous job that was executed and completed
        """
        if not self.completed_jobs:
            return None
        return self.completed_jobs[-1]

    @property
    def next_job(self) -> Optional[Job]:
        """
        next job in the job queue to be executed
        """
        if not self.job_queue:
            return None
        return self.job_queue[0]

    @property
    def spec_changed(self) -> bool:
        """
        checks whether job spec has changed between previous and current job
        """
        if self.previous_job is None and self.current_job is not None:  # Start of run
            return True
        if self.previous_job is not None and self.current_job is None:  # End of run
            return True
        return (self.previous_job is not None and self.current_job is not None) and (self.current_job.spec.id != self.previous_job.spec.id)

    @property
    def spec_will_change(self) -> bool:
        """
        checks whether job spec will change between current and next job
        """
        if self.current_job is None and self.next_job is not None:  # Start of run
            return True
        if self.current_job is not None and self.next_job is None:  # End of run
            return True
        return (self.next_job is not None and self.current_job is not None) and self.current_job.spec.id != self.next_job.spec.id

    @property
    def workload(self) -> Optional['Workload']:
        """
        workload being executed in the current job
        """
        if self.current_job:
            return self.current_job.workload
        return None

    @property
    def job_output(self) -> Optional[Output]:
        """
        output from the current job
        """
        if self.current_job:
            return self.current_job.output
        return None

    @property
    def output(self) -> RunOutput:
        """
        output from the current run
        """
        if self.current_job:
            return self.job_output  # type:ignore
        return self.run_output

    @property
    def output_directory(self) -> str:
        """
        output directory of the job execution
        """
        return self.output.basepath

    @property
    def reboot_policy(self) -> 'RebootPolicy':
        """
        reboot policy
        """
        return cast('RunConfigurationProtocol', self.cm.run_config).reboot_policy

    @property
    def target_info(self) -> Optional['TargetInfo']:
        """
        get target info
        """
        return self.run_output.target_info

    def __init__(self, cm: 'ConfigManager', tm: 'TargetManager', output: RunOutput):
        self.logger: logging.Logger = logging.getLogger('context')
        self.cm = cm
        self.tm = tm
        self.run_output = output
        self.run_state = output.state
        self.job_queue: Optional[List[Job]] = None
        self.completed_jobs: Optional[List[Job]] = None
        self.current_job: Optional[Job] = None
        self.successful_jobs: int = 0
        self.failed_jobs: int = 0
        self.run_interrupted: bool = False
        self._load_resource_getters()

    def start_run(self) -> None:
        """
        start execution
        """
        if self.output.info:
            self.output.info.start_time = datetime.utcnow()
        self.output.write_info()
        self.job_queue = copy(self.cm.jobs)
        self.completed_jobs = []
        if self.run_state:
            self.run_state.status = Status.STARTED
        self.output.status = Status.STARTED
        self.output.write_state()

    def end_run(self) -> None:
        """
        end the execution
        """
        if self.successful_jobs:
            if self.failed_jobs:
                status: 'StatusType' = Status.PARTIAL
            else:
                status = Status.OK
        else:
            status = Status.FAILED
        if self.run_state:
            self.run_state.status = status
        self.run_output.status = status
        if self.run_output.info:
            self.run_output.info.end_time = datetime.utcnow()
            self.run_output.info.duration = (cast(datetime, self.run_output.info.end_time)
                                             - cast(datetime, self.run_output.info.start_time))
        self.write_output()

    def finalize(self) -> None:
        """
        finalize the execution
        """
        self.tm.finalize()

    def start_job(self) -> 'Job':
        """
        start a job from the job queue
        """
        if not self.job_queue:
            raise RuntimeError('No jobs to run')
        self.current_job = self.job_queue.pop(0)
        job_output = init_job_output(self.run_output, self.current_job)
        self.current_job.set_output(job_output)
        return self.current_job

    def end_job(self) -> None:
        """
        end running job
        """
        if not self.current_job:
            raise RuntimeError('No jobs in progress')
        if self.completed_jobs:
            self.completed_jobs.append(self.current_job)
        self.output.write_result()
        self.current_job = None

    def set_status(self, status: 'StatusType',
                   force: bool = False, write: bool = True) -> None:
        """
        set status for the current job
        """
        if not self.current_job:
            raise RuntimeError('No jobs in progress')
        self.set_job_status(self.current_job, status, force, write)

    def set_job_status(self, job: Job, status: 'StatusType',
                       force: bool = False, write: bool = True) -> None:
        """
        set status for the specified job
        """
        job.set_status(status, force)
        if write:
            self.run_output.write_state()

    def extract_results(self) -> None:
        """
        exract results of the execution
        """
        self.tm.extract_results(self)

    def move_failed(self, job: Job):
        """
        move output of failed jobs to a separate directory
        """
        if job.output:
            self.run_output.move_failed(job.output)

    def skip_job(self, job: Job) -> None:
        """
        skip execution of the specified job
        """
        self.set_job_status(job, Status.SKIPPED, force=True)
        if self.completed_jobs:
            self.completed_jobs.append(job)

    def skip_remaining_jobs(self) -> None:
        """
        skip all the remaining jobs execution
        """
        while self.job_queue:
            job: Job = self.job_queue.pop(0)
            self.skip_job(job)
        self.write_state()

    def write_config(self) -> None:
        """
        write config into a config json file
        """
        self.run_output.write_config(self.cm.get_config())

    def write_state(self) -> None:
        """
        write execution state into .run_state json file
        """
        self.run_output.write_state()

    def write_output(self) -> None:
        """
        write info into run_info file, state into .run_state file and result into result file
        """
        self.run_output.write_info()
        self.run_output.write_state()
        self.run_output.write_result()

    def write_job_specs(self) -> None:
        """
        write job specs into jobs.json file
        """
        self.run_output.write_job_specs(self.cm.job_specs)

    def add_augmentation(self, aug: 'Plugin') -> None:
        """
        add augmentation to the run configuration
        """
        self.cm.run_config.add_augmentation(aug)

    def get_resource(self, resource: Resource, strict: bool = True) -> Optional[str]:
        """
        get path to the resource
        """
        result: Optional[str] = self.resolver.get(resource, strict)
        if result is None:
            return result
        if os.path.isfile(result):
            with open(result, 'rb') as fh:
                md5hash = hashlib.md5(fh.read())
                key = '{}/{}'.format(resource.owner, os.path.basename(result))
                self.update_metadata('hashes', key, md5hash.hexdigest())
        return result

    get = get_resource  # alias to allow a context to act as a resolver

    def get_metric(self, name: str) -> Optional[Metric]:
        """
        get metric of the specified name from the workload execution output
        """
        try:
            return self.output.get_metric(name)
        except HostError:
            if not self.current_job:
                raise
            return self.run_output.get_metric(name)

    def add_metric(self, name: str, value: Any, units: Optional[str] = None,
                   lower_is_better: bool = False,
                   classifiers: Optional[Dict[str, Any]] = None):
        """
        Add a metric to the workload execution output
        """
        if self.current_job:
            classifiers = merge_config_values(self.current_job.classifiers,
                                              classifiers)
        self.output.add_metric(name, value, units, lower_is_better, classifiers)

    def get_artifact(self, name: str) -> Optional[Artifact]:
        """
        get artifact from workload execution output
        """
        try:
            return self.output.get_artifact(name)
        except HostError:
            if not self.current_job:
                raise
            return self.run_output.get_artifact(name)

    def get_artifact_path(self, name: str) -> str:
        """
        get path to the specified artifact
        """
        try:
            return self.output.get_artifact_path(name)
        except HostError:
            if not self.current_job:
                raise
            return self.run_output.get_artifact_path(name)

    def add_artifact(self, name: str, path: str, kind: str,
                     description: Optional[str] = None,
                     classifiers: Optional[Dict[str, Any]] = None) -> None:
        """
        add artifact to the workload job execution output
        """
        self.output.add_artifact(name, path, kind, description, classifiers)

    def add_run_artifact(self, name: str, path: str, kind: str,
                         description: Optional[str] = None,
                         classifiers: Optional[Dict[str, Any]] = None) -> None:
        """
        add artifact to the workload run execution output
        """
        self.run_output.add_artifact(name, path, kind, description, classifiers)

    def add_event(self, message: str) -> None:
        """
        add event to the workload job execution output
        """
        self.output.add_event(message)

    def add_classifier(self, name: str, value: Any, overwrite: bool = False) -> None:
        """
        add classifier to workload execution output
        """
        self.output.add_classifier(name, value, overwrite)
        if self.current_job:
            self.current_job.add_classifier(name, value, overwrite)

    def add_metadata(self, key: str, *args, **kwargs) -> None:
        """
        add metadata to workload execution output
        """
        self.output.add_metadata(key, *args, **kwargs)

    def update_metadata(self, key: str, *args) -> None:
        """
        update an existing metadata in workload execution output
        """
        if self.output:
            self.output.update_metadata(key, *args)

    def take_screenshot(self, filename: str) -> None:
        """
        take screenshot
        """
        filepath: str = self._get_unique_filepath(filename)
        if self.tm.target:
            self.tm.target.capture_screen(filepath)
        if os.path.isfile(filepath):
            self.add_artifact('screenshot', filepath, kind='log')

    def take_uiautomator_dump(self, filename: str) -> None:
        """
        take a ui automator dump
        """
        filepath = self._get_unique_filepath(filename)
        cast(AndroidTarget, self.tm.target).capture_ui_hierarchy(filepath)
        self.add_artifact('uitree', filepath, kind='log')

    def record_ui_state(self, basename: str) -> None:
        """
        record ui state of the target
        """
        self.logger.info('Recording screen state...')
        self.take_screenshot('{}.png'.format(basename))
        target: Optional[Target] = self.tm.target
        if target and (target.os == 'android' or
           (target.os == 'chromeos' and target.has('android_container'))):
            self.take_uiautomator_dump('{}.uix'.format(basename))

    def initialize_jobs(self) -> None:
        """
        initialize jobs
        """
        new_queue: List[Job] = []
        failed_ids: List[str] = []
        if self.job_queue:
            for job in self.job_queue:
                if job.id in failed_ids:
                    # Don't try to initialize a job if another job with the same ID
                    # (i.e. same job spec) has failed - we can assume it will fail
                    # too.
                    self.skip_job(job)
                    continue

                try:
                    job.initialize(self)
                except WorkloadError as e:
                    self.set_job_status(job, Status.FAILED, write=False)
                    log.log_error(e, self.logger)
                    failed_ids.append(job.id or '')

                    if self.cm.run_config.bail_on_init_failure:
                        raise
                else:
                    new_queue.append(job)

        self.job_queue = new_queue
        self.write_state()

    def _load_resource_getters(self) -> None:
        """
        load resource getters
        """
        self.logger.debug('Loading resource discoverers')
        self.resolver = ResourceResolver(cast(ModuleType, self.cm.plugin_cache))
        self.resolver.load()
        for getter in self.resolver.getters:
            self.cm.run_config.add_resource_getter(getter)

    def _get_unique_filepath(self, filename: str) -> str:
        """
        get a unique filepath for the specified file in output directory
        """
        filepath: str = os.path.join(self.output_directory, filename)
        rest, ext = os.path.splitext(filepath)
        i: int = 1
        new_filepath: str = '{}-{}{}'.format(rest, i, ext)

        if not os.path.exists(filepath) and not os.path.exists(new_filepath):
            return filepath
        elif not os.path.exists(new_filepath):
            # new_filepath does not exit, thefore filepath must exit.
            # this is the first collision
            shutil.move(filepath, new_filepath)

        while os.path.exists(new_filepath):
            i += 1
            new_filepath = '{}-{}{}'.format(rest, i, ext)
        return new_filepath


class Executor(object):
    """
    The ``Executor``'s job is to set up the execution context and pass to a
    ``Runner`` along with a loaded run specification. Once the ``Runner`` has
    done its thing, the ``Executor`` performs some final reporting before
    returning.

    The initial context set up involves combining configuration from various
    sources, loading of required workloads, loading and installation of
    instruments and output processors, etc. Static validation of the combined
    configuration is also performed.

    """
    # pylint: disable=R0915

    def __init__(self) -> None:
        self.logger: logging.Logger = logging.getLogger('executor')
        self.error_logged: bool = False
        self.warning_logged: bool = False
        self.target_manager: Optional[TargetManager] = None

    def execute(self, config_manager: 'ConfigManager', output: RunOutput):
        """
        Execute the run specified by an agenda. Optionally, selectors may be
        used to only execute a subset of the specified agenda.

        Params::

            :state: a ``ConfigManager`` containing processed configuration
            :output: an initialized ``RunOutput`` that will be used to
                     store the results.

        """
        signal.connect(self._error_signalled_callback, signal.ERROR_LOGGED)
        signal.connect(self._warning_signalled_callback, signal.WARNING_LOGGED)

        self.logger.info('Initializing run')
        self.logger.debug('Finalizing run configuration.')
        config = config_manager.finalize()
        output.write_config(config)

        if config.run_config:
            self.target_manager = TargetManager(config.run_config.device,
                                                cast(Dict[str, 'ConfigurationPoint'], config.run_config.device_config),
                                                output.basepath)
        if self.target_manager:
            self.logger.info('Initializing execution context')
            context = ExecutionContext(config_manager, self.target_manager, output)

        try:
            self.do_execute(context)
        except KeyboardInterrupt as e:
            context.run_output.status = Status.ABORTED
            log.log_error(e, self.logger)
            context.write_output()
            raise
        except Exception as e:
            context.run_output.status = Status.FAILED
            log.log_error(e, self.logger)
            context.write_output()
            raise
        finally:
            context.finalize()
            self.execute_postamble(context, output)
            signal.send(signal.RUN_COMPLETED, cast(Type['Anonymous'], self), context)

    def do_execute(self, context: ExecutionContext) -> None:
        """
        connect to target, do initializations and run the jobs
        """
        self.logger.info('Connecting to target')
        context.tm.initialize()

        if context.cm.run_config.reboot_policy.perform_initial_reboot:
            self.logger.info('Performing initial reboot.')
            attempts: int = context.cm.run_config.max_retries
            while attempts:
                try:
                    if self.target_manager:
                        self.target_manager.reboot(context)
                except TargetError as e:
                    if attempts:
                        attempts -= 1
                    else:
                        raise e
                else:
                    break
        if self.target_manager:
            context.output.set_target_info(self.target_manager.get_target_info())

        self.logger.info('Generating jobs')
        context.cm.generate_jobs(context)
        context.write_job_specs()
        context.output.write_state()

        if self.target_manager and self.target_manager.target:
            self.logger.info('Installing instruments')
            for instrument in context.cm.get_instruments(self.target_manager.target):
                instrumentation.install(instrument, context)
            instrumentation.validate()

        self.logger.info('Installing output processors')
        pm = ProcessorManager()
        for proc in context.cm.get_processors():
            pm.install(proc, context)
        pm.validate()

        context.write_config()

        self.logger.info('Starting run')
        runner = Runner(context, pm)
        signal.send(signal.RUN_STARTED, cast(Type['Anonymous'], self), context)
        runner.run()

    def execute_postamble(self, context: ExecutionContext, output: RunOutput) -> None:
        """
        execute postamble
        """
        self.logger.info('Done.')
        duration: str = format_duration(output.info.duration or 0) if output.info else ''
        self.logger.info('Run duration: {}'.format(duration))
        num_ran: int = context.run_state.num_completed_jobs if context.run_state else 0
        status_summary: str = 'Ran a total of {} iterations: '.format(num_ran)

        if context.run_state:
            counter: Counter = context.run_state.get_status_counts()
        parts: List[str] = []
        for status in reversed(Status.levels):
            if status in counter:
                parts.append('{} {}'.format(counter[status], status))
        self.logger.info('{}{}'.format(status_summary, ', '.join(parts)))

        self.logger.info('Results can be found in {}'.format(output.basepath))

        if self.error_logged:
            self.logger.warning('There were errors during execution.')
            self.logger.warning('Please see {}'.format(output.logfile))
        elif self.warning_logged:
            self.logger.warning('There were warnings during execution.')
            self.logger.warning('Please see {}'.format(output.logfile))

    def _error_signalled_callback(self, _) -> None:
        """
        error signalled callback
        """
        self.error_logged = True
        signal.disconnect(self._error_signalled_callback, signal.ERROR_LOGGED)

    def _warning_signalled_callback(self, _) -> None:
        """
        warning signalled callback
        """
        self.warning_logged = True
        signal.disconnect(self._warning_signalled_callback, signal.WARNING_LOGGED)

    def __str__(self):
        return 'executor'

    __repr__ = __str__


class Runner(object):
    """
    Triggers running jobs and processing results

    Takes pre-initialized ExcecutionContext and ProcessorManager. Handles
    actually running the jobs, and triggers the ProcessorManager to handle
    processing job and run results.
    """

    def __init__(self, context: ExecutionContext, pm: ProcessorManager):
        self.logger: logging.Logger = logging.getLogger('runner')
        self.context = context
        self.pm = pm
        self.output = self.context.output
        self.config = self.context.cm

    def run(self) -> None:
        """
        run the jobs
        """
        try:
            self.initialize_run()
            self.send(signal.RUN_INITIALIZED)

            with signal.wrap('JOB_QUEUE_EXECUTION', cast(Type['Anonymous'], self), self.context):
                while self.context.job_queue:
                    if self.context.run_interrupted:
                        raise KeyboardInterrupt()
                    self.run_next_job(self.context)

        except KeyboardInterrupt as e:
            log.log_error(e, self.logger)
            self.logger.info('Skipping remaining jobs.')
            self.context.skip_remaining_jobs()
        except Exception as e:
            message: str = e.args[0] if e.args else str(e)
            log.log_error(e, self.logger)
            self.logger.error('Skipping remaining jobs due to "{}".'.format(message))
            self.context.skip_remaining_jobs()
            raise e
        finally:
            self.finalize_run()
            self.send(signal.RUN_FINALIZED)

    def initialize_run(self) -> None:
        """
        initialize run of execution
        """
        self.logger.info('Initializing run')
        signal.connect(self._error_signalled_callback, signal.ERROR_LOGGED)
        signal.connect(self._warning_signalled_callback, signal.WARNING_LOGGED)
        self.context.start_run()
        self.pm.initialize(self.context)
        with log.indentcontext():
            self.context.initialize_jobs()
        self.context.write_state()

    def finalize_run(self) -> None:
        """
        finalize run of execution
        """
        self.logger.info('Run completed')
        with log.indentcontext():
            if self.context.completed_jobs:
                for job in self.context.completed_jobs:
                    job.finalize(self.context)
        self.logger.info('Finalizing run')
        self.context.end_run()
        self.pm.enable_all()
        with signal.wrap('RUN_OUTPUT_PROCESSED', cast(Type['Anonymous'], self)):
            self.pm.process_run_output(self.context)
            self.pm.export_run_output(self.context)
        self.pm.finalize(self.context)
        if self.context.reboot_policy.reboot_on_run_completion:
            self.logger.info('Rebooting target on run completion.')
            self.context.tm.reboot(self.context)
        signal.disconnect(self._error_signalled_callback, signal.ERROR_LOGGED)
        signal.disconnect(self._warning_signalled_callback, signal.WARNING_LOGGED)

    def run_next_job(self, context: ExecutionContext) -> None:
        """
        run next job
        """
        job: Job = context.start_job()
        self.logger.info('Running job {}'.format(job.id))

        try:
            log.indent()
            if self.context.reboot_policy.reboot_on_each_job:
                self.logger.info('Rebooting on new job.')
                self.context.tm.reboot(context)
            elif self.context.reboot_policy.reboot_on_each_spec and context.spec_changed:
                self.logger.info('Rebooting on new spec.')
                self.context.tm.reboot(context)

            with signal.wrap('JOB', cast(Type['Anonymous'], self), context):
                context.tm.start()
                self.do_run_job(job, context)
                context.set_job_status(job, Status.OK)
        except (Exception, KeyboardInterrupt) as e:  # pylint: disable=broad-except
            log.log_error(e, self.logger)
            if isinstance(e, KeyboardInterrupt):
                context.run_interrupted = True
                context.set_job_status(job, Status.ABORTED)
                raise e
            else:
                context.set_job_status(job, Status.FAILED)
            if isinstance(e, TargetNotRespondingError):
                raise e
            elif isinstance(e, TargetError):
                context.tm.verify_target_responsive(context)
        finally:
            self.logger.info('Completing job {}'.format(job.id))
            self.send(signal.JOB_COMPLETED)
            context.tm.stop()
            context.end_job()

            log.dedent()
            self.check_job(job)

    def do_run_job(self, job: Job, context: ExecutionContext) -> None:
        """
        do run job
        """
        # pylint: disable=too-many-branches,too-many-statements
        rc: 'RunConfigurationProtocol' = self.context.cm.run_config
        if job.workload and job.workload.phones_home and not rc.allow_phone_home:
            self.logger.warning('Skipping job {} ({}) due to allow_phone_home=False'
                                .format(job.id, job.workload.name))
            self.context.skip_job(job)
            return

        context.set_job_status(job, Status.RUNNING)
        self.send(signal.JOB_STARTED)

        job.configure_augmentations(context, self.pm)

        with signal.wrap('JOB_TARGET_CONFIG', cast(Type['Anonymous'], self), context):
            job.configure_target(context)

        try:
            job.setup(context)
        except Exception as e:
            context.set_job_status(job, Status.FAILED)
            log.log_error(e, self.logger)
            if isinstance(e, (TargetError, TimeoutError)):
                context.tm.verify_target_responsive(context)
            self.context.record_ui_state('setup-error')
            raise e

        try:

            try:
                job.run(context)
            except KeyboardInterrupt:
                context.run_interrupted = True
                context.set_job_status(job, Status.ABORTED)
                raise
            except Exception as e:
                context.set_job_status(job, Status.FAILED)
                log.log_error(e, self.logger)
                if isinstance(e, (TargetError, TimeoutError)):
                    context.tm.verify_target_responsive(context)
                self.context.record_ui_state('run-error')
                raise e
            finally:
                try:
                    with signal.wrap('JOB_OUTPUT_PROCESSED', cast(Type['Anonymous'], self), context):
                        job.process_output(context)
                        self.pm.process_job_output(context)
                    self.pm.export_job_output(context)
                except Exception as e:
                    context.set_job_status(job, Status.PARTIAL)
                    if isinstance(e, (TargetError, TimeoutError)):
                        context.tm.verify_target_responsive(context)
                    self.context.record_ui_state('output-error')
                    raise

        except KeyboardInterrupt:
            context.run_interrupted = True
            context.set_status(Status.ABORTED)
            raise
        finally:
            # If setup was successfully completed, teardown must
            # run even if the job failed
            job.teardown(context)

    def check_job(self, job: Job) -> None:
        """
        check job
        """
        rc: 'RunConfigurationProtocol' = self.context.cm.run_config
        if job.status in rc.retry_on_status:
            if job.retries < rc.max_retries:
                msg: str = 'Job {} iteration {} completed with status {}. retrying...'
                self.logger.error(msg.format(job.id, job.iteration, job.status))
                self.retry_job(job)
                self.context.move_failed(job)
                self.context.write_state()
            else:
                msg = 'Job {} iteration {} completed with status {}. '\
                      'Max retries exceeded.'
                self.logger.error(msg.format(job.id, job.iteration, job.status))
                self.context.failed_jobs += 1
                self.send(signal.JOB_FAILED)
                if rc.bail_on_job_failure:
                    raise ExecutionError('Job {} failed, bailing.'.format(job.id))

        else:  # status not in retry_on_status
            self.logger.info('Job completed with status {}'.format(job.status))
            if job.status != 'ABORTED':
                self.context.successful_jobs += 1
            else:
                self.context.failed_jobs += 1
                self.send(signal.JOB_ABORTED)

    def retry_job(self, job: Job) -> None:
        """
        retry job
        """
        retry_job = Job(job.spec, job.iteration, self.context)
        retry_job.workload = job.workload
        retry_job.state = job.state
        # FIXME - the setter type is not geting recognized by the type checker
        retry_job.retries = job.retries + 1
        self.context.set_job_status(retry_job, Status.PENDING, force=True)
        if self.context.job_queue:
            self.context.job_queue.insert(0, retry_job)
        self.send(signal.JOB_RESTARTED)

    def send(self, s: 'Signal') -> None:
        """
        send signal to runner
        """
        signal.send(s, cast(Type['Anonymous'], self), self.context)

    def _error_signalled_callback(self, record: logging.LogRecord) -> None:
        """
        error signalled callback
        """
        self.context.add_event(record.getMessage())

    def _warning_signalled_callback(self, record: logging.LogRecord) -> None:
        """
        warniing signalled callback
        """
        self.context.add_event(record.getMessage())

    def __str__(self):
        return 'runner'
