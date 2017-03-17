import time
import logging


# The wiring for the LCD is as follows:
# 1 : GND
# 2 : 5V
# 3 : Contrast (0-5V)*      Tie to Gnd for max contrast
# 4 : RS (Register Select)
# 5 : R/W (Read Write)       - GROUND THIS PIN
# 6 : Enable or Strobe
# 7 : Data Bit 0             - NOT USED
# 8 : Data Bit 1             - NOT USED
# 9 : Data Bit 2             - NOT USED
# 10: Data Bit 3             - NOT USED
# 11: Data Bit 4
# 12: Data Bit 5
# 13: Data Bit 6
# 14: Data Bit 7
# 15: LCD Backlight +5V**
# 16: LCD Backlight GND

# Define GPIO to LCD mapping
LCD_RS = 7  # 4 : RS (Register Select)  [RPi pin 7 is connected to PiWedge 'CE1' ]
LCD_E = 8  # 6 : Enable or Strobe      [RPi pin 8 is connected to PiWedge 'CE0' ]
LCD_D4 = 25  # 11: Data Bit 4
LCD_D5 = 24  # 12: Data Bit 5
LCD_D6 = 23  # 13: Data Bit 6
LCD_D7 = 18  # 14: Data Bit 7

# Define some device constants
LCD_WIDTH = 16  # Maximum characters per line
LCD_CHR = True
LCD_CMD = False

LCD_LINE_1 = 0x80  # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0  # LCD RAM address for the 2nd line

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005


class LcdApi(object):

    def __init__(self, gpio):
        self.__logger = logging.getLogger(__name__)

        # noinspection PyPep8Naming
        GPIO = self.__GPIO = gpio
        GPIO.setup(LCD_E, GPIO.OUT)  # E
        GPIO.setup(LCD_RS, GPIO.OUT)  # RS
        GPIO.setup(LCD_D4, GPIO.OUT)  # DB4
        GPIO.setup(LCD_D5, GPIO.OUT)  # DB5
        GPIO.setup(LCD_D6, GPIO.OUT)  # DB6
        GPIO.setup(LCD_D7, GPIO.OUT)  # DB7

        self.__init__display()

    def __init__display(self):
        # # Initialise display
        self.lcd_byte(0x33, LCD_CMD)  # 110011 Initialise
        self.lcd_byte(0x32, LCD_CMD)  # 110010 Initialise
        self.lcd_byte(0x06, LCD_CMD)  # 000110 Cursor move direction
        self.lcd_byte(0x0C, LCD_CMD)  # 001100 Display On,Cursor Off, Blink Off
        self.lcd_byte(0x28, LCD_CMD)  # 101000 Data length, number of lines, font size
        self.lcd_byte(0x01, LCD_CMD)  # 000001 Clear display
        time.sleep(E_DELAY)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def lcd_byte(self, bits, mode):

        # Send byte to data pins
        # bits = data
        # mode = True  for character
        #        False for command

        # noinspection PyPep8Naming
        GPIO = self.__GPIO
        GPIO.output(LCD_RS, mode)  # RS --Select Register


        # High bits
        GPIO.output(LCD_D4, False)
        GPIO.output(LCD_D5, False)
        GPIO.output(LCD_D6, False)
        GPIO.output(LCD_D7, False)
        if bits & 0x10 == 0x10:
            GPIO.output(LCD_D4, True)
        if bits & 0x20 == 0x20:
            GPIO.output(LCD_D5, True)
        if bits & 0x40 == 0x40:
            GPIO.output(LCD_D6, True)
        if bits & 0x80 == 0x80:
            GPIO.output(LCD_D7, True)

        self.lcd_toggle_enable()

        # Low bits
        GPIO.output(LCD_D4, False)
        GPIO.output(LCD_D5, False)
        GPIO.output(LCD_D6, False)
        GPIO.output(LCD_D7, False)
        if bits & 0x01 == 0x01:
            GPIO.output(LCD_D4, True)
        if bits & 0x02 == 0x02:
            GPIO.output(LCD_D5, True)
        if bits & 0x04 == 0x04:
            GPIO.output(LCD_D6, True)
        if bits & 0x08 == 0x08:
            GPIO.output(LCD_D7, True)

        self.lcd_toggle_enable()

    def lcd_toggle_enable(self):

        # noinspection PyPep8Naming
        GPIO = self.__GPIO
        time.sleep(E_DELAY)
        GPIO.output(LCD_E, True)
        time.sleep(E_PULSE)
        GPIO.output(LCD_E, False)
        time.sleep(E_DELAY)

    def lcd_string(self, message, line):

        # Send string to display
        self.lcd_byte(line, LCD_CMD)

        if (len(message) > LCD_WIDTH) and 0:
            for i in range(len(message) - LCD_WIDTH + 1):
                time.sleep(3)
                self.lcd_byte(line, LCD_CMD)
                for c in message[i:(len(message))]:
                    self.lcd_byte(ord(c), LCD_CHR)

        else:
            messageLJ = message.ljust(LCD_WIDTH, ' ')
            for i in range(LCD_WIDTH):
                self.lcd_byte(ord(messageLJ[i]), LCD_CHR)

    def write(self, first_line, second_line):
        self.lcd_string(first_line, LCD_LINE_1)
        self.lcd_string(second_line, LCD_LINE_2)
