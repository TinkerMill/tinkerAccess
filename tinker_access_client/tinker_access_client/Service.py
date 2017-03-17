#!/usr/bin/env python

# Reference: https://wiki.debian.org/LSBInitScripts

### BEGIN INIT INFO
# Provides:          tinker-access-client
# Required-Start:    $all
# Required-Stop:     $remote_fs $syslog
# Default-Start:     2 3 4 5
# Default-Stop:      0 1 6
# Short-Description: tinker-access-client
# Description:       The tinker-access-client service is responsible for coordinating communication
# between RPi's modules (i.e. RFID reader, LCD, power relays etc..) and the remote tinker_access_server.
### END INIT INFO

import os
import sys
from State import State
from PackageInfo import PackageInfo
from ClientLogger import ClientLogger
from ClientDaemon import ClientDaemon
from CommandHandler import CommandHandler
from ClientOptionParser import ClientOptionParser, Command


def __handle_status_command(opts, args):
    status = ClientDaemon.status(opts, args)
    if status:
        __handle_command_response(['{0}\n'.format(status)], 0)
    else:
        __handle_command_response(['{0}\n'.format(State.TERMINATED)], 1)


def __handle_update_command(opts, args):
    (messages, exit_code) = ClientDaemon.update(opts, args)
    __handle_command_response(messages, exit_code)


def __handle_start_command(opts, args):
    (messages, exit_code) = ClientDaemon.start(opts, args)
    __handle_command_response(messages, exit_code)


def __handle_command_response(messages, exit_code=0):
    if messages:
        for msg in messages:
            sys.stdout.write(msg)
            sys.stdout.flush()
    sys.exit(exit_code)


def run():
    if os.geteuid() != 0:
        sys.stdout.write(
            'You need to have root privileges to run {0} commands.\n'
            'Please try again, this time using \'sudo\'.\n'.format(PackageInfo.pip_package_name))
        sys.stdout.flush()
        sys.exit(1)

    (opts, args) = ClientOptionParser().parse_args()
    logger = ClientLogger.setup(opts)

    try:
        with CommandHandler(opts, args) as handler:
            handler.on(Command.STOP, ClientDaemon.stop)
            handler.on(Command.START, __handle_start_command)
            handler.on(Command.STATUS, __handle_status_command)
            handler.on(Command.UPDATE, __handle_update_command)
            handler.on(Command.REMOVE, ClientDaemon.remove)
            handler.on(Command.RESTART, ClientDaemon.restart)
            return handler.handle_command()

    except Exception as e:
        logger.exception(e)
        sys.stdout.write(str(e))
        sys.stdout.flush()
        sys.exit(1)

if __name__ == '__main__':
    run()
