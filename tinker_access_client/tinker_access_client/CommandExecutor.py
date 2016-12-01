import os
import tempfile
import subprocess

from ClientLogger import ClientLogger


class CommandExecutor(object):

    def __init__(self, phase=None):
        #TODO: going to need to pass in opts for clientLogger
        self.__logger = ClientLogger.setup(phase=phase)

    def ensure_execute_permission(self, path):
        try:
            os.chmod(path, 0755)
        except Exception as e:
            self.__logger.exception(e)
            raise e

    def execute_commands(self, commands):

        # I suppose an explanation is warranted here...
        # Unfortunately we cannot execute these commands directly from python due to the fact that the
        # start priority 91 must be passed to the update-rc command as an integer and python converts all arguments to
        # strings which causes and exception when the update command is invoked.
        # We work around the problem by creating a temporary script file and executing that

        fd, path = tempfile.mkstemp()
        try:

            with os.fdopen(fd, 'w') as tmp:
                tmp.writelines(['#!/usr/bin/env bash\n\n'] + ['{0}\n'.format(command) for command in commands])
            self.ensure_execute_permission(path)
            self.execute_command(path)
        finally:
            os.remove(path)

    def execute_command(self, command):
        try:
            cmd = [command] + ['-evx']  # Options: http://www.tldp.org/LDP/abs/html/options.html
            cmd_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout_data, stderr_data = cmd_process.communicate()
            if cmd_process.returncode != 0:
                for ln in stderr_data.splitlines(True):
                    self.__logger.error(ln)
                raise RuntimeError('{0} command failed.\n'.format(cmd))
            else:
                for ln in stdout_data.splitlines(True):
                    self.__logger.debug(ln)
        except RuntimeError as e:
            raise e
        except Exception as e:
            self.__logger.exception(e)
            raise e
