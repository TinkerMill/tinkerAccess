# Current Sense Tuning

One of the features of the [custom tinkerAccess PCB](/Hardware/) is an input for a current transformer to detect the load current of the machine. The comparator circuitry on the PCB will prevent the tinkerAccess client from disabling power immediately to the machine, until the load current falls below a set threshold. The comparator threshold is set to discern between device 'running' current and device 'idle' current. On the original PCB designs, the threshold was set by changing resistor values on the PCB. On newer designs, the threshold can be set programmatically via a PWM output of the Pi.

This guide covers the procedure to tune the programmable current threshold on newer PCB designs, and explains the config parameters involved in the process.

### Config Parameters

The first two parameters apply to both versions of PCBs, the programmable threshold and the threshold set by resistor values.

- __max_power_down_timeout__:[integer seconds] (default: Infinite)

  This parameter determines the number of seconds to wait for the current to fall below the threshold during logout/shutdown. Basically, it waits until the machine reaches an idle state before disabling power. If this parameter is not set, the default is that it will wait forever for the current to fall below the threshold. However in reality, if no current transformer is connected, the detected current will be zero and likely always be below the threshold. If current detection is not desired, to guarantee that the client does not get stuck in an infinite wait state waiting for the threshold detection, this parameter should be set to 0, which essentially disables the current detection. If a current transformer is connected and current detection is desired, this value should be set to the maximum number of seconds to wait for the device to go to an idle current state during logout/shutdown.

- __logout_coast_time__:[integer seconds] (default: 0)

  This parameter determines the number of seconds to wait for the machine to coast down during a logout/shutdown. During a logout/shutdown event, the client will first wait for the current detection state to go 'idle' or it will wait the max_power_down_timeout, whichever comes first. At this point, it determines the machine is in an idle state and will wait an additional number of seconds determined by this parameter, before disabling power to the machine. This logout coast time will give an additional few seconds for things like a spinning blade to coast to a stop, before actually disabling power. The default value is 0 seconds, or no wait. If a coast time is desired, this parameter should be set to value greater than 0 seconds.

These parameters apply to the PCBs with a programmable current threshold

- __use_pgm_current_threshold__:[True|False] (default: False)

  This parameter determines whether the programmable current detect threshold PWM output is used or not. For PCBs without a programmable threshold, this parameter should be False, therefore it can be ignored since the default is False. For PCBs with a programmable threshold, but applications where current detection is not desired, this parameter should also be set to False. In this case, the programmable threshold is set to its maximum value and should always be in the 'idle' detection state. For applications that require current detection with a PCB that has a programmable threshold, this parameter should be set to True and the remaining parameters are also enabled.

- __current_detect_setting__:[integer RMS milliamps] (default: 10000)

  This parameter is used to set the programmable current detection threshold. It is defined as RMS milliamps. It should be set between the measured 'idle' current and 'running' current. There is a maximum threshold current that is determined by the CT burden resistor and CT turn ratio. The tuning script will report the maximum programmable threshold. The tuning script can also be ran at both 'idle' and 'running' conditions to determine the optimal threshold setting.

- __ct_burden_resistor__:[integer ohms] (default: 1000)

  This parameter is used in internal calculations and should match the actual value of the current transformer burden resistor on the PCB. The PCBs are built with default burden resistor values of 1K. Should the range of the programmable threshold not be adequate, the burden resistor can be increased to decrease the range, and decreased to increase the range. If the physical resistor is changed, then this parameter should be modified to reflect that change.

- __ct_turns_ratio__:[integer turns ratio] (default: 2000)

  This parameter is used in internal calculations and should match the actual turns ratio of the current transformer connected to the PCB. If the recommended SparkFun SEN-11005 current transformer is used, then the default CT ratio of 2000:1 is correct. Should the range of the programmable threshold not be adequate, the CT ratio can be increased to decrease the range, and decreased to increase the range. If the physical CT is changed, then this parameter should be modified to reflect that change.

### Tuning script

The `tune_current_sense.py` Python script can be used on a running client to sweep the programmable current detection threshold to 'measure' the actual machine current under different conditions. If this script is run at 'idle' then then under 'running' conditions, the optimal programmable threshold level will be somewhere between these two values.

Below is the procedure for running the the tuning script:

1. Edit the `/etc/tinker-access-client.conf` file to ensure the programmable current threshold is enabled and CT parameters are correct.

   The programmable current threshold detection needs to be enabled before running the tuning script. In addition the CT burden resistor and turns ratio values need to match the actual hardware. If the standard resistor and CT is being used then the default values do not need to be modified. The initial current detection setting does not matter during the tuning process.
   ```
   use_pgm_current_threshold:True
   #current_detect_setting:10000
   #ct_burden_resistor:1000
   #ct_turns_ratio:2000
   ```

   Restart the tinker-access-client and ensure it is running if changes are made to the config file.

2. Edit the `tune_current_sense.py` file to make sure the parameters match the client configuration.

   The following parameters in the script need to match the client config file and setup before running:
   ```
   pin_current_detect = 12     # GPIO pin number of the current detect input
   pin_current_threshold = 18  # GPIO pin number of the current threshold PWM output
   Rb = 1000                   # Burden resistor value on the PCB
   turns = 2000                # Turns ratio of current transformer
   Vcc = 3.3                   # GPIO voltage
   ```

3. Run the tuning script at machine idle conditions.

   With the machine at an idle condition, run the tuning script. The script will sweep all programmable threshold values. Record the current threshold value, where the detector transitions. Run the script with the following command:
   ```
   python tune_current_sense.py
   ```

   In this example, the partial output looks like this:
   ```
   Sweeping the current threshold PWM duty cycle, 50 steps in total, the current duty cycle setting is: 50
   Current sense setting: PWM Duty Cycle:  50 (100.0%), PWM Output: 3.300 Volts, Current Threshold Setting:  4.67 Amps(RMS), Detector: 0
   Current sense setting: PWM Duty Cycle:  49 ( 98.0%), PWM Output: 3.234 Volts, Current Threshold Setting:  4.57 Amps(RMS), Detector: 0
   Current sense setting: PWM Duty Cycle:  48 ( 96.0%), PWM Output: 3.168 Volts, Current Threshold Setting:  4.48 Amps(RMS), Detector: 0
   Current sense setting: PWM Duty Cycle:  47 ( 94.0%), PWM Output: 3.102 Volts, Current Threshold Setting:  4.39 Amps(RMS), Detector: 0
   ...
   Current sense setting: PWM Duty Cycle:   3 (  6.0%), PWM Output: 0.198 Volts, Current Threshold Setting:  0.28 Amps(RMS), Detector: 0
   Current sense setting: PWM Duty Cycle:   2 (  4.0%), PWM Output: 0.132 Volts, Current Threshold Setting:  0.19 Amps(RMS), Detector: 0
   Current sense setting: PWM Duty Cycle:   1 (  2.0%), PWM Output: 0.066 Volts, Current Threshold Setting:  0.09 Amps(RMS), Detector: 0
   Current sense setting: PWM Duty Cycle:   0 (  0.0%), PWM Output: 0.000 Volts, Current Threshold Setting:  0.00 Amps(RMS), Detector: 1
   Resetting PWM duty cycle to 50
   ```

   The first thing to note is that the maximum current threshold setting is 4.67 Amps. If this is not adequate for your application, then the CT burden resistor or CT turns ratio will need to be replaced in order to change the range. Second, the detector triggers at 0 Amps, therefore in this application, the 'idle' current is 0.

4. Rerun the tuning script with the machine running.

   Start the machine in its typical minimum running current condition. This could be the machine is on, but not being subjected to any load.

   In this example, the partial output looks like this:
   ```
   Sweeping the current threshold PWM duty cycle, 50 steps in total, the current duty cycle setting is: 50
   Current sense setting: PWM Duty Cycle:  50 (100.0%), PWM Output: 3.300 Volts, Current Threshold Setting:  4.67 Amps(RMS), Detector: 0
   Current sense setting: PWM Duty Cycle:  49 ( 98.0%), PWM Output: 3.234 Volts, Current Threshold Setting:  4.57 Amps(RMS), Detector: 0
   ...
   Current sense setting: PWM Duty Cycle:  35 ( 70.0%), PWM Output: 2.310 Volts, Current Threshold Setting:  3.27 Amps(RMS), Detector: 0
   Current sense setting: PWM Duty Cycle:  34 ( 68.0%), PWM Output: 2.244 Volts, Current Threshold Setting:  3.17 Amps(RMS), Detector: 0
   Current sense setting: PWM Duty Cycle:  33 ( 66.0%), PWM Output: 2.178 Volts, Current Threshold Setting:  3.08 Amps(RMS), Detector: 0
   Current sense setting: PWM Duty Cycle:  32 ( 64.0%), PWM Output: 2.112 Volts, Current Threshold Setting:  2.99 Amps(RMS), Detector: 0
   Current sense setting: PWM Duty Cycle:  31 ( 62.0%), PWM Output: 2.046 Volts, Current Threshold Setting:  2.89 Amps(RMS), Detector: 0
   Current sense setting: PWM Duty Cycle:  30 ( 60.0%), PWM Output: 1.980 Volts, Current Threshold Setting:  2.80 Amps(RMS), Detector: 1
   Current sense setting: PWM Duty Cycle:  29 ( 58.0%), PWM Output: 1.914 Volts, Current Threshold Setting:  2.71 Amps(RMS), Detector: 1
   Current sense setting: PWM Duty Cycle:  28 ( 56.0%), PWM Output: 1.848 Volts, Current Threshold Setting:  2.61 Amps(RMS), Detector: 1
   Current sense setting: PWM Duty Cycle:  27 ( 54.0%), PWM Output: 1.782 Volts, Current Threshold Setting:  2.52 Amps(RMS), Detector: 1
   Current sense setting: PWM Duty Cycle:  26 ( 52.0%), PWM Output: 1.716 Volts, Current Threshold Setting:  2.43 Amps(RMS), Detector: 1
   ...
   Current sense setting: PWM Duty Cycle:   1 (  2.0%), PWM Output: 0.066 Volts, Current Threshold Setting:  0.09 Amps(RMS), Detector: 1
   Current sense setting: PWM Duty Cycle:   0 (  0.0%), PWM Output: 0.000 Volts, Current Threshold Setting:  0.00 Amps(RMS), Detector: 1
   Resetting PWM duty cycle to 50
   ```

   In this example, the detector triggers at 2.80 Amps, therefore in this example, the 'running' current is 2.80 Amps.

5. Set the programmable threshold in the config file and restart the client.

   In the example above, the idle current is 0 and the running current is 2.80 Amps. A good threshold value would be half way between at 1.40 Amps. Since the config file value is in milliamps, the value should be 1400. The config file parameters would need to be modified to look like the following. Notice the CT parameters can be left commented out since we are using the default values:
   ```
   use_pgm_current_threshold:True
   current_detect_setting:1400
   #ct_burden_resistor:1000
   #ct_turns_ratio:2000
   ```

   After saving the config file, restart the tinker-access-client for the new parameter to take effect.
