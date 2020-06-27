import os
import sys
import ConfigParser
from optparse import OptionParser, OptionGroup

from Command import Command
from PackageInfo import PackageInfo
from ClientOption import ClientOption

ClientOptionDefaults = {
    ClientOption.DEBUG: False,
    ClientOption.LOG_LEVEL: 40,
    ClientOption.PIN_LOGOUT: 16,
    ClientOption.PIN_LED_RED: 21,
    ClientOption.DEVICE_ID: None,
    ClientOption.PIN_LED_BLUE: 20,
    ClientOption.REBOOT_DELAY: 300,
    ClientOption.PIN_LED_GREEN: 19,
    ClientOption.AUTO_UPDATE: False,
    ClientOption.FORCE_UPDATE: False,
    ClientOption.PIN_POWER_RELAY: 17,
    ClientOption.PIN_ESTOP: 6,
    ClientOption.USE_ESTOP: False,
    ClientOption.ESTOP_ACTIVE_HI: False,
    ClientOption.PIN_3V3_EN: 27,
    ClientOption.USE_3V3_EN: False,
    ClientOption.LOGOUT_COAST_TIME: 0,
    ClientOption.PIN_CURRENT_SENSE: 12,
    ClientOption.REBOOT_ON_ERROR: False,
    ClientOption.DISPLAY_SERLCD: False,    
    ClientOption.SERIAL_PORT_SPEED: 9600,
    ClientOption.AUTO_UPDATE_INTERVAL: 5,
    ClientOption.MAX_POWER_DOWN_TIMEOUT: None,
    ClientOption.SERIAL_PORT_NAME: '/dev/ttyUSB0',
    ClientOption.SERVER_ADDRESS: 'http://localhost:5000',
    ClientOption.CONFIG_FILE: '/etc/{0}.conf'.format(PackageInfo.pip_package_name),
    ClientOption.PID_FILE: '/var/run/{0}.pid'.format(PackageInfo.pip_package_name),
    ClientOption.LOG_FILE: '/var/log/{0}.log'.format(PackageInfo.pip_package_name),
    ClientOption.STATUS_FILE: '/var/log/{0}.status'.format(PackageInfo.pip_package_name),
    ClientOption.LOGGING_CONFIG_FILE: '/etc/{0}.logging.conf'.format(PackageInfo.pip_package_name)
}


class ClientOptionParser(object):
    def __init__(self, phase=None):
        self.__phase = phase
        self.__parser = OptionParser(
            version='%prog v{0}'.format(PackageInfo.version) if PackageInfo.version is not None else '0.0.0')

        if phase == 'install':
            for arg in sys.argv:
                if str(arg).startswith('-'):
                    self.__parser.add_option(str(arg).split('=', 1)[0])

        usage = "\n%prog command [options]"
        commands = ['\n\ncommand:\n']
        for key, value in vars(Command).items():
            if not key.startswith('__'):
                desc = value['description']
                cmd = value['command']
                commands.append('\t%s : %s' % (cmd, desc))
        commands = '\n'.join(commands)
        usage += commands
        usage += '\n\nTinkerMill Raspberry Pi access control system.' \
                 '\n\nExamples:\n\n' \
                 '  Start the client configured to use a different tinker-access-server ' \
                 '(i.e. a development server) and an alternative serial port' \
                 '\n\n  \'sudo {0} --server-address=http://<server-address> ' \
                 '--serial-port-name=/dev/ttyUSB1\' '.format(PackageInfo.python_package_name)

        self.__parser.set_usage(usage)

        self.__parser.add_option(
            '--config-file',
            help='the location of the config file to use [default:\'%default\'] '
                 'a non-default command-line option value will have precedence '
                 'over a config-file option value',
            default=ClientOptionDefaults[ClientOption.CONFIG_FILE],
            dest=ClientOption.CONFIG_FILE,
            action='store'
        )

        self.__parser.add_option(
            '--logging-config-file',
            help='the location of a logging config file to use [default:\'%default\'] '
                 'If this file is present, it will override the default logging configuration '
                 'including the --log-level and --log-file options',
            default=ClientOptionDefaults[ClientOption.LOGGING_CONFIG_FILE],
            dest=ClientOption.LOGGING_CONFIG_FILE,
            action='store'
        )

        self.__parser.add_option(
            '--debug',
            help='run in the foreground (a.k.a debug mode) [default:\'%default\']',
            default=ClientOptionDefaults[ClientOption.DEBUG],
            dest=ClientOption.DEBUG,
            action='store_true'
        )

        self.__parser.add_option(
            '--force-update',
            help='By default, the update command will not do an update if the current version matches the '
                 'latest version published to PyPI - the Python Package Index. '
                 'This option bypasses the version check, and will force a re-install [default:\'%default\']',
            default=ClientOptionDefaults[ClientOption.FORCE_UPDATE],
            dest=ClientOption.FORCE_UPDATE,
            action='store_true'
        )

        self.__parser.add_option(
            '--auto-update',
            help='periodically check if a newer version of the client has been published '
                 'to PyPI - the Python Package Index. If a new version is found, '
                 'install it automatically. [default:\'%default\']',
            default=ClientOptionDefaults[ClientOption.AUTO_UPDATE],
            dest=ClientOption.AUTO_UPDATE,
            action='store_true'
        )

        self.__parser.add_option(
            '--auto-update-interval',
            help='The period, specified in minutes,that PyPI - the Python Package Index, should '
                 'be checked for a new version of the client. [default:%default]',
            default=ClientOptionDefaults[ClientOption.AUTO_UPDATE_INTERVAL],
            dest=ClientOption.AUTO_UPDATE_INTERVAL,
            type='int',
            action='store'
        )

        self.__parser.add_option(
            '--log-file',
            help='the path and name of the log file [default:\'%default\']',
            default=ClientOptionDefaults[ClientOption.LOG_FILE],
            dest=ClientOption.LOG_FILE,
            action='store'
        )

        self.__parser.add_option(
            '--status-file',
            help='the path and name of the status file, the contents of this file will always '
                 'reflect the current state of the client. (i.e. initialized, idle, in_use, in_training, terminated) '
                 'A missing file indicates the client is not running [default:\'%default\']',
            default=ClientOptionDefaults[ClientOption.STATUS_FILE],
            dest=ClientOption.STATUS_FILE,
            action='store'
        )

        self.__parser.add_option(
            '--pid-file',
            help='the path & name of the pid file [default:\'%default\']',
            default=ClientOptionDefaults[ClientOption.PID_FILE],
            dest=ClientOption.PID_FILE,
            action='store'
        )

        self.__parser.add_option(
            '--log-level',
            help='the log level to use [default:%default]',
            default=ClientOptionDefaults[ClientOption.LOG_LEVEL],
            dest=ClientOption.LOG_LEVEL,
            type='int',
            action='store'
        )

        self.__parser.add_option(
            '--server-address',
            help='the api\'s server address [default:\'%default\']',
            default=ClientOptionDefaults[ClientOption.SERVER_ADDRESS],
            dest=ClientOption.SERVER_ADDRESS,
            action='store'
        )

        self.__parser.add_option(
            '--device-id',
            help='A unique identity for this client [default:\'%default\']',
            default=ClientOptionDefaults[ClientOption.DEVICE_ID],
            dest=ClientOption.DEVICE_ID,
            action='store'
        )

        self.__parser.add_option(
            '--logout-coast-time',
            help='a fixed number of seconds to wait for the physical machine '
                 'to stop after power has been disabled. '
                 '(i.e. a blade to stop spinning etc...) '
                 '[default:%default]',
            default=ClientOptionDefaults[ClientOption.LOGOUT_COAST_TIME],
            dest=ClientOption.LOGOUT_COAST_TIME,
            type='int',
            action='store'
        )

        self.__parser.add_option(
            '--max-power-down-timeout',
            help='the maximum number of seconds to wait for the user to disable power after clicking the logout button'
                 '[default:%default] If None is specified, the system will wait indefinitely',
            default=ClientOptionDefaults[ClientOption.MAX_POWER_DOWN_TIMEOUT],
            dest=ClientOption.MAX_POWER_DOWN_TIMEOUT,
            type='int',
            action='store'
        )

        self.__parser.add_option(
            '--reboot-on-error',
            help='Any unhandled errors will cause the device to reboot after the specified '
                 '--reboot-delay, specified in minutes.'
                 'This behavior is only supported on Raspberry Pi devices. [default:\'%default\']',
            default=ClientOptionDefaults[ClientOption.REBOOT_ON_ERROR],
            dest=ClientOption.REBOOT_ON_ERROR,
            action='store_true'
        )

        self.__parser.add_option(
            '--reboot-delay',
            help='seconds to wait before attempting to reboot the device after an unhandled error [default:%default]',
            default=ClientOptionDefaults[ClientOption.REBOOT_DELAY],
            dest=ClientOption.REBOOT_DELAY,
            type='int',
            action='store'
        )

        self.__parser.add_option(
            '--pin-logout',
            help='the logout pin [default:%default]',
            default=ClientOptionDefaults[ClientOption.PIN_LOGOUT],
            dest=ClientOption.PIN_LOGOUT,
            type='int',
            action='store'
        )

        self.__parser.add_option(
            '--pin-power-relay',
            help='the power relay pin [default:%default]',
            default=ClientOptionDefaults[ClientOption.PIN_POWER_RELAY],
            dest=ClientOption.PIN_POWER_RELAY,
            type='int',
            action='store'
        )

        self.__parser.add_option(
            '--pin-led-red',
            help='the red led pin [default:%default]',
            default=ClientOptionDefaults[ClientOption.PIN_LED_RED],
            dest=ClientOption.PIN_LED_RED,
            type='int',
            action='store'
        )

        self.__parser.add_option(
            '--pin-led-green',
            help='the green led pin [default:%default]',
            default=ClientOptionDefaults[ClientOption.PIN_LED_GREEN],
            dest=ClientOption.PIN_LED_GREEN,
            type='int',
            action='store'
        )

        self.__parser.add_option(
            '--pin-led-blue',
            help='the blue led pin [default:%default]',
            default=ClientOptionDefaults[ClientOption.PIN_LED_BLUE],
            dest=ClientOption.PIN_LED_BLUE,
            type='int',
            action='store'
        )

        self.__parser.add_option(
            '--pin-current-sense',
            help='the current sense pin [default:%default]',
            default=ClientOptionDefaults[ClientOption.PIN_CURRENT_SENSE],
            dest=ClientOption.PIN_CURRENT_SENSE,
            type='int',
            action='store'
        )

        self.__parser.add_option(
            '--pin-estop',
            help='the e-stop pin [default:%default]',
            default=ClientOptionDefaults[ClientOption.PIN_ESTOP],
            dest=ClientOption.PIN_ESTOP,
            type='int',
            action='store'
        )

        self.__parser.add_option(
            '--pin-3v3-en',
            help='the 3.3V enable pin [default:%default]',
            default=ClientOptionDefaults[ClientOption.PIN_3V3_EN],
            dest=ClientOption.PIN_3V3_EN,
            type='int',
            action='store'
        )

        self.__parser.add_option(
            '--use-estop',
            help='use the e-stop pin to detect an e-stop event [default:%default]',
            default=ClientOptionDefaults[ClientOption.USE_ESTOP],
            dest=ClientOption.USE_ESTOP,
            action='store_true'
        )

        self.__parser.add_option(
            '--estop-active-hi',
            help='an e-stop event is an active high logic level [default:%default]',
            default=ClientOptionDefaults[ClientOption.ESTOP_ACTIVE_HI],
            dest=ClientOption.ESTOP_ACTIVE_HI,
            action='store_true'
        )

        self.__parser.add_option(
            '--use-3v3-en',
            help='use the 3.3v enable pin function [default:\'%default\']',
            default=ClientOptionDefaults[ClientOption.USE_3V3_EN],
            dest=ClientOption.USE_3V3_EN,
            action='store_true'
        )

        self.__parser.add_option(
            '--serial-port-name',
            help='the serial port name to use [default:\'%default\']',
            default=ClientOptionDefaults[ClientOption.SERIAL_PORT_NAME],
            dest=ClientOption.SERIAL_PORT_NAME,
            action='store'
        )

        self.__parser.add_option(
            '--serial-port-speed',
            help='the serial port speed to use [default:%default]',
            default=ClientOptionDefaults[ClientOption.SERIAL_PORT_SPEED],
            dest=ClientOption.SERIAL_PORT_SPEED,
            type='int',
            action='store'
        )

        self.__parser.add_option(
            '--display-serlcd',
            help='The SparkFun LCD-14072 SerLCD display is connected. '
                 'If this flag is not set, then the original backpack style display '
                 'is assumed to be connected. [default:\'%default\']',
            default=ClientOptionDefaults[ClientOption.DISPLAY_SERLCD],
            dest=ClientOption.DISPLAY_SERLCD,
            action='store_true'
        )

    def parse_args(self, args=None, values=None):
        (opts, args) = self.__parser.parse_args(args=args, values=values)
        items = vars(opts)

        options = self.__parser.option_list[:]
        for group in self.__parser.option_groups:
            options = options + group.option_list[:]

        if os.path.isfile(items.get(ClientOption.CONFIG_FILE)):
            config_file_parser = ConfigParser.RawConfigParser()
            config_file_parser.read(items.get(ClientOption.CONFIG_FILE))
            for item in config_file_parser.items('config'):
                option = next((i for i in options if i.dest == item[0]), None)
                if option:

                    key = item[0]
                    value = item[1]
                    if option.type == 'int':
                        value = int(value)

                    if option.type == 'float':
                        value = float(value)

                    if option.action == 'store_true':
                        value = value.lower() == 'true'

                    if option.action == 'store_false':
                        value = value.lower() == 'false'

                    # prevents non-default command-line options from being replaced by config-file options
                    if items.get(key) == option.default != value:
                        items[key] = value

        # TODO: make args[0] required?, check the value and raise error parser.error()
        return items, args
