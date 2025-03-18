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


# pylint: disable=E1101
import logging
import logging.handlers
import os
import string
import subprocess
import threading
from contextlib import contextmanager
from typing_extensions import Protocol
from typing import (cast, Type, Optional, Union,
                    List, Generator, Any, Dict, Callable,
                    IO)
from louie import dispatcher  # type: ignore

import colorama  # type: ignore

from devlib.exception import DevlibError

from wa.framework import signal
from wa.framework.exception import WAError
from wa.utils.misc import get_traceback


COLOR_MAP = {
    logging.DEBUG: colorama.Fore.BLUE,
    logging.INFO: colorama.Fore.GREEN,
    logging.WARNING: colorama.Fore.YELLOW,
    logging.ERROR: colorama.Fore.RED,
    logging.CRITICAL: colorama.Style.BRIGHT + colorama.Fore.RED,
}

RESET_COLOR = colorama.Style.RESET_ALL

DEFAULT_INIT_BUFFER_CAPACITY = 1000

_indent_level: int = 0
_indent_width: int = 4
_console_handler: Optional[logging.StreamHandler] = None
_init_handler: Optional['InitHandler'] = None


class LoggedExc(Protocol):
    logged: bool  # Declares the attribute for type checkers


# pylint: disable=global-statement
def init(verbosity: int = logging.INFO, color: bool = True, indent_with: int = 4,
         regular_fmt: str = '%(levelname)-8s %(message)s',
         verbose_fmt: str = '%(asctime)s %(levelname)-8s %(name)10.10s: %(message)s',
         debug: bool = False) -> None:
    """
    initialize logger
    """
    global _indent_width, _console_handler, _init_handler
    _indent_width = indent_with
    signal.log_error_func = lambda m: log_error(m, signal.logger)  # type: ignore

    root_logger: logging.Logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    error_handler = ErrorSignalHandler(logging.DEBUG)
    root_logger.addHandler(error_handler)

    _console_handler = logging.StreamHandler()
    if color:
        formatter: Type[logging.Formatter] = ColorFormatter
    else:
        formatter = LineFormatter
    if verbosity:
        _console_handler.setLevel(logging.DEBUG)
        _console_handler.setFormatter(formatter(verbose_fmt))
    else:
        _console_handler.setLevel(logging.INFO)
        _console_handler.setFormatter(formatter(regular_fmt))
    root_logger.addHandler(_console_handler)

    buffer_capacity = int(os.getenv('WA_LOG_BUFFER_CAPACITY',
                                    str(DEFAULT_INIT_BUFFER_CAPACITY)))
    _init_handler = InitHandler(buffer_capacity)
    _init_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(_init_handler)

    logging.basicConfig(level=logging.DEBUG)
    if not debug:
        logging.raiseExceptions = False

    logger = logging.getLogger('CGroups')
    # FIXME - cannot assign to a method
    logger.info = logger.debug


def set_level(level: Union[int, str]) -> None:
    """
    set log level
    """
    if _console_handler:
        _console_handler.setLevel(level)


# pylint: disable=global-statement
def add_file(filepath: str, level: int = logging.DEBUG,
             fmt: str = '%(asctime)s %(levelname)-8s %(name)10.10s: %(message)s') -> None:
    """
    add log file
    """
    global _init_handler
    root_logger: logging.Logger = logging.getLogger()
    file_handler = logging.FileHandler(filepath)
    file_handler.setLevel(level)
    file_handler.setFormatter(LineFormatter(fmt))

    if _init_handler:
        _init_handler.flush_to_target(file_handler)
        root_logger.removeHandler(_init_handler)
        _init_handler = None

    root_logger.addHandler(file_handler)


def enable(logs: Union[str, List[str]]) -> None:
    """
    enable logging
    """
    if isinstance(logs, list):
        for log in logs:
            __enable_logger(log)
    else:
        __enable_logger(logs)


def disable(logs: Union[str, List[str]]) -> None:
    """
    disable logging
    """
    if isinstance(logs, list):
        for log in logs:
            __disable_logger(log)
    else:
        __disable_logger(logs)


def __enable_logger(logger: Union[str, logging.Logger]) -> None:
    """
    enable logger
    """
    if isinstance(logger, str):
        logger = logging.getLogger(logger)
    logger.propagate = True


def __disable_logger(logger: Union[str, logging.Logger]) -> None:
    """
    disable logger
    """
    if isinstance(logger, str):
        logger = logging.getLogger(logger)
    logger.propagate = False


# pylint: disable=global-statement
def indent() -> None:
    """
    increase indent level
    """
    global _indent_level
    _indent_level += 1


# pylint: disable=global-statement
def dedent() -> None:
    """
    decrease indent level
    """
    global _indent_level
    _indent_level -= 1


@contextmanager
def indentcontext() -> Generator[None, Any, None]:
    indent()
    try:
        yield
    finally:
        dedent()


# pylint: disable=global-statement
def set_indent_level(level: int):
    global _indent_level
    old_level = _indent_level
    _indent_level = level
    return old_level


def log_error(e: BaseException, logger: logging.Logger, critical: Optional[bool] = False) -> None:
    """
    Log the specified Exception as an error. The Error message will be formatted
    differently depending on the nature of the exception.

    :e: the error to log. should be an instance of ``Exception``
    :logger: logger to be used.
    :critical: if ``True``,  this error will be logged at ``logging.CRITICAL``
               level, otherwise it will be logged as ``logging.ERROR``.

    """
    if getattr(e, 'logged', None):
        return

    if critical:
        log_func = logger.critical
    else:
        log_func = logger.error

    if isinstance(e, KeyboardInterrupt):
        old_level: int = set_indent_level(0)
        logger.info('Got CTRL-C. Aborting.')
        set_indent_level(old_level)
    elif isinstance(e, (WAError, DevlibError)):
        log_func(str(e))
    elif isinstance(e, subprocess.CalledProcessError):
        tb: Optional[str] = get_traceback()
        log_func(tb)
        command: str = e.cmd
        if e.args:
            command = '{} {}'.format(command, ' '.join(map(str, e.args)))
        message: str = 'Command \'{}\' returned non-zero exit status {}\nOUTPUT:\n{}\n'
        log_func(message.format(command, e.returncode, e.output))
    elif isinstance(e, SyntaxError):
        tb = get_traceback()
        log_func(tb)
        message = 'Syntax Error in {}, line {}, offset {}:'
        log_func(message.format(e.filename, e.lineno, e.offset))
        log_func('\t{}'.format(e.msg))
    else:
        tb = get_traceback()
        log_func(tb)
        log_func('{}({})'.format(e.__class__.__name__, e))

    cast(LoggedExc, e).logged = True


class ErrorSignalHandler(logging.Handler):
    """
    Emits signals for ERROR and WARNING level traces.

    """

    def emit(self, record: logging.LogRecord):
        """
        emit a log record
        """
        if record.levelno == logging.ERROR:
            signal.send(signal.ERROR_LOGGED, cast(Type[dispatcher.Anonymous], self), record)
        elif record.levelno == logging.WARNING:
            signal.send(signal.WARNING_LOGGED, cast(Type[dispatcher.Anonymous], self), record)


class InitHandler(logging.handlers.BufferingHandler):
    """
    Used to buffer early logging records before a log file is created.

    """

    def __init__(self, capacity: int):
        super(InitHandler, self).__init__(capacity)
        self.targets: List[logging.Handler] = []

    def emit(self, record: logging.LogRecord) -> None:
        """
        emit a log record
        """
        record.indent_level = _indent_level
        super(InitHandler, self).emit(record)

    def flush(self) -> None:
        """
        flush logs
        """
        for target in self.targets:
            self.flush_to_target(target)
        self.buffer: List[logging.LogRecord] = []

    def add_target(self, target: logging.Handler):
        """
        add target handler
        """
        if target not in self.targets:
            self.targets.append(target)

    def flush_to_target(self, target: logging.Handler):
        """
        emit log to target handler
        """
        for record in self.buffer:
            target.emit(record)


class LineFormatter(logging.Formatter):
    """
    Logs each line of the message separately.

    """

    def format(self, record: logging.LogRecord) -> str:
        """
        format lines of the message
        """
        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)

        indent_level: int = getattr(record, 'indent_level', _indent_level)
        cur_indent: int = _indent_width * indent_level
        d: Dict[str, Any] = record.__dict__
        parts: List[str] = []
        for line in record.message.split('\n'):
            line = ' ' * cur_indent + line
            d.update({'message': line.strip('\r')})
            if self._fmt:
                parts.append(self._fmt % d)

        return '\n'.join(parts)


class ColorFormatter(LineFormatter):
    """
    Formats logging records with color and prepends record info
    to each line of the message.

        BLUE for DEBUG logging level
        GREEN for INFO logging level
        YELLOW for WARNING logging level
        RED for ERROR logging level
        BOLD RED for CRITICAL logging level

    """

    def __init__(self, fmt: Optional[str] = None, datefmt: Optional[str] = None):
        super(ColorFormatter, self).__init__(fmt, datefmt)
        template_text = self._fmt.replace('%(message)s', RESET_COLOR + '%(message)s${color}') if self._fmt else ''
        template_text = '${color}' + template_text + RESET_COLOR
        self.fmt_template = string.Template(template_text)

    def format(self, record: logging.LogRecord) -> str:
        """
        format line with color
        """
        self._set_color(COLOR_MAP[record.levelno])
        return super(ColorFormatter, self).format(record)

    def _set_color(self, color: str) -> None:
        """
        set log color
        """
        self._fmt = self.fmt_template.substitute(color=color)


class BaseLogWriter(object):

    def __init__(self, name: str, level: int = logging.DEBUG):
        """
        File-like object class designed to be used for logging from streams
        Each complete line (terminated by new line character) gets logged
        at DEBUG level. In complete lines are buffered until the next new line.

        :param name: The name of the logger that will be used.

        """
        self.logger: logging.Logger = logging.getLogger(name)
        self.buffer: str = ''
        if level == logging.DEBUG:
            self.do_write: Callable = self.logger.debug
        elif level == logging.INFO:
            self.do_write = self.logger.info
        elif level == logging.WARNING:
            self.do_write = self.logger.warning
        elif level == logging.ERROR:
            self.do_write = self.logger.error
        else:
            raise Exception('Unknown logging level: {}'.format(level))

    def flush(self) -> 'BaseLogWriter':
        """
        flush base log writer
        """
        # Defined to match the interface expected by pexpect.
        return self

    def close(self) -> 'BaseLogWriter':
        """
        close base log writer
        """
        if self.buffer:
            self.logger.debug(self.buffer)
            self.buffer = ''
        return self

    def __del__(self) -> None:
        # Ensure we don't lose bufferd output
        self.close()


class LogWriter(BaseLogWriter):
    """
    Log writer
    """

    def write(self, data: str) -> 'LogWriter':
        """
        write logs
        """
        data = data.replace('\r\n', '\n').replace('\r', '\n')
        if '\n' in data:
            parts = data.split('\n')
            parts[0] = self.buffer + parts[0]
            for part in parts[:-1]:
                self.do_write(part)
            self.buffer = parts[-1]
        else:
            self.buffer += data
        return self


class LineLogWriter(BaseLogWriter):
    """
    Line log writer
    """

    def write(self, data: str) -> None:
        """
        write logs as lines
        """
        self.do_write(data)


class StreamLogger(threading.Thread):
    """
    Logs output from a stream in a thread.

    """

    def __init__(self, name: str, stream: IO, level: int = logging.DEBUG, klass: Type = LogWriter):
        super(StreamLogger, self).__init__()
        self.writer = klass(name, level)
        self.stream = stream
        self.daemon = True

    def run(self) -> None:
        """
        run the stream logger
        """
        line: str = self.stream.readline()
        while line:
            self.writer.write(line.rstrip('\n'))
            line = self.stream.readline()
        self.writer.close()
