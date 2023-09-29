<!--
SPDX-FileCopyrightText: 2023 Charles Crighton <code@crighton.net.nz>

SPDX-License-Identifier: CC-BY-4.0
-->

# Rockwren Tutorial

Rockwren is designed to support a wide range of devices: lights, sensors, switches, and other controls.  Rockwren
provides Python, HTTP and Javascript APIs to support new device development. This tutorial walks through the basic
steps for adding functionality to a rockwren device.

## A Minimal Rockwren Device

A minimal rockwren device only needs a ```main.py``` that passes a device class to ```rockwren.fly```.

After installing rockwren, the ```main.py``` module in this tutorial needs

```python
from rockwren import rockwren

rockwren.fly(rockwren.Device())
```

The device will provide a web interface and MQTT support for turning on and off but these controls do not result in any
physical action in the device.

## Adding Some Behaviour

The Pico W has an onboard LED that can be controlled.  Add the LED pin to the device and use the default on and off
commands to turn the onboard LED on and off.

```python
from machine import Pin

from rockwren import rockwren


class PicoWLED(rockwren.Device):

    def __init__(self):
        self.led = Pin("LED", Pin.OUT)
        super().__init__(name="PicoWLED")

    def apply_state(self):

        if self.state == "ON":
            self.led.on()
        elif self.state == "OFF":
            self.led.off()

        super().apply_state()  # Always call last

rockwren.fly(PicoWLED())
```

This device will provides a web interface to turn the onboard LED on and off. Use the TOGGLE button
as shown below to control the LED.

In this example, ```__init__``` must be extended to create the instance variable ```self.led```.  The ```apply_state```
method must be extended to turn the led on or off based on the state of the device.

![Main screen](/main-screen.png)

## Add support for MQTT Commands

The device can now be controlled from the web UI to toggle the onboard LED.  However, to support control
via MQTT the ```command_handler``` method of the device must be extended in the example above.

```python
    def command_handler(self, topic, message):
        if message.get("state"):
            if message.get("state").upper() == "ON":
                self.on()
            elif message.get("state").upper() == "OFF":
                self.off()
        super().command_handler(topic, message)  # Always call last
```

The ```command_handler``` receives a decoded json object.  The two messages supported are ```{"state": "ON"}```
and ```{"state": "OFF"}```.

To receive the MQTT commands click the ```MQTT Configuration``` button on the main screen of the
web UI.  Once the device is connected successfully to an MQTT server these command can be sent to control
the device.

A command can be published to the device using the [mosquitto_pub](https://mosquitto.org/man/mosquitto_pub-1.html) tool
included with the [mosquitto](https://mosquitto.org/) MQTT server.

The topic ```rockwren/e6614103e7328b23/state``` show below is unique to the device.  The topic can be found by clicking
the ```Device Information``` button on the main screen of the web UI.  Use the mqtt command-topic.

```commandline
mosquitto_pub -h 192.168.1.7 -p 1883 -t "rockwren/e6614103e7328b23/state" -m '{"state": "ON"}'
```

In the device logs (click the ```View Logs``` button on the main screen of the web UI), the command will be
logged and the change of state.
```text
2023-09-29 07:36:19 [info     / 122kB] mqtt: b'rockwren/e6614103e7328b23/state' {"state": "ON"}
2023-09-29 07:36:20 [info     / 105kB] > GET /log (200 OK) [407ms]
2023-09-29 07:36:25 [info     / 120kB] > GET /log (200 OK) [182ms]2023-09-29 07:36:26 [debug    / 129kB] _mqtt_command_handler: b'rockwren/e6614103e7328b23/command': {'state': 'OFF'}
2023-09-29 07:36:26 [info     / 127kB] mqtt: b'rockwren/e6614103e7328b23/state' {"state": "OFF"}
```

## Add Home Assistant Discovery

Rockwren supports sending MQTT discovery messages for [Home Assistant](https://www.home-assistant.io/) discovery.

Rockwren provides a default discovery message for a light that can be used to switch the onboard LED on and off.  Add the following discovery declaration method to the device class above.

```python
    from rockwren import mqtt_client

    def discovery_function(self):
        return mqtt_client.default_discovery(self.mqtt_client)
```

The ```discovery_function``` returns a list of discovery messages to send to Home Assistant.  For a simple light a
single message is sent.  For more complex devices, multiple discovery messages can be sent.

## Updating The Device Controls In The Web UI

Rockwren provides a basic control UI out of the box that displays the state of the device (ON or OFF) and provides a
single TOGGLE button to change the state.

![Main Screen Controls](/main-screen-controls.png)

There are two parts of this UI control:
- Current state display (ON or OFF)
- An HTML input to control the device (in this case a single button labelled TOGGLE)

This control is provided by a block of html that is included in the rendering of the main web UI page.
The default block is shown below.  To customise the web UI device control this block must be copied to the root
folder of the device in a file named, by convention, ```controls.html``` with the ```main.py``` script.

The device class must set the ```self.template``` instance attribute to install the custom control block.

```python
    def __init__(self):
        self.led = Pin("LED", Pin.OUT)
        super().__init__(name="PicoWLED")
        self.template = "/controls.html"  # must be last
```

The default ```controls.html```
```html
{{'<h3 id="device-state" style="color:#008000;">ON</h3>' if device.is_on() else '<h3 id="device-state" style="color:#FF0000;">OFF</h3>'}}
<p><button  class="button" id='b1' onclick="deviceControl('b1', 'toggle', 'true')">TOGGLE</button></p>
```

The first line is the state display.  It uses a [Phew web server template](https://github.com/ccrighton/phew#templates)
to set the initial state based on the device.  The ```device``` variable in the template is the ```rockwren.Device```
class that is extended in the example above.  As this can be customised, so can the templates be customised.

```device-state``` is supported out-of-the-box and is updated automatically by the web UI.

The second line is the control button for the device. Rockwren provides a simple device control Javascript API.  When
an event in the web UI is received for a device update, the ```deviceControl(id, attribute, value)``` function must be called.

The id argument is the id of the source of the event. In this case the button with id ```b1```.  This will
enable rockwren to disable the source of the event while a command is posted via HTTP to the device.  This prevents
unwanted double clicks.

The attribute argument is the attribute to send to the device set to the contents of the value argument.

In this example, ```deviceControl('b1', 'toggle', 'true')``` causes a json message ```{"toggle":"true"}``` to be sent
to the device when the button ```onclick``` event is received.

To add ON and OFF buttons to the controls block the following html block in ```controls.html``` can be loaded on
the device.

```html
{{'<h3 id="device-state" style="color:#008000;">ON</h3>' if device.is_on() else '<h3 id="device-state" style="color:#FF0000;">OFF</h3>'}}
<p><button  class="button" id='b1' onclick="deviceControl('b1', 'toggle', 'true')">TOGGLE</button></p>
<p><button  class="button" id='b2' onclick="deviceControl('b2', 'state', 'ON')">ON</button></p>
<p><button  class="button" id='b3' onclick="deviceControl('b3', 'state', 'OFF')">OFF</button></p>
```

```controls.html``` can also be extended with javascript and css to provide highly configurable controls.  The
[pico_temperature](https://github.com/ccrighton/rockwren/examples/pico_temperature) example has a
[controls.html](https://github.com/ccrighton/rockwren/examples/pico_temperature/controls.html) with both javascript
and css style blocks.

## What next?

Check out the other example device applications for the Pico W:
  - [pico_led_light](https://github.com/ccrighton/rockwren/examples/pico_led_light)
  - [pico_binary_sensor](https://github.com/ccrighton/rockwren/examples/pico_binary_sensor)
  - [pico_temperature](https://github.com/ccrighton/rockwren/examples/pico_temperature)
  - [pico_switch](https://github.com/ccrighton/rockwren/examples/pico_switch)
