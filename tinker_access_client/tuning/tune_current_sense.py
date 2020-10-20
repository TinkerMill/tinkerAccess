# Use pigpio to manipulate and read the GPIO while the client is running
import pigpio
import math
import time

# Modify these parameters to the correct values before running this script

pin_current_detect = 12     # GPIO pin number of the current detect input
pin_current_threshold = 18  # GPIO pin number of the current threshold PWM output
Rb = 1000                   # Burden resistor value on the PCB
turns = 2000                # Turns ratio of current transformer
Vcc = 3.3                   # GPIO voltage

PIGPIO = pigpio.pi()

pwm_range = PIGPIO.get_PWM_range(pin_current_threshold)
pwm_current_dutycycle = PIGPIO.get_PWM_dutycycle(pin_current_threshold)

max_threshold_in_amps_rms = 1.0 * Vcc / math.sqrt(2) / Rb * turns
amps_resolution = 1.0 * max_threshold_in_amps_rms / pwm_range

print('Sweeping the current threshold PWM duty cycle, %d steps in total, the current duty cycle setting is: %d' % (pwm_range, pwm_current_dutycycle))

for pwm_dutycycle in range(pwm_range, -1, -1):

    PIGPIO.set_PWM_dutycycle(pin_current_threshold, pwm_dutycycle)

    time.sleep(0.5)

    pwm_dutycycle_pct = 100.0 * pwm_dutycycle / pwm_range
    pwm_amps = 1.0 * pwm_dutycycle * amps_resolution
    pwm_volts = 1.0 * Vcc * pwm_dutycycle / pwm_range

    current_detect = PIGPIO.read(pin_current_detect)

    print('Current sense setting: PWM Duty Cycle: %3d (%5.1f%%), PWM Output: %5.3f Volts, Current Threshold Setting: %5.2f Amps(RMS), Detector: %d' %
          (pwm_dutycycle, pwm_dutycycle_pct, pwm_volts, pwm_amps, current_detect))

# Restore the duty cycle setting
print('Resetting PWM duty cycle to %d' % (pwm_current_dutycycle))
PIGPIO.set_PWM_dutycycle(pin_current_threshold, pwm_current_dutycycle)
