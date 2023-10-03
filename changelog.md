<!--
SPDX-FileCopyrightText: 2023 Charles Crighton <code@crighton.net.nz>

SPDX-License-Identifier: GPL-3.0-or-later
-->

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<!--
## [x.y.z] - yyyy-mm-dd
### Added
### Changed
### Removed
### Fixed
-->

## [Unreleased]

## Released
## [1.0.0] - 2023-10-03

### Added
- Initial micropython-rockwren version
- Support for Raspberry Pi Pico W and ESP8266
- MQTT client with certificate support (e.g. AWS IoT)
- Web interface
  - Extendable web interface for device specific controls
  - MQTT, WiFi configuration
  - Log viewer
  - Device information
- Access Point mode for device configuration
- Home Assistant discovery
- Example device apps
  - [esp8266_led_light](https://github.com/ccrighton/micropython-rockwren/examples/esp8266_led_light)
  - [pico_led_light](https://github.com/ccrighton/micropython-rockwren/examples/pico_led_light)
  - [pico_binary_sensor](https://github.com/ccrighton/micropython-rockwren/examples/pico_binary_sensor)
  - [pico_temperature](https://github.com/ccrighton/micropython-rockwren/examples/pico_temperature)
  - [pico_switch](https://github.com/ccrighton/micropython-rockwren/examples/pico_switch)

- Makefile for build, flash and distribution
  - Build esp8266 port with Rockwren and dependencies as frozen modules
- Documentation


<!-- Links -->
[Unreleased]: https://github.com/ccrighton/micropython-rockwren/tree/1.0.0...main

[1.0.0]: https://github.com/ccrighton/micropython-rockwren/tree/1.0.0
