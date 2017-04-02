import os
import time
import signal
import subprocess
from subprocess import CalledProcessError

from State import State
from Client import Client
from Command import Command
from daemonize import Daemonize
from PackageInfo import PackageInfo
from ClientOption import ClientOption
from ClientLogger import ClientLogger
from LoggedRequest import LoggedRequest
from CommandExecutor import CommandExecutor


# noinspection PyClassHasNoInit
class ClientDaemon:

    @staticmethod
    def start(opts, args):
        logger = ClientLogger.setup(opts)
        if not ClientDaemon.status(opts, args):
            pid_file = opts.get(ClientOption.PID_FILE)
            foreground = opts.get(ClientOption.DEBUG)

            def start():
                Client.run(opts, args)

            daemon = Daemonize(
                app=PackageInfo.pip_package_name,
                pid=pid_file,
                action=start,
                foreground=foreground,
                verbose=True,
                logger=logger,
                auto_close_fds=False
            )
            daemon.start()
            return [], 0
        else:
            return ['{0} is already running...\n'.format(PackageInfo.pip_package_name)], 1

    #TODO: need to cover scenario of machine is in use, and stop command is recieved

    @staticmethod
    def stop(opts, args):
        logger = ClientLogger.setup(opts)
        pid_file = opts.get(ClientOption.PID_FILE)
        logout_coast_time = opts.get(ClientOption.LOGOUT_COAST_TIME)

        try:
            for process_id in ClientDaemon.__get_process_ids():
                try:
                    os.kill(process_id, signal.SIGTERM)
                except Exception as e:
                    logger.exception(e)
        except CalledProcessError:
            pass

        # Wait for what we assume will be a graceful exit,
        # this will exit early if the pid file is removed as expected.
        current = time.time()
        max_wait_time = logout_coast_time + 5
        while time.time() - current < max_wait_time and os.path.isfile(pid_file):
            time.sleep(0.1)

        # This should never happen, but... if the pid file still exist at this point, we will nuke it from orbit!
        # Otherwise it will prevent the client daemon from starting again...
        if os.path.isfile(pid_file):
            try:
                os.remove(pid_file)
            except Exception as e:
                logger.exception(e)

    @staticmethod
    def update(opts, args):
        if not ClientDaemon.__is_in_use(opts, args):
            logger = ClientLogger.setup(opts)
            requested_version = args[1] if len(args) >= 2 else None
            if ClientDaemon.__should_update(opts, requested_version):
                try:
                    requested_package = PackageInfo.pip_package_name

                    # BUG: There is a big fat bug with pip that is causing it to redirect to
                    # install the latest version, even when a specific version is installed.
                    # I'll look into this when I get time.

                    if requested_version:
                        requested_package = '{0}=={1}'.format(requested_package, requested_version)

                    ClientDaemon.stop(opts, args)
                    CommandExecutor().execute_commands([
                        'pip install --upgrade --force-reinstall --ignore-installed --no-cache-dir {0}'
                        .format(requested_package)
                    ])
                except Exception as e:
                    msg = '{0} update failed, remediation maybe required!'.format(PackageInfo.pip_package_name)
                    logger.error(msg)
                    logger.exception(e)
                    raise e
                finally:
                    if not ClientDaemon.status(opts, args):
                        ClientDaemon.restart(opts, args)
            else:

                force_update_hint = 'Use the --force-update option to bypass ' \
                                    'the version check and re-install from PyPi.\n'\
                                    .format(
                                        PackageInfo.pip_package_name,
                                        PackageInfo.version
                                    )

                if not PackageInfo.version:
                    return [
                        'You are currently using a non-versioned build...\n',
                        force_update_hint
                    ], 1

                version = 'latest' if not requested_version else 'requested'
                return [
                    '{0} v{1} already matches the {2} version. \n'
                    'Use the --force-update option to bypass the version check and re-install.\n'.format(
                        PackageInfo.pip_package_name,
                        PackageInfo.version,
                        version
                    )], 1
        else:
            return ['{0} is currently in use, try again later...\n'.format(PackageInfo.pip_package_name)], 1

    @staticmethod
    def __get_latest_version_from_pypi():
        response = LoggedRequest.get('https://pypi.python.org/pypi/{0}/json'.format(PackageInfo.pip_package_name))
        response.raise_for_status()
        data = response.json()
        latest_version = data.get('info', {}).get('version', '0.0.0')
        return '.'.join([s.zfill(2) for s in latest_version.split('.')])

    @staticmethod
    def __should_update(opts, requested_version=None):
        logger = ClientLogger.setup(opts)
        try:
            if opts.get(ClientOption.FORCE_UPDATE):
                return True

            current_version = PackageInfo.version
            if current_version:
                if not requested_version:
                    return current_version != ClientDaemon.__get_latest_version_from_pypi()

                requested_version = '.'.join([s.zfill(2) for s in requested_version.split('.')])
            return current_version != requested_version
        except Exception as e:
            logger.exception(e)
        return False

    @staticmethod
    def restart(opts, args):
        logger = ClientLogger.setup(opts)
        reboot_delay = opts.get(ClientOption.REBOOT_DELAY)
        logout_coast_time = opts.get(ClientOption.LOGOUT_COAST_TIME)
        try:
            args[0] = Command.STOP.get('command')
            ClientDaemon.stop(opts, args)
            time.sleep(logout_coast_time)
            logger.debug('Restarting in %s seconds...', reboot_delay)
            time.sleep(reboot_delay)
            args[0] = Command.START.get('command')
            ClientDaemon.start(opts, args)
        except Exception as e:
            msg = '{0} restart failed.'.format(PackageInfo.pip_package_name)
            logger.error(msg)
            logger.exception(e)
            raise e

    @staticmethod
    def remove(opts, args):
        try:
            CommandExecutor().execute_commands([
                '{'
                '\tset +e',
                '\tservice tinker-access-client stop',
                '\tupdate-rc.d -f tinker-access-client remove',
                '\trm -rf /etc/init.d/tinker-access-client',
                '\twhile [[ $(pip uninstall tinker-access-client -y) == 0 ]]; do :; done',
                '\tfind /usr/local/lib/python2.7/dist-packages/ -name \'tinker[_-]access[_-]client*\' -type d -exec sudo rm -r "{}" \;',
                '\tsed -i.bak \'/^\/.*\/tinker_access_client$/s///g\' /usr/local/lib/python2.7/dist-packages/easy-install.pth',
                '} &> /dev/null'
            ])
        except Exception:
            pass

    @staticmethod
    def status(opts, _):
        status_file = opts.get(ClientOption.STATUS_FILE)

        process_ids = ClientDaemon.__get_process_ids()
        status = terminated = State.TERMINATED
        if os.path.isfile(status_file):
            with open(status_file, 'r') as f:
                status = f.readline().strip()

        return status if status is not terminated and len(process_ids) > 0 else None

    @staticmethod
    def __is_in_use(opts, args):
        status = ClientDaemon.status(opts, args)
        return status == State.IN_USE or status == State.IN_TRAINING

    @staticmethod
    def __get_process_ids():
        process_ids = []

        try:
            cmd = ['pgrep', '-f', '(/{0}\s+(start|restart|update))'.format(PackageInfo.pip_package_name)]
            for process_id in subprocess.check_output(cmd).splitlines():
                process_id = int(process_id)
                is_current_process = process_id == int(os.getpid())
                if not is_current_process:
                    process_ids.append(process_id)
        except CalledProcessError:
            pass

        return process_ids
