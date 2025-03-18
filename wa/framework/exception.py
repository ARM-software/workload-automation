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
# pylint: disable=unused-import
from devlib.exception import (DevlibError, HostError, TimeoutError,  # pylint: disable=redefined-builtin
                              TargetError, TargetNotRespondingError)

from wa.utils.misc import get_traceback
from typing import Optional, Tuple, Type
from types import TracebackType


class WAError(Exception):
    """Base class for all Workload Automation exceptions."""
    @property
    def message(self) -> str:
        """Error message"""
        if self.args:
            return self.args[0]
        return ''


class NotFoundError(WAError):
    """Raised when the specified item is not found."""


class ValidationError(WAError):
    """Raised on failure to validate an extension."""


class ExecutionError(WAError):
    """Error encountered by the execution framework."""


class WorkloadError(WAError):
    """General Workload error."""


class JobError(WAError):
    """Job execution error."""


class InstrumentError(WAError):
    """General Instrument error."""


class OutputProcessorError(WAError):
    """General OutputProcessor error."""


class ResourceError(WAError):
    """General Resolver error."""


class CommandError(WAError):
    """Raised by commands when they have encountered an error condition
    during execution."""


class ToolError(WAError):
    """Raised by tools when they have encountered an error condition
    during execution."""


class ConfigError(WAError):
    """Raised when configuration provided is invalid. This error suggests that
    the user should modify their config and try again."""


class SerializerSyntaxError(Exception):
    """
    Error loading a serialized structure from/to a file handle.
    """
    @property
    def message(self) -> str:
        """Error message"""
        if self.args:
            return self.args[0]
        return ''

    def __init__(self, message: str, line: Optional[int] = None,
                 column: Optional[int] = None):
        super(SerializerSyntaxError, self).__init__(message)
        self.line = line
        self.column = column

    def __str__(self) -> str:
        linestring: str = ' on line {}'.format(self.line) if self.line else ''
        colstring: str = ' in column {}'.format(self.column) if self.column else ''
        message: str = 'Syntax Error{}: {}'
        return message.format(''.join([linestring, colstring]), self.message)


class PluginLoaderError(WAError):
    """Raised when there is an error loading an extension or
    an external resource. Apart form the usual message, the __init__
    takes an exc_info parameter which should be the result of
    sys.exc_info() for the original exception (if any) that
    caused the error."""

    def __init__(self, message: str,
                 exc_info: Optional[Tuple[Optional[Type[BaseException]],
                                          Optional[BaseException], Optional[TracebackType]]] = None):
        super(PluginLoaderError, self).__init__(message)
        self.exc_info = exc_info

    def __str__(self) -> str:
        if self.exc_info:
            orig: Optional[BaseException] = self.exc_info[1]
            orig_name: str = type(orig).__name__
            if isinstance(orig, WAError):
                reason: str = 'because of:\n{}: {}'.format(orig_name, orig)
            else:
                text: str = 'because of:\n{}\n{}: {}'
                reason = text.format(get_traceback(self.exc_info), orig_name, orig)
            return '\n'.join([self.message, reason])
        else:
            return self.message


class WorkerThreadError(WAError):
    """
    This should get raised  in the main thread if a non-WAError-derived
    exception occurs on a worker/background thread. If a WAError-derived
    exception is raised in the worker, then it that exception should be
    re-raised on the main thread directly -- the main point of this is to
    preserve the backtrace in the output, and backtrace doesn't get output for
    WAErrors.

    """

    def __init__(self, thread: str,
                 exc_info: Tuple[Optional[Type[BaseException]],
                                 Optional[BaseException], Optional[TracebackType]]):
        self.thread = thread
        self.exc_info = exc_info
        orig = self.exc_info[1]
        orig_name = type(orig).__name__
        text = 'Exception of type {} occured on thread {}:\n{}\n{}: {}'
        message = text.format(orig_name, thread, get_traceback(self.exc_info),
                              orig_name, orig)
        super(WorkerThreadError, self).__init__(message)
