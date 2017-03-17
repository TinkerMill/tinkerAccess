import os
import time

from PackageInfo import PackageInfo
from ClientLogger import ClientLogger
from CommandExecutor import CommandExecutor


class ServiceInstaller(object):
    def __init__(self, install_lib):
        self.__logger = ClientLogger.setup(phase='install')
        self.__command_executor = CommandExecutor(phase='install')

        self.__install_lib = install_lib
        self.__service_link = "/etc/init.d/{0}".format(PackageInfo.pip_package_name)
        self.__service_script = '{0}{1}/Service.py'.format(install_lib, PackageInfo.python_package_name)

    def install(self):
        try:
            self.__create_service()
            self.__configure_service()
            self.__restart_service()

        except Exception as e:
            self.__logger.debug('%s service installation failed.', PackageInfo.pip_package_name)
            self.__logger.exception(e)
            raise e

    def __create_service(self):
        self.__command_executor.ensure_execute_permission(self.__service_script)

        # remove any existing service if it is a file or directory, and it is not a symlink
        if os.path.exists(self.__service_link) and not os.path.islink(self.__service_link):
            os.remove(self.__service_link)

        # remove the existing service if it is a symlink and it is not pointed to the current target
        if os.path.lexists(self.__service_link) and os.readlink(self.__service_link) != self.__service_script:
            os.remove(self.__service_link)

        # create the symlink if it doesn't already exists
        if not os.path.lexists(self.__service_link):
            os.symlink(self.__service_script, self.__service_link)

    def __configure_service(self):
        time.sleep(5)
        self.__command_executor.execute_commands([
            'update-rc.d -f {0} defaults 91\n'.format(PackageInfo.pip_package_name)
        ])

    def __restart_service(self):
        time.sleep(5)
        self.__command_executor.execute_commands([
            'service {0} restart\n'.format(PackageInfo.pip_package_name)
        ])




