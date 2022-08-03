# tinker-access-client

The tinker-access-client is the client piece of the tinkerAccess system, a [Raspberry Pi](https://www.raspberrypi.org/products/) based access control system that can be used to prevent unauthorized users from using devices that require special training. It could also conceivably be used to control electronic lock boxes or doors.

The system was originally designed and created by [Matt Stallard](https://github.com/mstallard), [Ron Thomas](https://github.com/RonaldThomas), and [Matt Peopping](https://github.com/analogpixel) for [TinkerMill](http://www.tinkermill.org) a makerspace in [Longmont, CO](https://www.google.com/maps/place/Longmont,+CO/@40.1679379,-105.1678944,12z/data=!3m1!4b1!4m5!3m4!1s0x876bf908d5cc3349:0xc17da1eef3a32735!8m2!3d40.1672068!4d-105.1019275). It is continually being maintained and enhanced by other contributors in the community.

The client software is a [Python 2.7](https://www.python.org/download/releases/2.7/) service designed to run on the [Raspberry Pi OS](https://www.raspberrypi.org/downloads/raspberry-pi-os/). The service is responsible for coordinating activity between the RPi's peripherals (i.e., RFID reader, LCD, etc.) and the GPIO, as well as communicating with the [tinker-access-server](/tinker_access_server/README.md) for activity logging, authentication, and authorization.

Official releases of the client software are packaged and published to [PyPI - the Python Package Index ](https://pypi.python.org/pypi/tinker-access-client/)  

## Prerequisites
You will need to complete these [prerequisites](docs/prerequisites.md) before installing the tinker-access-client.

## Installing the tinker-access-client:

By default, the tinker-access-client is installed as a service that starts immediately, as well as upon reboot of the device.

Use the following command to get the latest version of the client:
```
sudo pip install --upgrade --force-reinstall --ignore-installed --no-cache-dir tinker-access-client --no-binary tinker-access-client
```

Query the client status:
```
sudo tinker-access-client status
```

If the client successfully starts, then the expected status should be *'idle'*. However, the client service will likely not start up at first, and the returned status will be *'terminated'*. The reason for this is that the default client configuration settings will likely not work without some changes. Therefore a client configuration file needs to be added and modified. Get an example client config file directly from the GitHub repo, and then modify it:
```
sudo wget https://raw.githubusercontent.com/TinkerMill/tinkerAccess/master/tinker_access_client/config_file/tinker-access-client.conf -P /etc --backups=1
sudo nano /etc/tinker-access-client.conf
```

The example configuration file has the most commonly used options, many of which are commented out. The *Options* section below lists all of the possible options that can be set in the config file. The command line configuration options all start with --, but the equivalent config file name to be used in the config file is shown in square brackets [ ]. Modify the config file to match your tinker-access-client node wiring and setup, then save the file.

Start the client service again and recheck the status:
```
sudo tinker-access-client start
sudo tinker-access-client status
```

If the client status still does not come back as *'idle'*, then check the log file to get an idea as to why the client service is not starting:
```
less /var/log/tinker-access-client.log
```

See the [development guide](docs/development.md) for special installation instructions, best practices and other helpful information for maintaining and enhancing the code for the future.

## Upgrading the tinker-access-client:

To upgrade to the latest version of the client, here are the commands that have worked for me:
```
sudo tinker-access-client stop
sudo pip install --upgrade --force-reinstall --ignore-installed --no-cache-dir tinker-access-client --no-binary tinker-access-client
sudo tinker-access-client --version
sudo tinker-access-client status
```

## Downgrading the tinker-access-client:

To downgrade to a previous version of the client, here are the commands that have worked for me. Replace the version number in the 'pip install' line with the actual desired version number:
```
sudo tinker-access-client stop
sudo tinker-access-client remove
sudo pip install --upgrade --force-reinstall --ignore-installed --no-cache-dir tinker-access-client==2020.6.28.24 --no-binary tinker-access-client
sudo tinker-access-client --version
sudo tinker-access-client status
```

## Using the tinker-access-client command-line tools:
The remaining information in this guide explains some ways to customize the behavior of the client, control the client, and/or get feedback about the state of the client.

All of the following commands and options are available by using the  --help option on the command line.
```
sudo tinker-access-client --help
```

#### Usage:
```
sudo tinker-access-client <command> [options]
```

#### Commands:
- __start__ : This command will start the tinker-access-client process.

- __stop__ : This command will stop the tinker-access-client process.

- __status__ : This command will return the current state of the tinker-access-client (i.e. initialized, idle, in_use, in_training, terminated).

- __update__ : This command will update the tinker-access-client from the [PyPI - the Python Package Index ](https://pypi.python.org/pypi/tinker-access-client/).  

  By default, the latest published version will be installed. Optionally, a second argument can be provided to specify the specific version desired.
  ```
  sudo tinker-access-client update 2017.2.14.441
  ```

- __remove__ : This command will stop the tinker-access-client process, remove the service and all other artifacts installed via PIP.  

- __restart__ : This command will stop and restart the tinker-access-client process, this can be useful to reload after code changes.

#### Options:

The default value of most of these options can be overridden in a config file. Specifying options via the command line can be useful for debugging purposes.

For example creating this file would enable the auto_update feature, and set the logging level to debug:  

File: `/etc/tinker-access-client.conf`
```
[config]
log_level: 10
auto_update: true
```

- __--version__: Show the current version number and exit

- __-h, --help__: Show the help message and exit

- __--config-file=[config_file]__: The location of the config file to use [default:'/etc/tinker-access-client.conf'] a non-default command-line option value will have precedence over a config-file option value

- __--logging-config-file=[logging_config_file]__: The location of a logging config file to use [default:'/etc/tinker-access-client.logging.conf'] If this file is present, it will override the default logging configuration including the --log-level and --log-file options

- __--debug__: Run in the foreground (a.k.a debug mode) [default:'False']

- __--force-update__: By default, the update command will not do an update if the current version matches the latest version published to [PyPI - the Python Package Index ](https://pypi.python.org/pypi/tinker-access-client/). This option bypasses the version check, and will force a re-install [default:'False']

- __--auto-update=[auto_update]__: If configured, the client will periodically check if a newer version has been published to [PyPI - the Python Package Index ](https://pypi.python.org/pypi/tinker-access-client/). If a new version is found, it will be install it automatically.
[default:'False']

- __--auto-update-interval=[auto_update_interval]__: The period (specified in minutes) that the [PyPI - the Python Package Index ](https://pypi.python.org/pypi/tinker-access-client/) should be checked for a new version of the client. [default:5]

- __--log-file=[log_file]__: The path and name of the log file [default:'/var/log/tinker-access-client.log']

- __--status-file=[status_file]__: The path and name of the status file, the contents of this file will always reflect the current state of the client. (i.e. initialized, idle, in_use, in_training, terminated) A missing file indicates the client is not running [default:'/var/log/tinker-access-client.status']

- __--pid-file=[pid_file]__: The path and name of the client daemon's pid file [default:'/var/run/tinker-access-client.pid']

- __--log-level=[log_level]__: The log level to use [default:40]

- __--server-address=[server_address]__: The [tinker-access-server's](../tinker_access_server/README.md) api address
[default:'http://localhost:5000']

- __--device-id=[device_id]__: The unique identifier for this client, as configured in the [tinker-access-server](../tinker_access_server/README.md) [default:'none']

- __--logout-coast-time=[logout_coast_time]__: A fixed number of seconds to wait for the physical machine to stop before disabling power, after the current sense pin goes low. (i.e., a blade to stop spinning etc...) [default:0]

- __--max-power-down-timeout=[max_power_down_timeout]__: The maximum number of seconds to wait for the current sense pin to go low during logout/shutdown [default:None(infinite)]

- __--reboot-on-error=[reboot_on_error]__: Any unhandled errors will cause the device to reboot after the specified --reboot-delay. [default:'False']

  This behavior is only supported on Raspberry Pi devices.

- __--reboot-delay=[reboot_delay]__: The number of seconds to wait before attempting to reboot the device after an unhandled error. [default:5]

- __--pin-logout=[pin_logout]__: The logout button pin [default:16]

- __--pin-power-relay=[pin_power_relay]__: The power relay pin [default:17]

- __--pin-led-red=[pin_led_red]__: The red led pin [default:21]

- __--pin-led-green=[pin_led_green]__: The green led pin [default:19]

- __--pin-led-blue=[pin_led_blue]__: The blue led pin [default:20]

- __--pin-current-sense=[pin_current_sense]__: The current sense pin [default:12]

- __--pin-current-threshold=[pin_current_threshold]__: The current sense detect threshold PWM pin [default:18]

- __--pin-estop=[pin_estop]__: The E-STOP input pin [default:6]

- __--pin-bypass-detect=[pin_bypass_detect]__: The bypass detect input pin [default:13]

- __--pin-3v3-en=[pin_3v3_en]__: The 3.3V enable pin [default:27]

- __--pin-alarm=[pin_alarm]__: The alarm output pin [default:22]

- __--use-estop=[use_estop]__: The E-STOP input pin will be used to detect E-STOP events and automatically logout the user [default:'False']

- __--estop-active-hi=[estop_active_hi]__: The E-STOP input pin is detected as active high if true, otherwise the input is active low [default:'False']

- __--use-bypass-detect=[use_bypass_detect]__: The bypass detect input pin will be monitored to log a tamper or bypass event [default:'False']

- __--use-3v3-en=[use_3v3_en]__: The PCB has a 3.3V enable output pin and will be cycled during start-up or certain errors. This feature should be set for PCB rev 1.4 or higher [default:'False']

- __--use-alarm=[use_alarm]__: The alarm output pin is enabled and will output high during an alarm condition [default:'False']

- __--use-pgm-current-threshold=[use_pgm_current_threshold]__: The PCB has a programmable current detect threshold PWM output and will be set during init to set the current detect threshold. This feature is available on PCB rev 1.4 or higher. If current detection is desired on rev 1.4 PCBs, this feature must be set True. If it is not desired, it can be left set to False [default:'False']

- __--current-detect-setting=[current_detect_setting]__: The current sense detect threshold setting in RMS milliamps [default:'10000']

- __--ct-burden-resistor=[ct_burden_resistor]__: The current transformer burden resistor value in ohms [default:'1000']

- __--ct-turns-ratio=[ct_turns_ratio]__: The current transformer turns ratio [default:'2000']

- __--is-a-door=[is_a_door]__: The device is a door. If defined, it changes the default behavior of the device and enables the remaining door parameters below [default:'False']

- __--door-unlock-time=[door_unlock_time]__: The amount of time the door unlocks in seconds. Only used if the is-a-door parameter is also enabled [default:'10']

- __--door-continuous-unlock=[door_continuous_unlock]__: The door is defined as being able to be held in a continuously unlocked state. Only used if is-a-door parameter is also enabled. This parameter should only be used on door locks that can be left permanently energized. It should not be enabled on non-continuous duty solenoid style locks. The logout button will be used to toggle between the locked and unlocked state. Therefore, the training mode will be disabled if this parameter is set [default:'False']

- __--door-normal-hr-start=[door_normal_hr_start]__: The start of normal hours, when a door can be held in a continuously unlocked state. Only used if is-a-door and door-continuous-unlock parameters are also enabled. The time is defined in 24hr format. The door cannot be held in an unlocked state before this time [default:'730']

- __--door-normal-hr-end=[door_normal_hr_end]__: The end of normal hours, when a door can be held in a continuously unlocked state. Only used if is-a-door and door-continuous-unlock parameters are also enabled. The time is defined in 24hr format. The door will lock if currently unlocked at this time and cannot be held in an unlocked state after this time [default:'2200']

- __--disable-training-mode=[disable_training_mode]__: Disables entering training mode at the device if the logout button is held down for 3 seconds [default:'False']

- __--serial-port-name=[serial_port_name]__: The serial port attached to the RFID reader [default:'/dev/ttyUSB0']

- __--serial-port-speed=[serial_port_speed]__: The serial port speed to use [default:9600]

- __--display-serlcd=[display_serlcd]__: Send commands for the SparkFun LCD-14072 SerLCD display if true, otherwise send commands for the original backpack style display [default:'False']

- __--allow-user-override=[allow_user_override]__: Allows a new user to login and takeover the current user login session [default:'False']

## Tuning the current detection threshold:

Newer PCBs (rev 1.4) have a programmable current detection threshold. Details on how to tune this can be found [here](tuning/README.md).

