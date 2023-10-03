<!--
SPDX-FileCopyrightText: 2023 Charles Crighton <code@crighton.net.nz>

SPDX-License-Identifier: CC-BY-4.0
-->

# Rockwren Install

- [Install with Thonny](#thonny)
- [Install with pipkin](#pipkin)
- [Install ESP8266 Firmware with Rockwren](#esp8266-firmware)

## Installing from PyPI

- [Thonny](#thonny)
- [Pipkin](#pipkin)

After installing the rockwren package read the [README](../README.md) for instructions
on installing a simple application.

### Thonny

See the [Pico guide](https://projects.raspberrypi.org/en/projects/introduction-to-the-pico)
for details on setting up Thonny and adding the Micropython firmware to your [Pico W](https://www.raspberrypi.com/documentation/microcontrollers/raspberry-pi-pico.html) or other similar device supporting micropython.

Once you have Thonny installed, the rockwren package can be installed.

1. Select ```Tools``` then ```Manage packages...```.
2. Enter ```micropython-rockwren```, click ```Search on PyPI```.
3. Click on ```micropython-rockwren``` in the search results.
4. Click on ```Install```.
5. Once the installation has completed, close the package window.

Rockwren is now installed on the Pico W.  Now install an application.

### Pipkin

[Pipkin](https://pypi.org/project/pipkin/) is used for command line installs from PyPI.

Install pipkin.
```commandline
pip install pipkin
```
Install ```micropython-rockwren``` and dependencies.
```commandline
pipkin install micropython-rockwren
```

### ESP8266 Firmware

Rockwren provides custome micropython firmware for ESP8266 that includes Rockwren as a frozen module.

Download the firmware for the Rockwren release from the [Github releases](https://github.com/ccrighton/rockwren/releases) page.

Before flashing the firmware install ```esptool``` and ```mpremote``` in a python virtual environment.

```commandline
pip install esptool
pip install mpremote
```

Flash the firmware.  Replace the file name ```firmware.bin``` with the filename of the download micropython firmware.

```commandline
python -m esptool --port ${PORT} --chip esp8266 --baud 460800 write_flash --flash_size detect 0 firmware.bin
```

Once the firmware is installed, use Thonny or ```mpremote``` to install the rockwren html and an application.

For example, with ```mpremote```.  Unpack the rockwren source distribution:

```commandline
tar xvf micropython-rockwren-1.0.0.tar.gz
```

Install the html, css and svg files on the device:

```commandline
mpremote cp micropython-rockwren-1.0.0/rockwren/*.html :lib/rockwren/
mpremote cp micropython-rockwren-1.0.0/rockwren/*.css :lib/rockwren/
mpremote cp micropython-rockwren-1.0.0/rockwren/*.svg :lib/rockwren/
```

Install the application:

```commandline
mpremote cp main.py :
mpremote cp controls.html :
```
