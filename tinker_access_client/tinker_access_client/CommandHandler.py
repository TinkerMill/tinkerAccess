import logging
from Command import Command
from PackageInfo import PackageInfo


class CommandHandler(object):

    def __init__(self, opts=None, args=None):
        self.__logger = logging.getLogger(__name__)
        self.__args = args or []
        self.__opts = opts or {}
        self.__handlers = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def handle_command(self):

        cmd = Command(self.__args[0].lower() if len(self.__args) >= 1 and len(self.__args[0].lower()) >= 1 else None)
        for (command, call_back) in self.__handlers:
            if command is cmd:
                try:
                    return call_back(opts=self.__opts, args=self.__args)
                except Exception as e:
                    self.__logger.debug('%s failed to handle the command.', PackageInfo.pip_package_name)
                    self.__logger.exception(e)
                    raise e

    def on(self, command, call_back):
        self.__handlers.append((command, call_back,))
