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

# Adapted from
# https://gist.github.com/jtriley/1108174
# pylint: disable=bare-except,unpacking-non-sequence
import os
import shlex
import struct
import platform
import subprocess

from typing import Tuple, Optional, Any


def get_terminal_size() -> Tuple[int, int]:
    """ getTerminalSize()
     - get width and height of console
     - works on linux,os x,windows,cygwin(windows)
     originally retrieved from:
     http://stackoverflow.com/questions/566746/how-to-get-console-window-width-in-python
    """
    current_os: str = platform.system()
    tuple_xy: Optional[Tuple[int, int]] = None
    if current_os == 'Windows':
        tuple_xy = _get_terminal_size_windows()
        if tuple_xy is None:
            # needed for window's python in cygwin's xterm
            tuple_xy = _get_terminal_size_tput()
    if current_os in ['Linux', 'Darwin'] or current_os.startswith('CYGWIN'):
        tuple_xy = _get_terminal_size_linux()
    if tuple_xy is None or tuple_xy == (0, 0):
        tuple_xy = (80, 25)      # assume "standard" terminal
    return tuple_xy


def _get_terminal_size_windows() -> Optional[Tuple[int, int]]:
    """
    get terminal size in windows os
    """
    # pylint: disable=unused-variable,redefined-outer-name,too-many-locals, import-outside-toplevel
    try:
        from ctypes import windll, create_string_buffer  # type:ignore
        # stdin handle is -10
        # stdout handle is -11
        # stderr handle is -12
        h = windll.kernel32.GetStdHandle(-12)
        csbi = create_string_buffer(22)
        res = windll.kernel32.GetConsoleScreenBufferInfo(h, csbi)
        if res:
            (bufx, bufy, curx, cury, wattr,
             left, top, right, bottom,
             maxx, maxy) = struct.unpack("hhhhHhhhhhh", csbi.raw)
            sizex: int = right - left + 1
            sizey: int = bottom - top + 1
            return sizex, sizey
    except:  # NOQA
        pass
    return None


def _get_terminal_size_tput() -> Optional[Tuple[int, int]]:
    """
    get terminal size tput
    """
    # get terminal width
    # src: http://stackoverflow.com/questions/263890/how-do-i-find-the-width-height-of-a-terminal-window
    try:
        cols = int(subprocess.check_call(shlex.split('tput cols')))
        rows = int(subprocess.check_call(shlex.split('tput lines')))
        return (cols, rows)
    except:  # NOQA
        pass
    return None


def _get_terminal_size_linux() -> Optional[Tuple[int, int]]:
    """
    get terminal size in linux os
    """
    # pylint: disable=import-outside-toplevel
    def ioctl_GWINSZ(fd: int):
        try:
            import fcntl
            import termios
            cr: Tuple[Any, ...] = struct.unpack('hh',
                                                fcntl.ioctl(fd, termios.TIOCGWINSZ, '1234'))  # type:ignore
            return cr
        except:  # NOQA
            pass
    cr: Optional[Tuple[Any, ...]] = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd: int = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:   # NOQA
            pass
    if not cr:
        try:
            cr = (os.environ['LINES'], os.environ['COLUMNS'])
        except:  # NOQA
            return None
    return int(cr[1]), int(cr[0])


if __name__ == "__main__":
    sizex, sizey = get_terminal_size()
    print('width =', sizex, 'height =', sizey)
