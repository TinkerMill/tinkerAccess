import time
import math
import json
import serial
import logging
import threading
from LcdApi import LcdApi
from ClientOptionParser import ClientOption


class Channel(object):
    LCD, SERIAL, LED, PIN = range(0, 4)

    def __new__(cls, channel):
        for key, value in vars(Channel).items():
            if not key.startswith('__'):
                if value == channel:
                    return key
        return None


class DeviceApi(object):

    def __init__(self, opts):
        self.__opts = opts
        self.__fault = None
        self.__should_exit = False
        self.__edge_detected = False
        self.__first_line = ""
        self.__second_line = ""
        self.__lcd_refresh_timer = None
        self.__write_lcd_lock = threading.Lock()
        self.__logger = logging.getLogger(__name__)

    def __enter__(self):
        try:
            self.__configure_gpio()
            self.__configure_serial()
        except (RuntimeError, ImportError) as e:
            self.__logger.exception(e)
            raise e
        except Exception as e:
            self.__logger.debug(
                'Device initialization failed with %s.',
                json.dumps(self.__opts, indent=4, sort_keys=True))
            self.__logger.exception(e)
            raise e
        return self

    def __configure_gpio(self):
        # noinspection PyUnresolvedReferences
        import RPi.GPIO as GPIO
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.__opts.get(ClientOption.PIN_LED_RED), GPIO.OUT)
        GPIO.setup(self.__opts.get(ClientOption.PIN_LED_BLUE), GPIO.OUT)
        GPIO.setup(self.__opts.get(ClientOption.PIN_LED_GREEN), GPIO.OUT)
        GPIO.setup(self.__opts.get(ClientOption.PIN_POWER_RELAY), GPIO.OUT)
        GPIO.setup(self.__opts.get(ClientOption.PIN_LOGOUT), GPIO.IN, GPIO.PUD_DOWN)

        # No pulldown for current sense pin, it will alter the RC time constant of the detect circuit
        GPIO.setup(self.__opts.get(ClientOption.PIN_CURRENT_SENSE), GPIO.IN, GPIO.PUD_OFF)

        if self.__opts.get(ClientOption.USE_ALARM):
            GPIO.setup(self.__opts.get(ClientOption.PIN_ALARM), GPIO.OUT)

        # If using programmable current threshold, set the pin as output high initially before PWM is enabled. If not using
        # the programmable threshold, set the pin to an input so it does not potentially contend with previous PCB revisions,
        # but enable the weak pullup so the threshold will float high, which will prevent the detection from triggering. 
        if self.__opts.get(ClientOption.USE_PGM_CURRENT_THRESHOLD):
            GPIO.setup(self.__opts.get(ClientOption.PIN_CURRENT_THRESHOLD), GPIO.OUT, initial=GPIO.HIGH)
        else:
            GPIO.setup(self.__opts.get(ClientOption.PIN_CURRENT_THRESHOLD), GPIO.IN, GPIO.PUD_UP)

        if self.__opts.get(ClientOption.USE_3V3_EN):
            # Toggle the 3.3V enable to reset I2C devices
            GPIO.setup(self.__opts.get(ClientOption.PIN_3V3_EN), GPIO.OUT)
            GPIO.output(self.__opts.get(ClientOption.PIN_3V3_EN), GPIO.LOW)
            time.sleep(1)
            GPIO.output(self.__opts.get(ClientOption.PIN_3V3_EN), GPIO.HIGH)
            time.sleep(2)

        if self.__opts.get(ClientOption.USE_ESTOP):
            if self.__opts.get(ClientOption.ESTOP_ACTIVE_HI):
                GPIO.setup(self.__opts.get(ClientOption.PIN_ESTOP), GPIO.IN, GPIO.PUD_UP)
            else:
                GPIO.setup(self.__opts.get(ClientOption.PIN_ESTOP), GPIO.IN, GPIO.PUD_DOWN)

        if self.__opts.get(ClientOption.USE_BYPASS_DETECT):
            GPIO.setup(self.__opts.get(ClientOption.PIN_BYPASS_DETECT), GPIO.IN, GPIO.PUD_UP)

        self.GPIO = GPIO

        self.__configure_pwm()

    def __configure_pwm(self):

        if self.__opts.get(ClientOption.USE_PGM_CURRENT_THRESHOLD):

            # Use pigpio for the current sense threshold PWM output as the RPi.GPIO PWM jitter is not very good
            import pigpio
            PIGPIO = pigpio.pi()

            # Set some parameters needed for PWM calcs
            pin_current_threshold = self.__opts.get(ClientOption.PIN_CURRENT_THRESHOLD)
            Rb = self.__opts.get(ClientOption.CT_BURDEN_RESISTOR)
            turns = self.__opts.get(ClientOption.CT_TURNS_RATIO)
            Vcc = 3.3

            # Attempt to set the PWM frequency and duty cycle range then get the actual values and adjust duty cycle to the real value
            PIGPIO.set_PWM_frequency(pin_current_threshold, 4000)
            PIGPIO.set_PWM_range(pin_current_threshold, 100)
            pwm_freq = PIGPIO.get_PWM_frequency(pin_current_threshold)
            pwm_range = PIGPIO.get_PWM_real_range(pin_current_threshold)
            PIGPIO.set_PWM_range(pin_current_threshold, pwm_range)

            max_threshold_in_amps_rms = Vcc / math.sqrt(2) / Rb * turns
            amps_resolution = max_threshold_in_amps_rms / pwm_range

            self.__logger.info('Current sense PWM setup: Rb: %d ohms, CT: %d:1, PWM Freq: %d, PWM Steps: %d, Max threshold: %.2f Amps(RMS), Step size: %.3f Amps(RMS).',
                               Rb, turns, pwm_freq, pwm_range, max_threshold_in_amps_rms, amps_resolution)

            pwm_dutycycle_raw = min(int(round(self.__opts.get(ClientOption.CURRENT_DETECT_SETTING) / 1000.0 / max_threshold_in_amps_rms * pwm_range)), pwm_range)
            pwm_dutycycle_pct = 100.0 * pwm_dutycycle_raw / pwm_range
            pwm_amps = pwm_dutycycle_raw * amps_resolution
            pwm_volts = Vcc * pwm_dutycycle_raw / pwm_range

            self.__logger.info('Current sense PWM setting: PWM Duty Cycle: %d (%.1f%%), PWM Output: %.3f Volts, Current Threshold Setting: %.2f Amps(RMS)',
                               pwm_dutycycle_raw, pwm_dutycycle_pct, pwm_volts, pwm_amps)

            PIGPIO.set_PWM_dutycycle(pin_current_threshold, pwm_dutycycle_raw)

            self.PIGPIO = PIGPIO

        else:
            self.PIGPIO = None

    def __configure_serial(self):
        serial_port_name = self.__opts.get(ClientOption.SERIAL_PORT_NAME)
        serial_port_speed = self.__opts.get(ClientOption.SERIAL_PORT_SPEED)
        self.__serial_connection = serial.Serial(serial_port_name, serial_port_speed)
        self.__serial_connection.flushInput()
        self.__serial_connection.flushOutput()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__stop()
        self.__do_cleanup()

    def __stop(self):
        self.__should_exit = True

    # noinspection PyBroadException
    def __do_cleanup(self):
        try:
            self.__write_to_led(True, False, False)
            self.__write_to_lcd('System Offline!', 'Try later...')
            self.__cancel_lcd_refresh_timer()
        except Exception:
            pass
        finally:
            if self.PIGPIO:
                self.PIGPIO.stop()
            self.GPIO.cleanup()

    def __do_callback(self, call_back, *args, **kwargs):
        try:
            call_back(*args, **kwargs)
        except Exception as e:
            self.__fault = e
            self.__stop()
        finally:
            self.__edge_detected = True

    def __poll_for_serial_input(self, call_back):
        while not self.__should_exit:
            try:
                badge_code = self.read(Channel.SERIAL)
                if badge_code:
                    self.__do_callback(call_back, badge_code=badge_code)
            except Exception as e:
                self.__fault = e
                self.__stop()
            time.sleep(.5)

    def __read_from_serial(self):
        serial_connection = self.__serial_connection

        if serial_connection.inWaiting() > 1:
            value = serial_connection.readline().strip()[-12:]
            serial_connection.flushInput()
            serial_connection.flushOutput()
            return value

        return None

    def __read_from_pin(self, pin, expected_state):
        # noinspection PyPep8Naming
        GPIO = self.GPIO
        expected_state = GPIO.LOW if not expected_state else GPIO.HIGH
        return GPIO.input(pin) == expected_state

    def __write_to_led(self, red, green, blue):
        # noinspection PyPep8Naming
        GPIO = self.GPIO
        GPIO.output(self.__opts.get(ClientOption.PIN_LED_RED), red)
        GPIO.output(self.__opts.get(ClientOption.PIN_LED_GREEN), green)
        GPIO.output(self.__opts.get(ClientOption.PIN_LED_BLUE), blue)

        # Retry backlight write multiple times, then raise error if unsuccessful
        num_attempts = 5
        for attempt in range(num_attempts):
            try:
                self.__call_lcd_backlight(red, green, blue)
            except Exception as e:
                if attempt == (num_attempts-1):
                    # All attempts exhausted, report as fatal
                    raise e
            else:
                break

    def __call_lcd_backlight(self, red, green, blue):
        try:
            with LcdApi(self.__opts, False) as lcd:
                lcd.rgb_backlight(red, green, blue)
        except Exception as e:
            self.__logger.debug('LCD I2C write backlight failed with colors \'%d %d %d\'.', red, green, blue)
            self.__logger.exception(e)
            raise e

    def __write_to_lcd(self, first_line, second_line, refresh=False):
        # Get the lock to allow only one thread to call the LCD write at a time
        self.__write_lcd_lock.acquire()

        # If not a refresh write, update the stored lines
        if not refresh:
            self.__first_line = first_line
            self.__second_line = second_line

        # Retry write multiple times, then raise error if unsuccessful
        num_attempts = 5
        for attempt in range(num_attempts):
            try:
                self.__call_lcd_write(self.__first_line, self.__second_line)
            except Exception as e:
                if attempt == (num_attempts-1):
                    # All attempts exhausted, report as fatal and make sure to release the lock
                    self.__write_lcd_lock.release()
                    raise e
            else:
                break

        self.__write_lcd_lock.release()

    def __call_lcd_write(self, first_line, second_line):
        try:
            self.__cancel_lcd_refresh_timer()
            with LcdApi(self.__opts) as lcd:
                lcd.write(first_line, second_line)
        except Exception as e:
            self.__logger.debug('LCD I2C write message failed with message \'%s %s\'.', first_line, second_line)
            self.__logger.exception(e)
            raise e

        self.__start_lcd_refresh_timer()

    def __cancel_lcd_refresh_timer(self):
        if self.__lcd_refresh_timer:
            self.__lcd_refresh_timer.cancel()

        self.__lcd_refresh_timer = None

    def __lcd_refresh_timer_tick(self):
        try:
            if not self.__should_exit:
                self.__write_to_lcd("", "", True)
        except Exception as e:
            self.__fault = e
            self.__stop()

    def __start_lcd_refresh_timer(self, interval=30):
        self.__cancel_lcd_refresh_timer()
        self.__lcd_refresh_timer = threading.Timer(
            interval,
            self.__lcd_refresh_timer_tick
        )
        self.__lcd_refresh_timer.start()

    def __write_to_pin(self, pin, state):
        # noinspection PyPep8Naming
        GPIO = self.GPIO
        state = GPIO.LOW if not state else GPIO.HIGH
        GPIO.output(pin, state)

    def on(self, channel, **kwargs):
        pin = kwargs.get('pin')
        direction = kwargs.get('direction')
        call_back = kwargs.get('call_back')

        # noinspection PyPep8Naming
        GPIO = self.GPIO
        if channel is Channel.PIN and pin and direction and call_back:

            def rising_edge_detected(*args, **kwargs):
                pin = args[0]
                time.sleep(.1)
                if GPIO.input(pin):
                    self.__do_callback(call_back, args, kwargs)

            def falling_edge_detected(*args, **kwargs):
                pin = args[0]
                time.sleep(.1)
                if not GPIO.input(pin):
                    self.__do_callback(call_back, args, kwargs)

            def both_edge_detected(*args, **kwargs):
                time.sleep(.5)
                self.__do_callback(call_back, args, kwargs)

            if direction == self.GPIO.RISING:
                GPIO.add_event_detect(pin, direction, callback=rising_edge_detected, bouncetime=500)
            elif direction == self.GPIO.FALLING:
                GPIO.add_event_detect(pin, direction, callback=falling_edge_detected, bouncetime=500)
            elif direction == self.GPIO.BOTH:
                GPIO.add_event_detect(pin, direction, callback=both_edge_detected, bouncetime=500 )
            else:
                raise NotImplementedError

        elif channel is Channel.SERIAL and direction is self.GPIO.IN and call_back:
            poll_for_serial_input = threading.Thread(
                name='poll_for_serial_input',
                target=self.__poll_for_serial_input,
                args=(call_back,)
            )
            poll_for_serial_input.daemon = True
            poll_for_serial_input.start()

        else:
            raise NotImplementedError

    def read(self, channel, *args):
        if self.__should_exit:
            return

        channel_name = Channel(channel)
        try:

            if channel == Channel.SERIAL:
                value = self.__read_from_serial()

            elif channel == Channel.PIN:
                pin = args[0] if len(args) >= 1 else None
                expected_state = args[1] if len(args) >= 2 else True
                value = self.__read_from_pin(pin, expected_state)

            else:
                raise NotImplementedError

        except Exception as e:
            self.__logger.debug('Read from %s failed with args \'%s\'.', channel_name, args)
            self.__logger.exception(e)
            raise e

        return value

    def write(self, channel, *args):
        if self.__should_exit:
            return

        channel_name = Channel(channel)
        try:
            if channel == Channel.LED:
                red = len(args) >= 1 and args[0] is True
                green = len(args) >= 2 and args[1] is True
                blue = len(args) >= 3 and args[2] is True
                self.__write_to_led(red, green, blue)

            elif channel == Channel.LCD:
                first_line = args[0] if len(args) >= 1 else ''
                second_line = args[1] if len(args) >= 2 else ''
                self.__write_to_lcd(first_line, second_line)

            elif channel == Channel.PIN:
                pin = args[0] if len(args) >= 1 else None
                state = args[1] if len(args) >= 2 else None
                self.__write_to_pin(pin, state)

            else:
                raise NotImplementedError

        except Exception as e:
            self.__logger.debug('Write to \'%s\' failed with args \'%s\'.', channel_name, args)
            self.__logger.exception(e)
            raise e

    def wait(self):
        while not self.__should_exit and not self.__edge_detected:
            time.sleep(1)
        self.__edge_detected = False
        self.__raise_fault()

    def __raise_fault(self):
        if self.__fault:
            raise self.__fault

