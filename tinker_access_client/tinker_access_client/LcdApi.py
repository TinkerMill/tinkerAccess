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


# The wiring for the LCD with backpack is as follows:
#   LCD | Pin on Raspberry Pi
#   ====|====================
#   GND | 6 (GND)
#   VCC | 4 (5V)
#   SDA | 3 (GPIO2, SDA1 I2C)
#   SCL | 5 (GPIO3, SCL1 I2C)


import time
import logging
import I2CApi
from ClientOptionParser import ClientOption

# LCD Address
LCD_BACKPACK_ADDRESS = 0x27
LCD_SERLCD_ADDRESS = 0x72

# LCD display init sleep delay
LCD_INITDELAY = 0.2

# SerLCD command characters
SERLCD_SPECIAL_CMD = 254
SERLCD_SETTING_CMD = 0x7C

# SerLCD special commands
SERLCD_RETURNHOME = 0x02
SERLCD_ENTRYMODESET = 0x04
SERLCD_DISPLAYCONTROL = 0x08
SERLCD_CURSORSHIFT = 0x10
SERLCD_SETDDRAMADDR = 0x80

# SerLCD setting commands (partial list)
SERLCD_CONTRAST = 0x18
SERLCD_RGB_BACKLIGHT = 0x2B
SERLCD_CLEARDISPLAY = 0x2D

# LCD commands for backpack only
LCD_CLEARDISPLAY = 0x01
LCD_RETURNHOME = 0x02
LCD_ENTRYMODESET = 0x04
LCD_DISPLAYCONTROL = 0x08
LCD_CURSORSHIFT = 0x10
LCD_FUNCTIONSET = 0x20
LCD_SETCGRAMADDR = 0x40
LCD_SETDDRAMADDR = 0x80

# flags for LCD display entry mode, common to backpack and SerLCD
LCD_ENTRYRIGHT = 0x00
LCD_ENTRYLEFT = 0x02
LCD_ENTRYSHIFTINCREMENT = 0x01
LCD_ENTRYSHIFTDECREMENT = 0x00

# flags for LCD display on/off control, common to backpack and SerLCD
LCD_DISPLAYON = 0x04
LCD_DISPLAYOFF = 0x00
LCD_CURSORON = 0x02
LCD_CURSOROFF = 0x00
LCD_BLINKON = 0x01
LCD_BLINKOFF = 0x00

# flags for LCD display/cursor shift, common to backpack and SerLCD
LCD_DISPLAYMOVE = 0x08
LCD_CURSORMOVE = 0x00
LCD_MOVERIGHT = 0x04
LCD_MOVELEFT = 0x00

# flags for LCD function set, backpack only
LCD_8BITMODE = 0x10
LCD_4BITMODE = 0x00
LCD_2LINE = 0x08
LCD_1LINE = 0x00
LCD_5x10DOTS = 0x04
LCD_5x8DOTS = 0x00

# flags for LCD backlight control, backpack only
LCD_BACKLIGHT = 0x08
LCD_NOBACKLIGHT = 0x00

En = 0b00000100 # LCD Enable bit
Rw = 0b00000010 # LCD Read/Write bit
Rs = 0b00000001 # LCD Register select bit

class LcdApi(object):

    # Initialize objects and LCD
    def __init__(self, opts, init=True):
        self.__logger = logging.getLogger(__name__)
        self.__opts = opts
        self.__init = init
        self.__serlcd = self.__opts.get(ClientOption.DISPLAY_SERLCD)

        if self.__serlcd:
            # SerLCD address
            self.lcd_device = I2CApi.i2c_device(LCD_SERLCD_ADDRESS)
        else:
            # Backpack address
            self.lcd_device = I2CApi.i2c_device(LCD_BACKPACK_ADDRESS)

        if not self.__serlcd:
            # Only for backpack
            self.lcd_write(0x03)
            self.lcd_write(0x03)
            self.lcd_write(0x03)
            self.lcd_write(0x02)

        if (self.__init):
            self.__init__display()

    # Fulfill context management requirements
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    # Initialize display
    def __init__display(self):

        if self.__serlcd:
            # SerLCD
            self.serlcd_write(SERLCD_SPECIAL_CMD, [LCD_DISPLAYCONTROL | LCD_DISPLAYON | LCD_CURSOROFF | LCD_BLINKOFF])
            self.serlcd_write(SERLCD_SPECIAL_CMD, [LCD_ENTRYMODESET | LCD_ENTRYLEFT | LCD_ENTRYSHIFTDECREMENT])
            self.serlcd_write(SERLCD_SETTING_CMD, [SERLCD_CLEARDISPLAY])
            #self.serlcd_write(SERLCD_SETTING_CMD, [SERLCD_RGB_BACKLIGHT, 0, 0, 0])

        else:
            # Backpack
            self.lcd_write(LCD_FUNCTIONSET | LCD_2LINE | LCD_5x8DOTS | LCD_4BITMODE)
            self.lcd_write(LCD_DISPLAYCONTROL | LCD_DISPLAYON)
            self.lcd_write(LCD_CLEARDISPLAY)
            self.lcd_write(LCD_ENTRYMODESET | LCD_ENTRYLEFT)
            
        time.sleep(LCD_INITDELAY)
        
    # Write a command to SerLCD
    def serlcd_write(self, cmd, data):
        self.lcd_device.write_block_data(cmd, data)
        
    # Write a command to backpack LCD
    def lcd_write(self, cmd, mode=0):
        self.lcd_write_four_bits(mode | (cmd & 0xF0))
        self.lcd_write_four_bits(mode | ((cmd << 4) & 0xF0))

    # Write four bits to the backpack LCD
    def lcd_write_four_bits(self, data):
        self.lcd_device.write_cmd(data | LCD_BACKLIGHT)
        self.lcd_strobe(data)

    # clocks EN to latch command for backpack
    def lcd_strobe(self, data):
        self.lcd_device.write_cmd(data | En | LCD_BACKLIGHT)
        time.sleep(.0005)
        self.lcd_device.write_cmd(((data & ~En) | LCD_BACKLIGHT))
        time.sleep(.0001)

    # write a character to lcd (or character rom)
    # 0x09: backlight | RS=DR< works!
    def lcd_write_char(self, charvalue, mode=1):
        self.lcd_write_four_bits(mode | (charvalue & 0xF0))
        self.lcd_write_four_bits(mode | ((charvalue << 4) & 0xF0))

    # put string function with optional char positioning
    def lcd_display_string(self, string, line=1, pos=0):
        if line == 1:
            pos_new = pos
        elif line == 2:
            pos_new = 0x40 + pos
        elif line == 3:
            pos_new = 0x14 + pos
        elif line == 4:
            pos_new = 0x54 + pos

        if self.__serlcd:
            # SerLCD
            self.serlcd_write(SERLCD_SPECIAL_CMD, [SERLCD_SETDDRAMADDR + pos_new] + [ord(char) for char in string])
            
        else:
            # Backpack
            self.lcd_write(0x80 + pos_new)

            for char in string:
                self.lcd_write(ord(char), Rs)

    # clear lcd and set to home
    def lcd_clear(self):
        self.lcd_write(LCD_CLEARDISPLAY)
        self.lcd_write(LCD_RETURNHOME)

    # define backlight on/off (lcd.backlight(1); off= lcd.backlight(0)
    def backlight(self, state): # for state, 1 = on, 0 = off
        if state == 1:
            self.lcd_device.write_cmd(LCD_BACKLIGHT)
        elif state == 0:
            self.lcd_device.write_cmd(LCD_NOBACKLIGHT)

    # add custom characters (0 - 7)
    def lcd_load_custom_chars(self, fontdata):
        self.lcd_write(0x40);
        for char in fontdata:
            for line in char:
                self.lcd_write_char(line)

    # Write two lines to the LCD, called from outside
    def write(self, first_line, second_line):
	self.lcd_display_string(first_line, 1, 0)
	self.lcd_display_string(second_line, 2, 0)

    # Set the RGB backlight (SerLCD only)
    def rgb_backlight(self, red, green, blue):
        if self.__serlcd:
            self.serlcd_write(SERLCD_SETTING_CMD, [SERLCD_RGB_BACKLIGHT, (0,255)[red], (0,255)[green], (0,255)[blue]])

