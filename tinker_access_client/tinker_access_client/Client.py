import time
import threading
from transitions import Machine

from State import State
from PackageInfo import PackageInfo
from ClientLogger import ClientLogger
from DeviceApi import DeviceApi, Channel
from CommandExecutor import CommandExecutor
from AutoUpdateTimer import AutoUpdateTimer
from TinkerAccessServerApi import TinkerAccessServerApi
from ClientOptionParser import ClientOptionParser, ClientOption
from UserRegistrationException import UserRegistrationException
from UnauthorizedAccessException import UnauthorizedAccessException

maximum_lcd_characters = 16
training_mode_delay_seconds = 2
logout_timer_interval_seconds = 1


class Trigger(object):
    IDLE = 'idle'
    LOGIN = 'login'
    LOGOUT = 'logout'
    TERMINATE = 'terminate'


# noinspection PyUnusedLocal
class Client(Machine):
    def __init__(self, device=None, opts=None):
        self.__opts = opts
        self.__device = device
        self.__user_info = None
        self.__logout_timer = None
        self.__logger = ClientLogger.setup(opts)
        self.__tinkerAccessServerApi = TinkerAccessServerApi(opts)

        states = []
        for key, value in vars(State).items():
            if not key.startswith('__'):
                states.append(value)

        transitions = [
            {
                'source': [State.INITIALIZED],
                'trigger': Trigger.IDLE,
                'dest': State.IDLE
            },

            {
                'source': [State.IDLE],
                'trigger': Trigger.LOGIN,
                'dest': State.IN_USE,
                'conditions': ['is_authorized']
            },

            {
                'source': [State.IN_USE],
                'trigger': Trigger.LOGIN,
                'dest': State.IN_USE,
                'conditions': ['should_extend_current_session']
            },

            {
                'source': [State.IN_USE, State.IN_TRAINING],
                'trigger': Trigger.LOGOUT,
                'dest': State.IDLE
            },

            {
                'source': [State.IDLE],
                'trigger': Trigger.LOGOUT,
                'dest': State.IN_TRAINING,
                'conditions': ['is_waiting_for_training']
            },

            {
                'source': '*',
                'trigger': Trigger.TERMINATE,
                'dest': State.TERMINATED
            }
        ]

        Machine.__init__(self, queued=True, states=states,
                         transitions=transitions, initial=State.INITIALIZED, after_state_change='update_status')

    def __enter__(self):
        self.update_status()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.terminate()

    #
    # idle -- The machine is idle and waiting for a badge to be scanned
    #

    def __ensure_idle(self):
        self.__do_logout()
        self.__disable_power()
        self.__show_blue_led()
        self.__show_scan_badge()

    def __do_login(self, *args, **kwargs):
        badge_code = kwargs.get('badge_code')

        # noinspection PyBroadException
        try:
            self.__show_attempting_login(1)
            self.__update_user_context(
                self.__tinkerAccessServerApi.login(badge_code)
            )
            remaining_seconds = self.__user_info.get('remaining_seconds')
            self.__show_access_granted(1)

        except UnauthorizedAccessException as e:
            self.__handle_unauthorized_access_exception()
            self.__ensure_idle()
        except Exception as e:
            self.__handle_unexpected_exception()
            self.__ensure_idle()

        return self.__user_info is not None

    def __show_attempting_login(self, delay=0):
        self.__device.write(
            Channel.LCD,
            'ATTEMPTING'.center(maximum_lcd_characters, ' '),
            'LOGIN...'.center(maximum_lcd_characters, ' ')
        )
        time.sleep(delay)

    def __update_user_context(self, user_info):
        self.__user_info = user_info
        for handler in self.__logger.handlers:
            for context_filter in handler.filters:
                update_user_context = getattr(context_filter, "update_user_context", None)
                if callable(update_user_context):
                    context_filter.update_user_context(self.__user_info)

    def __handle_unauthorized_access_exception(self):
        self.__show_red_led()
        self.__show_access_denied(2)

    def __show_access_denied(self, delay=0):
        self.__device.write(
            Channel.LCD,
            'ACCESS DENIED'.center(maximum_lcd_characters, ' '),
            'TAKE THE CLASS'.center(maximum_lcd_characters, ' ')
        )
        time.sleep(delay)

    def __show_red_led(self):
        self.__device.write(Channel.LED, True, False, False)

    def __do_logout(self):
        self.__cancel_logout_timer()

        if self.__user_info:
            badge_code = self.__user_info.get('badge_code')
            threading.Timer(0, self.__tinkerAccessServerApi.logout, (badge_code, )).start()

        self.__update_user_context(None)

    def __show_blue_led(self):
        self.__device.write(Channel.LED, False, False, True)

    def __show_scan_badge(self):
        self.__device.write(
            Channel.LCD,
            'SCAN BADGE'.center(maximum_lcd_characters, ' '),
            'TO LOGIN'.center(maximum_lcd_characters, ' ')
        )

    #
    # in_use -- The machine is currently in use and the logout timer is ticking...
    #

    def __ensure_in_use(self):
        self.__enable_power()
        self.__show_green_led()

    def __enable_power(self):
        self.__device.write(Channel.PIN, self.__opts.get(ClientOption.PIN_POWER_RELAY), True)

    def __show_access_granted(self, delay=0):
        self.__device.write(
            Channel.LCD,
            'ACCESS GRANTED'.center(maximum_lcd_characters, ' '),
        )
        time.sleep(delay)

    def __show_green_led(self):
        self.__device.write(Channel.LED, False, True, False)

    def __start_logout_timer(self):
        self.__cancel_logout_timer()
        self.__logout_timer = threading.Timer(
            logout_timer_interval_seconds,
            self.__logout_timer_tick
        )
        self.__logout_timer.start()

    def __logout_timer_tick(self):
        if not self.is_terminated() and self.__user_info:
            remaining_seconds = self.__user_info.get('remaining_seconds')

            if remaining_seconds <= 0:
                self.logout()
                return

            self.__user_info['remaining_seconds'] = (remaining_seconds - logout_timer_interval_seconds)
            self.__show_remaining_time()
            self.__start_logout_timer()

    def __show_remaining_time(self):
        remaining_seconds = self.__user_info.get('remaining_seconds')
        if remaining_seconds < 300:
            self.__toggle_red_led()

        m, s = divmod(int(remaining_seconds), 60)
        h, m = divmod(m, 60)
        user_name = self.__user_info.get('user_name')
        self.__device.write(
            Channel.LCD,
            user_name.center(maximum_lcd_characters, ' '),
            '{0:02d}:{1:02d}:{2:02d}'.format(h, m, s).center(maximum_lcd_characters, ' ')
        )

    def __toggle_red_led(self):
        red_led_status = self.__device.read(Channel.PIN, self.__opts.get(ClientOption.PIN_LED_RED))
        self.__device.write(Channel.LED, not red_led_status, False, False)

    def __cancel_logout_timer(self):
        if self.__logout_timer:
            self.__logout_timer.cancel()

        self.__logout_timer = None

    def __extend_session(self):
        self.__cancel_logout_timer()

        # TODO: add api call to let server know that time has been extended...

        session_seconds = self.__user_info.get('session_seconds')
        remaining_seconds = self.__user_info.get('remaining_seconds')
        remaining_extensions = self.__user_info.get('remaining_extensions')

        if remaining_extensions:
            if remaining_extensions != float('inf'):
                self.__user_info['remaining_extensions'] = remaining_extensions - 1

            remaining_seconds = remaining_seconds + session_seconds
            self.__user_info['remaining_seconds'] = remaining_seconds
            self.__logger.info('Session extended %s remaining_seconds', remaining_seconds)

            self.__show_session_extended(1)
        else:
            self.__show_no_extensions_remaining(2)

        self.__start_logout_timer()

    def __show_session_extended(self, delay=0):
        self.__device.write(
            Channel.LCD,
            'SESSION EXTENDED'.center(maximum_lcd_characters, ' ')
        )
        time.sleep(delay)
        self.__show_remaining_time()

    def __show_no_extensions_remaining(self, delay=0):
        self.__device.write(
            Channel.LCD,
            'NO EXTENSIONS'.center(maximum_lcd_characters, ' '),
            'REMAINING...'.center(maximum_lcd_characters, ' ')
        )
        time.sleep(delay)
        self.__show_remaining_time()

    #
    # training - the client has entered training mode
    #

    def __show_training_mode_activated(self, delay=0):
        self.__device.write(
            Channel.LCD,
            'TRAINING MODE'.center(maximum_lcd_characters, ' '),
            'ACTIVATED...'.center(maximum_lcd_characters, ' ')
        )
        time.sleep(delay)

    def __activate_trainer(self, badge_code):
        # Note: currently we call the normal login method on the tinkerAccessServer
        # the backend ensures the user is a trainer on the 'registerUser' call.
        # I expect this might change in the future once the server code gets refactored
        try:
            self.__show_attempting_login(1)
            self.__update_user_context(
                self.__tinkerAccessServerApi.login(badge_code)
            )
            self.__show_trainer_accepted(1)
            self.__prompt_for_student_badge()

        except UnauthorizedAccessException:
            self.__handle_unauthorized_access_exception()
            self.__prompt_for_trainer_badge()
        except Exception as e:
            self.__handle_unexpected_exception()
            self.__prompt_for_trainer_badge()

        return self.__user_info is not None

    def __prompt_for_trainer_badge(self):
        self.__show_blue_led()
        self.__show_scan_trainer_badge()

    def __show_scan_trainer_badge(self):
        self.__device.write(
            Channel.LCD,
            'SCAN'.center(maximum_lcd_characters, ' '),
            'TRAINER BADGE...'.center(maximum_lcd_characters, ' ')
        )

    def __show_trainer_accepted(self, delay=0):
        self.__device.write(
            Channel.LCD,
            'TRAINER'.center(maximum_lcd_characters, ' '),
            'ACCEPTED...'.center(maximum_lcd_characters, ' ')
        )
        time.sleep(delay)

    def __prompt_for_student_badge(self):
        self.__show_blue_led()
        self.__show_scan_student_badge()

    def __show_scan_student_badge(self, delay=0):
        self.__device.write(
            Channel.LCD,
            'SCAN'.center(maximum_lcd_characters, ' '),
            'STUDENT BADGE...'.center(maximum_lcd_characters, ' ')
        )
        time.sleep(delay)

    def __register_student(self, badge_code):
        try:
            self.__show_attempting_registration(1)
            trainer_id = self.__user_info.get('user_id')
            trainer_badge_code = self.__user_info.get('badge_code')
            self.__tinkerAccessServerApi.register_user(trainer_id, trainer_badge_code, badge_code)
            self.__show_student_registered(1)
        except UserRegistrationException:
            self.__handle_user_registration_exception()
            self.__show_invalid_user(2)
        except Exception as e:
            self.__handle_user_registration_exception()
            self.__handle_unexpected_exception()
        finally:
            self.__prompt_for_student_badge()

    def __show_attempting_registration(self, delay=0):
        self.__device.write(
            Channel.LCD,
            'ATTEMPTING'.center(maximum_lcd_characters, ' '),
            'REGISTRATION...'.center(maximum_lcd_characters, ' ')
        )
        time.sleep(delay)

    def __show_student_registered(self, delay=0):
        self.__device.write(
            Channel.LCD,
            'STUDENT'.center(maximum_lcd_characters, ' '),
            'REGISTERED...'.center(maximum_lcd_characters, ' ')
        )
        time.sleep(delay)

    def __handle_user_registration_exception(self):
        self.__show_red_led()
        self.__show_registration_failed(2)

    def __show_registration_failed(self, delay=0):
        self.__device.write(
            Channel.LCD,
            'REGISTRATION'.center(maximum_lcd_characters, ' '),
            'FAILED...'.center(maximum_lcd_characters, ' ')
        )
        time.sleep(delay)

    def __show_invalid_user(self, delay=0):
        self.__device.write(
            Channel.LCD,
            'INVALID'.center(maximum_lcd_characters, ' '),
            'USER...'.center(maximum_lcd_characters, ' ')
        )
        time.sleep(delay)
    #
    # logout/terminated - the user has logged out, or the client is shutting down
    #

    def __disable_power(self):
        if self.__device.read(Channel.PIN, self.__opts.get(ClientOption.PIN_POWER_RELAY)):
            self.__device.write(Channel.PIN, self.__opts.get(ClientOption.PIN_POWER_RELAY), False)
            self.__wait_for_power_down()
            self.__wait_for_logout_coast_time()

    def __wait_for_power_down(self):
        current_sense_pin = self.__opts.get(ClientOption.PIN_CURRENT_SENSE)
        max_power_down_timeout = self.__opts.get(ClientOption.MAX_POWER_DOWN_TIMEOUT)

        current = time.time()
        while time.time() - current < max_power_down_timeout and self.__device.read(Channel.PIN, current_sense_pin):
            self.__show_disabling_power()
            time.sleep(0.1)

    def __wait_for_logout_coast_time(self):
        logout_coast_time = self.__opts.get(ClientOption.LOGOUT_COAST_TIME)
        if logout_coast_time:
            self.__show_coasting_down()
            time.sleep(logout_coast_time)

    def __show_disabling_power(self, delay=0):
        self.__device.write(
            Channel.LCD,
            'DISABLING'.center(maximum_lcd_characters, ' '),
            'POWER...'.center(maximum_lcd_characters, ' ')
        )
        time.sleep(delay)

    def __show_coasting_down(self, delay=0):
        self.__device.write(
            Channel.LCD,
            'COASTING'.center(maximum_lcd_characters, ' '),
            'DOWN...'.center(maximum_lcd_characters, ' ')
        )
        time.sleep(delay)

    def __handle_unexpected_exception(self):
        self.__show_red_led()
        self.__show_error_occurred(2)
        self.__show_please_try_again(2)

    def __show_error_occurred(self, delay=0):
        self.__device.write(
            Channel.LCD,
            'THERE WAS AN'.center(maximum_lcd_characters, ' '),
            'UNEXPECTED ERROR'.center(maximum_lcd_characters, ' ')
        )
        time.sleep(delay)

    def __show_please_try_again(self, delay=0):
        self.__device.write(
            Channel.LCD,
            'PLEASE'.center(maximum_lcd_characters, ' '),
            'TRY AGAIN...'.center(maximum_lcd_characters, ' ')
        )
        time.sleep(delay)
    #
    # a badge code has been detected on the serial input
    #

    def handle_badge_code(self, *args, **kwargs):
        badge_code = kwargs.get('badge_code')
        if self.state == State.IN_TRAINING:
            if not self.__user_info:
                if self.__activate_trainer(badge_code):
                    self.__show_scan_student_badge()
                else:
                    self.__show_scan_trainer_badge()
            else:
                if not self.__is_current_badge_code(*args, **kwargs):
                    self.__register_student(badge_code)
        else:
            self.login(*args, **kwargs)

    #
    # wait - wait for the next edge detection event from the device.
    #

    def wait(self):
        self.__device.wait()

    #
    # status - The client has received a status command
    #

    def status(self):
        return self.state

    def update_status(self, *args, **kwargs):
        status_file = self.__opts.get(ClientOption.STATUS_FILE)
        with open(status_file, 'w') as f:
            f.write('{0}\n'.format(self.status()))
    #
    # conditions - used to allow/prevent triggers causing a transition if the conditions are not met.
    #

    def is_in_use(self):
        return self.status() == State.IN_USE or self.state == State.IN_TRAINING

    def is_terminated(self):
        return self.status() == State.TERMINATED

    def is_authorized(self, *args, **kwargs):
        return self.__do_login(*args, **kwargs)

    def is_waiting_for_training(self, *args, **kwargs):
        current = time.time()
        while not self.is_terminated() and time.time() - current < training_mode_delay_seconds \
                and self.__device.read(Channel.PIN, self.__opts.get(ClientOption.PIN_LOGOUT)):
            time.sleep(0.1)

        return self.__device.read(Channel.PIN, self.__opts.get(ClientOption.PIN_LOGOUT))

    def should_extend_current_session(self, *args, **kwargs):
        if self.__is_current_badge_code(*args, **kwargs):
            self.__extend_session()
            return True
        return False

    def __is_current_badge_code(self, *args, **kwargs):
        new_badge_code = kwargs.get('badge_code')
        current_badge_code = self.__user_info.get('badge_code') if self.__user_info else None

        if current_badge_code and current_badge_code == new_badge_code:
            return True

        return False

    def on_enter_idle(self, *args, **kwargs):
        self.__ensure_idle()
        self.__show_scan_badge()

    def on_enter_in_use(self, *args, **kwargs):
        self.__ensure_in_use()
        self.__start_logout_timer()

    def on_enter_in_training(self, *args, **kwargs):
        self.__ensure_idle()
        self.__show_training_mode_activated(1)
        self.__show_scan_trainer_badge()

    def on_enter_terminated(self, *args, **kwargs):
        self.__ensure_idle()

    @staticmethod
    def run(opts, args):
        logger = ClientLogger.setup(opts)
        reboot_delay = opts.get(ClientOption.REBOOT_DELAY) * 60
        reboot_on_error = opts.get(ClientOption.REBOOT_ON_ERROR)

        try:
            with DeviceApi(opts) as device, \
                    Client(device, opts) as client, \
                    AutoUpdateTimer(client, opts) as auto_update_timer:

                device.on(
                    Channel.SERIAL,
                    direction=device.GPIO.IN,
                    call_back=client.handle_badge_code
                )

                device.on(
                    Channel.PIN,
                    pin=opts.get(ClientOption.PIN_LOGOUT),
                    direction=device.GPIO.RISING,
                    call_back=client.logout
                )

                client.idle()
                auto_update_timer.start()
                while not client.is_terminated():
                    logger.debug('%s is waiting...', PackageInfo.pip_package_name)
                    client.wait()

        except (KeyboardInterrupt, SystemExit) as e:
            pass

        except Exception as e:
            logger.exception(e)

            if reboot_on_error:

                # reboot is only supported on Raspberry PI devices
                # noinspection PyBroadException
                try:
                    # noinspection PyUnresolvedReferences
                    import RPi.GPIO
                    logger.error('Rebooting in %s minutes...', reboot_delay / 60)
                    CommandExecutor().execute_commands([
                        'sleep {0}s'.format(reboot_delay),
                        'reboot now'
                    ])
                except Exception:
                    pass

