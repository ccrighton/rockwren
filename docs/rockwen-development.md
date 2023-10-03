<!--
SPDX-FileCopyrightText: 2023 Charles Crighton <code@crighton.net.nz>

SPDX-License-Identifier: CC-BY-4.0
-->

# Rockwren Development

This page is for developers who are modifying the Rockwren module or building versions of micropython
firmware with Rockwren included as a frozen module.

- [Create Distribution](#create-the-rockwren-source-distribution-sdist)
- [Publish to PyPI](#publish-the-distribution)
- [Build ESP8266 Firmware](#build-esp8266-firmware)
- [Makefile targets](#makefile)

## Create the Rockwren Source Distribution (sdist)

After merging changes for a new distribution, check the [version file](../rockwren/version.py) to ensure that
the correct version has been applied.  Rockwren complies with the [Semantic Versioning 2.0.0](https://semver.org/).

Update [changelog.md](../changelog.md)

```commandline
make dist
```

This will create the sdist and wheel in the ```dist``` directory.

## Publish the Distribution

Test publication to testpypi is performed using the following make target:
```commandline
make publish-testpypi
```
Publication to the live pypi is performed using:
```commandline
make publish-pypi
```

## Build ESP8266 Firmware

The ESP8266 has limited resources.  To preserve limited memory it is necessary to freeze the Rockwren module
in the micropython firmware for it to operate successfully.  The following make targets are used to build and
deploy the firmware.

```commandline
make build-esp8266
```

```commandline
make flash-esp8266
```

## Makefile

The [Makefile](../Makefile) provides a set of useful targets for building, testing and deploying Rockwren.

```text
Rockwren build and flash targets

help: Display this help
dist: Package rockwren python distribution
test: Run test cases
license-check: Check reuse license compliance
build-esp8266: Build ESP8266 Firmware
flash-esp8266: Flash ESP8266 Rockwren firmware to device. PORT variable can be configured e.g. PORT=/dev/ttyUSB1
install-pico: Install rockwren and dependencies on Raspberry Pi Pico W
install-example: Flash example app to device.  APP variable must be set to name of app e.g. APP=pico_switch
device-reset: Reset the device (needed after an installation to run the app or via console and Ctrl-D)
clean: Clean
git-setup: Set up git (pre-commit hooks)
reuse-annotate-gpl3: Annotate files with copyright and license details. FILE variable must be set e.g. FILE=rockwren/rockwren.py
reuse-annotate-cc-by-4: Annotate files with copyright and license details. FILE variable must be set e.g. FILE=docs/main-screen.png
publish-testpypi: Publish distribution file to TestPyPI
publish-pypi: Publish distribution file to PyPI

```
