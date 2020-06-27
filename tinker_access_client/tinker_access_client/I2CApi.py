# -*- coding: utf-8 -*-
# Original code found at:
# https://gist.github.com/DenisFromHR/cc863375a6e19dce359d

"""
Compiled, mashed and generally mutilated 2014-2015 by Denis Pleic
Made available under GNU GENERAL PUBLIC LICENSE

# Modified Python I2C library for Raspberry Pi
# as found on http://www.recantha.co.uk/blog/?p=4849
# Joined existing 'i2c_lib.py' and 'lcddriver.py' into a single library
# added bits and pieces from various sources
# By DenisFromHR (Denis Pleic)
# 2015-02-10, ver 0.1

"""

# Cobbled together from former TinkerAccess LcdApi.py and
# http://www.circuitbasics.com/raspberry-pi-i2c-lcd-set-up-and-programming/
# by kso512 (Chris Lindbergh) with lots of teaching from Erick McQueen
# 2017-05

import time
import smbus2 as smbus

# i2c bus (0 -- original Pi, 1 -- Rev 2 Pi)
I2CBUS = 1

class i2c_device:

    # Initialize I2C bus
    def __init__(self, addr, port=I2CBUS):
        self.addr = addr
        self.bus = smbus.SMBus(port)

    # Fix for 'too many files open' error
    def __del__(self):
        self.bus.close()

    # Fulfill context management requirements
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.bus.close()

    # Write a single command to the i2c bus
    def write_cmd(self, cmd):
        self.bus.write_byte_data(self.addr, cmd, 0)
        time.sleep(0.0001)

    # Write a command and argument to the i2c bus
    def write_cmd_arg(self, cmd, data):
        self.bus.write_byte_data(self.addr, cmd, data)
        time.sleep(0.0001)

    # Write a block of data to the i2c bus
    def write_block_data(self, cmd, data):
        self.bus.write_i2c_block_data(self.addr, cmd, data)
        time.sleep(0.0001)

    # Read a single byte from the i2c bus
    def read(self):
        return self.bus.read_byte(self.addr)

    # Read from the i2c bus
    def read_data(self, cmd):
        return self.bus.read_byte_data(self.addr, cmd)

    # Read a block of data from the i2c bus
    def read_block_data(self, cmd):
        return self.bus.read_block_data(self.addr, cmd)

