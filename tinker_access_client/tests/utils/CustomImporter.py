import sys

import MockRPi
import MockLcd
import serial


def add_custom_importer():
    metas = sys.meta_path
    for meta in metas:
        if meta.__class__ is CustomImporter:
            sys.meta_path.remove(meta)
    sys.meta_path.append(CustomImporter())


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
    return is_lcd_module(full_name) or \
           is_lcd(full_name) or \
           is_rpi_module(full_name) or \
           is_gpio_module(full_name) or \
           is_serial_module(full_name)


class CustomImporter(object):

    def find_module(self, full_name, _):
        if is_device_module(full_name):
            return self

        return None

    @staticmethod
    def load_module(full_name):

        if is_rpi_module(full_name):
            return MockRPi

        if is_gpio_module(full_name):
            return MockRPi.GPIO

        if is_lcd_module(full_name):
            return MockLcd

        if is_lcd(full_name):
            return MockLcd.LCD

        if is_serial_module(full_name):
            return serial

        raise ImportError(full_name)
