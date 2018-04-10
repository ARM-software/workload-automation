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


import os
import stat
import logging
import subprocess
import re
import threading
import tempfile
import shutil
import time

from pexpect import EOF, TIMEOUT, spawn, pxssh

from wlauto.exceptions import HostError, DeviceError, TimeoutError, ConfigError
from wlauto.utils.misc import (which, strip_bash_colors, escape_single_quotes, check_output,
                               CalledProcessErrorWithStderr)

ssh = None
scp = None
sshpass = None

logger = logging.getLogger('ssh')


def ssh_get_shell(host, username, password=None, keyfile=None, port=None, timeout=10, telnet=False, original_prompt=None):
    _check_env()
    start_time = time.time()
    extra_login_args = {}
    while True:
        if telnet:
            if keyfile:
                raise ValueError('keyfile may not be used with a telnet connection.')
            conn = TelnetConnection()
            if original_prompt:
                extra_login_args['original_prompt'] = original_prompt
            if port is None:
                port = 23
        else:  # ssh
            conn = pxssh.pxssh()

        try:
            if keyfile:
                conn.login(host, username, ssh_key=keyfile, port=port, login_timeout=timeout, **extra_login_args)
            else:
                conn.login(host, username, password, port=port, login_timeout=timeout, **extra_login_args)
            break
        except EOF:
            timeout -= time.time() - start_time
            if timeout <= 0:
                message = 'Could not connect to {}; is the host name correct?'
                raise DeviceError(message.format(host))
            time.sleep(5)

    conn.sendline('shopt -s checkwinsize')
    conn.prompt()
    conn.setwinsize(500,200)
    conn.sendline('')
    conn.prompt()
    conn.sendline('stty rows 500')
    conn.prompt()
    conn.sendline('stty cols 200')
    conn.prompt()
    conn.setecho(False)
    return conn


class TelnetConnection(pxssh.pxssh):
    # pylint: disable=arguments-differ

    def login(self, server, username, password='', original_prompt=r'[#$]', login_timeout=10,
              auto_prompt_reset=True, sync_multiplier=1, port=23):
        cmd = 'telnet -l {} {} {}'.format(username, server, port)

        spawn._spawn(self, cmd)  # pylint: disable=protected-access
        try:
            i = self.expect('(?i)(?:password)', timeout=login_timeout)
            if i == 0:
                self.sendline(password)
                i = self.expect([original_prompt, 'Login incorrect'], timeout=login_timeout)
            if i:
                raise pxssh.ExceptionPxssh('could not log in: password was incorrect')
        except TIMEOUT:
            if not password:
                # There was no password prompt before TIMEOUT, and we didn't
                # have a password to enter. Assume everything is OK.
                pass
            else:
                raise pxssh.ExceptionPxssh('could not log in: did not see a password prompt')

        if not self.sync_original_prompt(sync_multiplier):
            self.close()
            raise pxssh.ExceptionPxssh('could not synchronize with original prompt')

        if auto_prompt_reset:
            if not self.set_unique_prompt():
                self.close()
                message = 'could not set shell prompt (recieved: {}, expected: {}).'
                raise pxssh.ExceptionPxssh(message.format(self.before, self.PROMPT))
        return True


def check_keyfile(keyfile):
    """
    keyfile must have the right access premissions in order to be useable. If the specified
    file doesn't, create a temporary copy and set the right permissions for that.

    Returns either the ``keyfile`` (if the permissions on it are correct) or the path to a
    temporary copy with the right permissions.
    """
    desired_mask = stat.S_IWUSR | stat.S_IRUSR
    actual_mask = os.stat(keyfile).st_mode & 0xFF
    if actual_mask != desired_mask:
        tmp_file = os.path.join(tempfile.gettempdir(), os.path.basename(keyfile))
        shutil.copy(keyfile, tmp_file)
        os.chmod(tmp_file, desired_mask)
        return tmp_file
    else:  # permissions on keyfile are OK
        return keyfile


class SshShell(object):

    default_password_prompt = '[sudo] password'
    max_cancel_attempts = 5

    def __init__(self, password_prompt=None, timeout=10, telnet=False):
        self.password_prompt = password_prompt if password_prompt is not None else self.default_password_prompt
        self.timeout = timeout
        self.telnet = telnet
        self.conn = None
        self.lock = threading.Lock()
        self.connection_lost = False

    def login(self, host, username, password=None, keyfile=None, port=None, timeout=None):
        # pylint: disable=attribute-defined-outside-init
        logger.debug('Logging in {}@{}'.format(username, host))
        self.host = host
        self.username = username
        self.password = password
        self.keyfile = check_keyfile(keyfile) if keyfile else keyfile
        self.port = port
        timeout = self.timeout if timeout is None else timeout
        self.conn = ssh_get_shell(host, username, password, self.keyfile, port, timeout, self.telnet)

    def push_file(self, source, dest, timeout=30):
        dest = '{}@{}:{}'.format(self.username, self.host, dest)
        return self._scp(source, dest, timeout)

    def pull_file(self, source, dest, timeout=30):
        source = '{}@{}:{}'.format(self.username, self.host, source)
        return self._scp(source, dest, timeout)

    def background(self, command, stdout=subprocess.PIPE, stderr=subprocess.PIPE):
        port_string = '-p {}'.format(self.port) if self.port else ''
        keyfile_string = '-i {}'.format(self.keyfile) if self.keyfile else ''
        command = '{} {} {} {}@{} {}'.format(ssh, keyfile_string, port_string, self.username, self.host, command)
        logger.debug(command)
        if self.password:
            command = _give_password(self.password, command)
        return subprocess.Popen(command, stdout=stdout, stderr=stderr, shell=True)

    def reconnect(self):
        self.conn = ssh_get_shell(self.host, self.username, self.password,
                                  self.keyfile, self.port, self.timeout, self.telnet)

    def execute(self, command, timeout=None, check_exit_code=True, as_root=False, strip_colors=True):
        try:
            with self.lock:
                if self.connection_lost:
                    logger.debug('Attempting to reconnect...')
                    self.reconnect()
                    self.connection_lost = False
                output = self._execute_and_wait_for_prompt(command, timeout, as_root, strip_colors)
                if check_exit_code:
                    exit_code_text = self._execute_and_wait_for_prompt('echo $?', strip_colors=strip_colors, log=False)
                    try:
                        exit_code = int(exit_code_text.split()[0])
                        if exit_code:
                            message = 'Got exit code {}\nfrom: {}\nOUTPUT: {}'
                            raise DeviceError(message.format(exit_code, command, output))
                    except (ValueError, IndexError):
                        logger.warning('Could not get exit code for "{}",\ngot: "{}"'.format(command, exit_code_text))
                return output
        except EOF:
            self.connection_lost = True
            raise DeviceError('Connection dropped.')

    def logout(self):
        logger.debug('Logging out {}@{}'.format(self.username, self.host))
        self.conn.logout()

    def cancel_running_command(self):
        # simulate impatiently hitting ^C until command prompt appears
        logger.debug('Sending ^C')
        for _ in xrange(self.max_cancel_attempts):
            self.conn.sendline(chr(3))
            if self.conn.prompt(0.1):
                return True
        return False

    def _execute_and_wait_for_prompt(self, command, timeout=None, as_root=False, strip_colors=True, log=True):
        self.conn.prompt(0.1)  # clear an existing prompt if there is one.
        if as_root:
            command = "sudo -- sh -c '{}'".format(escape_single_quotes(command))
            if log:
                logger.debug(command)
            self.conn.sendline(command)
            index = self.conn.expect_exact([self.password_prompt, TIMEOUT], timeout=0.5)
            if index == 0:
                self.conn.sendline(self.password)
            timed_out = self._wait_for_prompt(timeout)
            output = re.sub(r' \r([^\n])', r'\1', self.conn.before)
            output = process_backspaces(output)
            output = re.sub(r'.*?{}'.format(re.escape(command)), '', output, 1).strip()
        else:
            if log:
                logger.debug(command)
            self.conn.sendline(command)
            timed_out = self._wait_for_prompt(timeout)
            # the regex removes line breaks potential introduced when writing
            # command to shell.
            output = re.sub(r' \r([^\n])', r'\1', self.conn.before)
            output = process_backspaces(output)
            command_index = output.find(command)
            output = output[command_index + len(command):].strip()
        if timed_out:
            self.cancel_running_command()
            raise TimeoutError(command, output)
        if strip_colors:
            output = strip_bash_colors(output)
        return output

    def _wait_for_prompt(self, timeout=None):
        if timeout:
            return not self.conn.prompt(timeout)
        else:  # cannot timeout; wait forever
            while not self.conn.prompt(self.timeout):
                pass
            return False

    def _scp(self, source, dest, timeout=30):
        # NOTE: the version of scp in Ubuntu 12.04 occasionally (and bizarrely)
        # fails to connect to a device if port is explicitly specified using -P
        # option, even if it is the default port, 22. To minimize this problem,
        # only specify -P for scp if the port is *not* the default.
        port_string = '-P {}'.format(self.port) if (self.port and self.port != 22) else ''
        keyfile_string = '-i {}'.format(self.keyfile) if self.keyfile else ''
        command = '{} -r {} {} {} {}'.format(scp, keyfile_string, port_string, source, dest)
        pass_string = ''
        logger.debug(command)
        if self.password:
            command = _give_password(self.password, command)
        try:
            check_output(command, timeout=timeout, shell=True)
        except subprocess.CalledProcessError as e:
            raise CalledProcessErrorWithStderr(e.returncode,
                                               e.cmd.replace(pass_string, ''),
                                               output=e.output,
                                               error=getattr(e, 'error', ''))
        except TimeoutError as e:
            raise TimeoutError(e.command.replace(pass_string, ''), e.output)


def _give_password(password, command):
    if not sshpass:
        raise HostError('Must have sshpass installed on the host in order to use password-based auth.')
    pass_string = "sshpass -p '{}' ".format(password)
    return pass_string + command


def _check_env():
    global ssh, scp, sshpass  # pylint: disable=global-statement
    if not ssh:
        ssh = which('ssh')
        scp = which('scp')
        sshpass = which('sshpass')
    if not (ssh and scp):
        raise HostError('OpenSSH must be installed on the host.')


def process_backspaces(text):
    chars = []
    for c in text:
        if c == chr(8) and chars:  # backspace
            chars.pop()
        else:
            chars.append(c)
    return ''.join(chars)
