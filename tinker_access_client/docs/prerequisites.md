# Prerequisites:
1. Build the custom [Raspberry Pi HAT](https://www.raspberrypi.org/blog/introducing-raspberry-pi-hats/) as described [here](../../docs/tinkerAccess.fzz).

1. Create a [Raspbian OS](https://www.raspberrypi.org/downloads/raspbian/) boot image as described [here](docs/bootimage.md).

1. Transfer your SD card to the Raspberry Pi and boot it up.

1. Create a remote secure shell to your Raspberry Pi. If you followed the previous setup instructions, your PI is already configured to allow SSH connections.  
[These](https://www.raspberrypi.org/documentation/remote-access/ssh/README.md) instructions may assist you in identifying the correct IP address and creating the connection.

1. Complete [these](https://www.howtogeek.com/167195/how-to-change-your-raspberry-pi-or-other-linux-devices-hostname/) steps to change the hostname of your Raspberry Pi, and [these](https://www.raspberrypi.org/documentation/linux/usage/users.md) to update your the default password.

1. If you have not already done so already, __reboot__ the Raspberry Pi so that the changes take affect & __reconnect__ to the Raspberry Pi using your new hostname.

1. Install the python package mamanager (a.k.a 'pip')

  **IMPORTANT**: If you have just created a new image using the previous mentioned guide, or you are using an existing image...

  Ensure you have the latest version of [pip](https://pip.pypa.io/en/stable) and its related setuptools installed, if you don't complete this step, you will almost certainly __not__ have a good time. Version issues with PIP and its related setuptools can be inconsistent, confusing and difficult to resolve, it is better to just avoid it now and ensure that they are updated.

  You can find references to many of these issues described [here](https://pip.pypa.io/en/stable/installing/#upgrading-pip)...

  This is what has worked for me consistently:
  ```commandline
  sudo apt-get update
  sudo apt-get install python-pip
  sudo easy_install pip
  sudo pip install --upgrade  setuptools pip
  ```

1. [Continue](../README.md)
