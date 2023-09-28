<!--
SPDX-FileCopyrightText: 2023 Charles Crighton <code@crighton.net.nz>

SPDX-License-Identifier: GPL-3.0-or-later
-->

# [micropython-rockwren](https://github.com/ccrighton/rockwren)

Rockwren is a micropython device application framework to simplify the creation of
connected devices such as lights, switches, and sensors.  It is designed for the
Raspberry Pi Pico W but also runs on less capable devices such as the ESP8266.

Why call this package rockwren?

The [New Zealand rock wren (Pīwauwau)](https://www.doc.govt.nz/nature/native-animals/birds/birds-a-z/rock-wren-tuke/)
is a tiny but widely admired alpine bird that lives in the mountains of Fiordland in New Zealand. It ability to
live life year round in a very harsh environment and it's small size seemed apt when thinking of a name for this
micropython package.

## Features

- Web interface for configuration and device control
- MQTT client with certificate support (e.g. AWS IoT)
- Access Point mode for device configuration
- Home Assistant discovery via MQTT
- The web interface supports:
  - An extendable web interface for device specific controls and status display
  - MQTT, WiFi configuration
  - A log viewer
  - A device information viewer

## Dependencies
Rockwren depends on:
- [Micropython](https://micropython.org)
- A fork of the Pimoroni Phew web server: [Phew](https://github.com/ccrighton/phew)
- An MQTT client: [umqtt.simple2](https://github.com/fizista/micropython-umqtt.simple2) and [umqtt.robust2](https://github.com/fizista/micropython-umqtt.robust2) by [Wojciech Banaś](https://github.com/fizista)

## Installing from PyPI

### Thonny

See the [Pico guide](https://projects.raspberrypi.org/en/projects/introduction-to-the-pico)
for details on setting up Thonny and adding the Micropython firmware to your [Pico W](https://www.raspberrypi.com/documentation/microcontrollers/raspberry-pi-pico.html) or other similar device supporting micropython.

Once you have Thonny installed, the rockwren package can be installed.

1. Select ```Tools``` then ```Manage packages...```.
2. Enter ```micropython-rockwren```, click ```Search on PyPI```.
3. Click on ```micropython-rockwren``` in the search results.
4. Click on ```Install```.
5. Once the installation has completed, close the package window.

Rockwren is now installed on the Pico W.  Now install the sample application.

#### Pico W LED

This is a simple application that turns the onboard LED on and off from the web, home assistant, or via MQTT.

1. Create a new file in Thonny, paste the following code into it and save as ```main.py```.  When prompted for ```Where to save to?```, choose ```Raspberry Pi Pico```.
```python
from machine import Pin

from rockwren import mqtt_client
from rockwren import rockwren


class PicoWLED(rockwren.Device):

    def __init__(self):
        self.led = Pin("LED", Pin.OUT)
        super().__init__(name="PicoWLED", device_type=b"light")  # Always call last

    def apply_state(self):

        if self.state == "ON":
            self.led.on()
        elif self.state == "OFF":
            self.led.off()

        super().apply_state()  # Always call last

    def command_handler(self, topic, message):
        if message.get("state"):
            if message.get("state").upper() == "ON":
                self.on()
            elif message.get("state").upper() == "OFF":
                self.off()
        super().command_handler(topic, message)  # Always call last

    def discovery_function(self):
        return mqtt_client.default_discovery(self.mqtt_client)


rockwren.fly(PicoWLED())
```
2. Run the current script. Click ```Run``` and ```Run current script```.
   ```
   2023-09-29 00:15:36 [info     / 136kB] Free storage: 568.0 KB
   2023-09-29 00:15:36 [info     / 131kB] mqtt_server not set using default
   2023-09-29 00:15:36 [info     / 129kB] mqtt_port not set using default
   2023-09-29 00:15:36 [info     / 127kB] mqtt_client_cert not set using default
   2023-09-29 00:15:36 [info     / 125kB] mqtt_client_key not set using default
   essid=rockwren, password=12345678
   2023-09-29 00:15:36 [info     / 123kB] Access point active
   2023-09-29 00:15:36 [info     / 121kB] ('192.168.4.1', '255.255.255.0', '192.168.4.1', '0.0.0.0')
   2023-09-29 00:15:36 [info     / 119kB] > starting web server on port 80
   ```
3. This will start the device in access point mode.
4. Connect to the ```rockwren``` wifi access point.
5. In a browser navigate to [```http://192.168.4.1```](http://192.168.4.1)
6. Enter your SSID and password and click ```Submit```
7. A restart page will be displayed.
7. Once the device reboot it will connect to the SSID provided.
8. Use the IP address from the console on boot, an IP address scanner or check your router settings to find the IP
   address of your device.  One options is [Fing](https://www.fing.com/) for Android and iOS.  Choose the device called ```rockwren``` on the list displayed by the IP scanner or router.
9. Reconnect to the same SSID and in a browser navigate to IP address of the device.
10. Click ```TOGGLE``` to turn the Pico W LED on and off.

## Other Example Device Applications
  - [pico_led_light](https://github.com/ccrighton/micropython-rockwren/examples/pico_led_light)
  - [pico_binary_sensor](https://github.com/ccrighton/micropython-rockwren/examples/pico_binary_sensor)
  - [pico_temperature](https://github.com/ccrighton/micropython-rockwren/examples/pico_temperature)
  - [pico_switch](https://github.com/ccrighton/micropython-rockwren/examples/pico_switch)

## Further Documentation

Additional documentation on configuring and developing new devices is in github: [Rockwren Docs](https://github.com/ccrighton/rockwren/docs)
