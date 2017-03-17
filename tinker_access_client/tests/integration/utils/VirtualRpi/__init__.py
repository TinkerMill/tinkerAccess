import sys
import RPi
from tests.integration.utils.VirtualRpi.RPi.GPIO import GPIO


def is_rpi_module(full_name):
    return full_name.endswith('.RPi')


def is_gpio_module(full_name):
    return full_name.endswith('.GPIO')


def is_lcd_module(full_name):
    return full_name.endswith('.lcdModule')


def is_lcd(full_name):
    return full_name.endswith('.LCD')


def is_serial_module(full_name):
    return full_name.endswith('.serial')


def is_device_module(full_name):
    return is_rpi_module(full_name) or is_gpio_module(full_name)


class VirtualRpi(object):

    __gpio = None

    def __init__(self, opts):
        self.__opts = opts
        VirtualRpi.__gpio = GPIO(opts)

    def find_module(self, full_name, _):
        if is_device_module(full_name):
            return self

        return None

    def read_pin(self, pin):
        return self.__gpio.input(pin)

    def write_pin(self, pin, value):
        return self.__gpio.output(pin, value)

    @staticmethod
    def load_module(full_name):
        if is_rpi_module(full_name):
            return RPi

        if is_gpio_module(full_name):
            return VirtualRpi.__gpio

        raise ImportError(full_name)


