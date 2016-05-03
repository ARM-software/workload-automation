
#    Copyright 2014-2015 ARM Limited
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
import re
import time
import logging
from distutils.version import LooseVersion
from wlauto.utils.serial_port import TIMEOUT


logger = logging.getLogger('U-Boot')


class UbootMenu(object):
    """
    Allows navigating Das U-boot menu over serial (it relies on a pexpect connection).

    """

    option_regex = re.compile(r'^\[(\d+)\]\s+([^\r]+)\r\n', re.M)
    prompt_regex = re.compile(r'^([^\r\n]+):\s*', re.M)
    invalid_regex = re.compile(r'Invalid input \(max (\d+)\)', re.M)
    uboot_regex = re.compile(r"U-Boot\s(\d\S*)\s")

    load_delay = 1  # seconds
    default_timeout = 60  # seconds
    fixed_uboot_version = '2016.03'  # The version on U-Boot that fixed newlines

    def __init__(self, conn,
                 start_prompt='Hit any key to stop autoboot'):
        """
        :param conn: A serial connection as returned by ``pexect.spawn()``.
        :param prompt: U-Boot menu prompt
        :param start_prompt: The starting prompt to wait for during ``open()``.

        """
        self.conn = conn
        self.conn.crlf = None
        self.start_prompt = start_prompt
        self.options = {}
        self.prompt = None

    def open(self, timeout=default_timeout):
        """
        "Open" the UEFI menu by sending an interrupt on STDIN after seeing the
        starting prompt (configurable upon creation of the ``UefiMenu`` object.

        """
        self.conn.expect(self.start_prompt, timeout)
        self._set_line_separator()
        self.conn.sendline('')
        time.sleep(self.load_delay)
        self.conn.readline()  # garbage
        self.conn.sendline('')
        self.prompt = self.conn.readline().strip()

    def getenv(self):
        output = self.enter('printenv')
        result = {}
        for line in output.split('\n'):
            if '=' in line:
                variable, value = line.split('=', 1)
                result[variable.strip()] = value.strip()
        return result

    def setenv(self, variable, value, force=False):
        force_str = ' -f' if force else ''
        if value is not None:
            command = 'setenv{} {} {}'.format(force_str, variable, value)
        else:
            command = 'setenv{} {}'.format(force_str, variable)
        return self.enter(command)

    def boot(self):
        self.write_characters('boot')

    def nudge(self):
        """Send a little nudge to ensure there is something to read. This is useful when you're not
        sure if all out put from the serial has been read already."""
        self.enter('')

    def enter(self, value, delay=load_delay):
        """Like ``select()`` except no resolution is performed -- the value is sent directly
        to the serial connection."""
        # Empty the buffer first, so that only response to the input about to
        # be sent will be processed by subsequent commands.
        value = str(value)
        self.empty_buffer()
        self.write_characters(value)
        self.conn.expect(self.prompt, timeout=delay)
        return self.conn.before

    def write_characters(self, line):
        line = line.rstrip('\r\n')
        for c in line:
            self.conn.send(c)
            time.sleep(0.05)
        self.conn.sendline('')

    def empty_buffer(self):
        try:
            while True:
                time.sleep(0.1)
                self.conn.read_nonblocking(size=1024, timeout=0.1)
        except TIMEOUT:
            pass
        self.conn.buffer = ''

    def _set_line_separator(self):
        uboot_text = self.conn.before
        uboot_ver = self.uboot_regex.findall(uboot_text)
        if uboot_ver and LooseVersion(uboot_ver[0]) < LooseVersion(self.fixed_uboot_version):
            self.conn.crlf = "\n\r"
        else:
            self.conn.crlf = "\r\n"
