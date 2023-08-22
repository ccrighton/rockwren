# SPDX-FileCopyrightText: 2023 Charles Crighton <rockwren@crighton.nz>
#
# SPDX-License-Identifier: GPL-3.0-or-later
"""

"""
import os
import sys

import ntptime
import uasyncio
import ujson

from . import accesspoint
from . import env as rockwren_env
from . import mqtt_client
from . import networking
from . import web
from phew import server


class Device:
    """
    Device represents the specific behaviour of the device to be implemented.
    This class is extended to implement the logic to send a discovery message
    to home assistant, handle mqtt commands, send mqtt status updates, change
    device state and so on.
    """

    def __init__(self, name="RockwrenDevice", device_type=b"light"):
        self.name = name
        self.device_type = device_type
        self.state = "OFF"
        self.web = None
        self.mqtt_client = None
        self.listeners = []
        self.apply_state()

    def __str__(self):
        return f"{self.name}(state={self.state})"

    def command_handler(self, topic, message):
        """
        Apply the state of the device on change and notify listeners
        The implementation must call ``super.command_handler()`` last.
        """
        self.apply_state()

    def json(self) -> str:
        """
        Return a json representation of the device encoded as a str. Used by `mqtt_client` to publish
        frequent state updates to the MQTT server. Overridden for each device that has more capability than on or off.
        :return: device state as json
        """
        return ujson.dumps({'state': self.state})

    def on(self):
        """ Update the device state to ON.  Override or extend when needed.
        If overridden, self.apply_state() must be called. """
        self.state = "ON"
        self.apply_state()

    def off(self):
        """ Update the device state to OFF.  Override or extend when needed.
        If overridden, self.apply_state() must be called. """
        self.state = "OFF"
        self.apply_state()

    def toggle(self):
        """ Update the device state by toggling.  Override or extend when needed.
        If overridden, self.apply_state() must be called. """
        if self.is_on():
            self.off()
        else:
            self.on()

    def is_on(self) -> bool:
        """
        Check if the device is in the ON state. Override or extend when needed.
        :return: True if device is on, False if the device is off.
        """
        return self.state == "ON"

    def apply_state(self):
        """
        Apply the state of the device on change and notify listeners
        The implementation must call ``super.apply_state()`` last.
        """
        self.notify_listeners()

    def notify_listeners(self) -> None:
        """
        Notify all registered listeners of a change of state of the device.
        Listeners are registered using ``Device.register_listener(func).``
        """
        for listener in self.listeners:
            listener()

    def register_listener(self, func) -> None:
        """
        Register state change listener functions.
        :param func: listener function
        """
        self.listeners.append(func)

    def register_web(self, _web: server.Phew) -> None:
        """
        Register the web server with the device.
        :param _web: Phew web server instance
        """
        self.web = _web

    def register_mqtt_client(self, _mqtt_client: mqtt_client.MqttDevice) -> None:
        """
        Register the ``mqtt_client``
        :param _mqtt_client:
        """
        self.mqtt_client = _mqtt_client

    def discovery_function(self):
        """
        The dicovery function to run for this device
        :return: the discovery function that produces a discovery json message
        """
        return None


def set_global_exception(loop):
    """ Set global exception to catch and output uncaught exceptions to aid debugging. """
    def handle_exception(loop, context):
        sys.print_exception(context["exception"])
        sys.exit()
    loop.set_exception_handler(handle_exception)


def fly(the_device: Device):
    """
    Convenience method to start a device with web and mqtt capabilities.
    :param the_device: device implementation
    """

    web.device = the_device

    stats = os.statvfs('/')
    print(f"Free storage: {stats[0]*stats[3]/1024} KB")

    networking.load_network_config()

    # Initial wifi setup via access point
    if rockwren_env.SSID == '':
        try:
            set_global_exception()
            accesspoint.start_ap()
        except Exception as ex:
            print(ex)
        finally:
            sys.exit()

    # Normal operation with Wifi setup
    try:
        set_global_exception(uasyncio.get_event_loop())
        rockwren_env.CONNECTION_PARAMS = networking.connect()

        ntptime.settime()

        client = mqtt_client.MqttDevice(the_device, rockwren_env.MQTT_SERVER, rockwren_env.CONNECTION_PARAMS,
                                        discovery_function=the_device.discovery_function(),
                                        command_handler=the_device.command_handler,
                                        mqtt_port=int(rockwren_env.MQTT_PORT))
        client.run(uasyncio.get_event_loop())

        web.run(uasyncio.get_event_loop())

        uasyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print('Keyboard interrupt at loop level.')
    except Exception as ex:
        sys.print_exception(ex)
        uasyncio.new_event_loop()  # Clear retained state
        # machine.reset()
