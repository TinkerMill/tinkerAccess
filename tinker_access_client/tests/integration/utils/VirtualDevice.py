from __future__ import absolute_import

import sys
import time
import threading

import serial
import smbus2 as smbus
from mock import patch, Mock

from tinker_access_client.tinker_access_client.Client import Client
from tinker_access_client.tinker_access_client.ClientOption import ClientOption

from tests.integration.utils.VirtualRpi import VirtualRpi
from tinker_access_client.tests.integration.utils.VirtualSerial import VirtualSerial


update_status = Client.update_status


class VirtualDevice(object):

    def __init__(self, opts):
        self.__opts = opts
        self.__displays = []
        self.__client = None
        self.__transitions = []
        self.__virtual_rpi = VirtualRpi(opts)
        self.__virtual_serial = VirtualSerial()

	self.__lcd_patcher = patch.object(smbus, 'SMBus', return_value=Mock())
	self.__lcd_patcher.start()

        #TODO: should only patch if the address, matches the option for the serial address
        self.__serial_patcher = patch.object(serial, 'Serial', return_value=self.__virtual_serial)
        self.__serial_patcher.start()

        self.__client__update_status = patch.object(Client, 'update_status', side_effect=self.__update__status, autospec=True)
        self.__client__update_status.start()

    def __update__status(self, *args, **kwargs):
        self.__client = args[0]
        self.__transitions.append(self.__client.status())
        update_status(self.__client, *args, **kwargs)

    def __enter__(self):
        sys.meta_path.append(self.__virtual_rpi)

        def run():
            Client.run(self.__opts, [])

        t = threading.Thread(target=run)
        t.daemon = True
        t.start()

        time.sleep(1)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__client__update_status.stop()
        self.__serial_patcher.stop()
	self.__lcd_patcher.stop()
        [sys.meta_path.remove(meta) for meta in sys.meta_path if meta is self.__virtual_rpi]

    def transitions(self):
        return self.__transitions

    def status(self):
        return self.__client.status() if self.__client is not None else None

    def scan_badge(self, badge_code):
        self.__virtual_serial.scan_badge(badge_code)

    def hold_logout(self, hold_time=None):
        pin_logout = self.__opts.get(ClientOption.PIN_LOGOUT)
        hold_time = hold_time if hold_time is not None else 0.5
        self.__virtual_rpi.write_pin(pin_logout, True)

        def reset_pin():
            time.sleep(hold_time)
            self.__virtual_rpi.write_pin(pin_logout, False)

        t = threading.Thread(target=reset_pin)
        t.daemon = True
        t.start()

    def read_pin(self, pin):
        return self.__virtual_rpi.read_pin(pin)

