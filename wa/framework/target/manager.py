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

import logging

from devlib.platform.gem5 import Gem5SimulationPlatform
from devlib.utils.misc import memoized
from devlib.target import Target
from devlib.module.hotplug import HotplugModule
from wa.framework import signal
from wa.framework.exception import ExecutionError, TargetError, TargetNotRespondingError
from wa.framework.plugin import Parameter
from wa.framework.target.descriptor import (get_target_description,
                                            instantiate_target,
                                            instantiate_assistant)
from wa.framework.target.info import (get_target_info, get_target_info_from_cache,
                                      cache_target_info, read_target_info_cache)
from wa.framework.target.runtime_parameter_manager import RuntimeParameterManager
from wa.framework.target.assistant import LinuxAssistant, AndroidAssistant, ChromeOsAssistant
from wa.utils.types import module_name_set, obj_dict
from typing import TYPE_CHECKING, Dict, Optional, Union, cast, Type, List, Any
from wa.framework.configuration.tree import JobSpecSource
if TYPE_CHECKING:
    from wa.framework.configuration.core import ConfigurationPoint
    from louie import dispatcher  # type:ignore
    from wa.framework.execution import ExecutionContext
    from wa.framework.target.info import TargetInfo
    from wa.framework.target.descriptor import TargetDescriptionProtocol


class TargetManager(object):
    """
    Instantiate the required target and perform configuration and validation of the device.
    """

    parameters: Dict[str, Parameter] = {'disconnect':
                                        Parameter('disconnect', kind=bool, default=False,
                                                  description="""
                                                    Specifies whether the target should be disconnected from
                                                    at the end of the run.
                                                    """),
                                        }

    def __init__(self, name: str, parameters: Dict[str, Parameter],
                 outdir: Optional[str]):
        self.outdir = outdir
        self.logger = logging.getLogger('tm')
        self.target_name = name
        self.target: Optional[Target] = None
        self.assistant: Optional[Union[LinuxAssistant, AndroidAssistant, ChromeOsAssistant]] = None
        self.platform_name: Optional[str] = None
        self.is_responsive: Optional[bool] = None
        self.rpm: Optional[RuntimeParameterManager] = None
        self.parameters = parameters
        # FIXME - seems like improper access. list of Parameter dont have get property
        self.disconnect = parameters.get('disconnect')

    def initialize(self) -> None:
        """
        initialize target and assistant
        """
        self._init_target()
        if self.assistant:
            self.assistant.initialize()

        # If target supports hotplugging, online all cpus before perform discovery
        # and restore original configuration after completed.
        if self.target:
            if self.target.has('hotplug'):
                online_cpus: List[int] = self.target.list_online_cpus()
                try:
                    cast(HotplugModule, self.target.hotplug).online_all()
                except TargetError:
                    msg: str = 'Failed to online all CPUS - some information may not be '\
                        'able to be retrieved.'
                    self.logger.debug(msg)
                self.rpm = RuntimeParameterManager(self.target)
                all_cpus = set(range(self.target.number_of_cpus))
                cast(HotplugModule, self.target.hotplug).offline(*all_cpus.difference(online_cpus))
            else:
                self.rpm = RuntimeParameterManager(self.target)

    def finalize(self) -> None:
        """
        finalize target and assistant
        """
        if not self.target:
            return
        if self.assistant:
            self.assistant.finalize()
        if self.disconnect or isinstance(self.target.platform, Gem5SimulationPlatform):
            self.logger.info('Disconnecting from the device')
            with signal.wrap('TARGET_DISCONNECT'):
                self.target.disconnect()

    def start(self) -> None:
        """
        start assistant
        """
        if self.assistant:
            self.assistant.start()

    def stop(self) -> None:
        """
        stop assistant
        """
        if self.assistant:
            self.assistant.stop()

    def extract_results(self, context: 'ExecutionContext') -> None:
        """
        extract results from target
        """
        if self.assistant:
            self.assistant.extract_results(context)

    @memoized
    def get_target_info(self) -> 'TargetInfo':
        """
        get target information
        """
        cache: Dict[str, Any] = read_target_info_cache()
        info: Optional['TargetInfo'] = get_target_info_from_cache(self.target.system_id,
                                                                  cache=cache) if self.target and self.target.system_id else None
        if self.target is None:
            raise TargetError("Target is None")
        if info is None:
            info = get_target_info(self.target)
            cache_target_info(info, cache=cache)
        else:
            # If module configuration has changed form when the target info
            # was previously cached, it is possible additional info will be
            # available, so should re-generate the cache.
            if module_name_set(info.modules) != module_name_set(self.target.modules):
                info = get_target_info(self.target)
                cache_target_info(info, overwrite=True, cache=cache)

        return info

    def reboot(self, context: 'ExecutionContext', hard: bool = False) -> None:
        """
        reboot the target
        """
        with signal.wrap('REBOOT', cast(Type[dispatcher.Anonymous], self), context):
            if self.target:
                self.target.reboot(hard)

    def merge_runtime_parameters(self,
                                 parameters: Dict[JobSpecSource, Dict[str, 'ConfigurationPoint']]) -> Dict:
        """
        merge runtime parameters from different sources
        """
        if self.rpm is None:
            raise ExecutionError('rpm is not set')
        return self.rpm.merge_runtime_parameters(parameters)

    def validate_runtime_parameters(self, parameters: obj_dict) -> None:
        """
        validate the runtime parameters
        """
        if self.rpm is None:
            raise ExecutionError('rpm is not set')
        self.rpm.validate_runtime_parameters(parameters)

    def commit_runtime_parameters(self, parameters: obj_dict) -> None:
        """
        commit the runtime parameters to runtime parameter manager
        """
        if self.rpm is None:
            raise ExecutionError('rpm is not set')
        self.rpm.commit_runtime_parameters(parameters)

    def verify_target_responsive(self, context: 'ExecutionContext') -> None:
        """
        verify that the target is responsive
        """
        can_reboot: bool = context.reboot_policy.can_reboot
        if self.target is None:
            raise TargetError("Target is None")
        if not self.target.check_responsive(explode=False):
            self.is_responsive = False
            if not can_reboot:
                raise TargetNotRespondingError('Target unresponsive and is not allowed to reboot.')
            elif self.target.has('hard_reset'):
                self.logger.info('Target unresponsive; performing hard reset')
                self.reboot(context, hard=True)
                self.is_responsive = True
                raise ExecutionError('Target became unresponsive but was recovered.')
            else:
                raise TargetNotRespondingError('Target unresponsive and hard reset not supported; bailing.')

    def _init_target(self) -> None:
        """
        initialize target
        """
        tdesc: 'TargetDescriptionProtocol' = get_target_description(self.target_name)

        extra_plat_params: Dict[str, str] = {}
        if tdesc.platform is Gem5SimulationPlatform:
            extra_plat_params['host_output_dir'] = self.outdir or ''

        self.logger.debug('Creating {} target'.format(self.target_name))
        self.target = instantiate_target(tdesc, self.parameters, connect=False,
                                         extra_platform_params=extra_plat_params)

        self.is_responsive = True

        with signal.wrap('TARGET_CONNECT'):
            self.target.connect()
        self.logger.info('Setting up target')
        self.target.setup()

        self.assistant = instantiate_assistant(tdesc, self.parameters, self.target)
