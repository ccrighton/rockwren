# SPDX-FileCopyrightText: 2023 Charles Crighton <code@crighton.net.nz>
#
# SPDX-License-Identifier: GPL-3.0-or-later
"""

"""
import gc
import io
import os
import sys

import machine
import ntptime
import uasyncio
import ubinascii
import ujson

from phew import logging
from phew import server
from . import accesspoint
from . import env as rockwren_env
from . import mqtt_client
from . import networking
from . import utils
from . import web
from .version import __version__


class Device:
    """
    Device represents the specific behaviour of the device to be implemented.
    This class is extended to implement the logic to send a discovery message
    to home assistant, handle mqtt commands, send mqtt status updates, change
    device state, handle web ui state changes and so on.
    """

    def __init__(self, name="RockwrenDevice", device_type=b"light"):
        self.name = name
        self.device_type = device_type
        self.state = "OFF"
        self.web = None
        self.mqtt_client: mqtt_client.MqttDevice = None
        self.listeners = []
        self.apply_state()
        """ HTML template path for use for controlling the device from the web ui. """
        self.template = "/lib/rockwren/controls.html"

    def __str__(self):
        return f"{self.name}(state={self.state})"

    def web_post_handler(self, form):
        """ Handle web ui device control changes. Extend or override to provide handling for the
            device change post requests. """
        logging.debug(form)
        if not form:
            return "Form not provided.", 400
        if form.get("state") and form.get("state").upper() == "ON":
            self.on()
        elif form.get("state") and form.get("state").upper() == "OFF":
            self.off()
        elif form.get("toggle"):
            """ Ignore value """
            self.toggle()
        return self.device_state(), 200

    def command_handler(self, topic, message):
        """
        Apply the state of the device on change and notify listeners
        The implementation must call ``super.command_handler()`` last.
        """
        self.apply_state()

    def device_state(self) -> str:
        """
        Return a json representation of the device encoded as a str. Used by `mqtt_client` to publish
        frequent state updates to the MQTT server. Overridden for each device that has more capability than on or off.
        :return: device state as json
        """
        return ujson.dumps({'state': self.state})

    def information(self) -> str:
        """
        Return a json representation of the device information encoded as a str. Extended or overridden for each device
        that has additional information.  Normally, best practice is to extended: get the information dictionary
        from this function then add to it to provide addition information.
        :return: device state as json
        """
        return ujson.dumps({'device': {
            'name': self.name,
            'type': self.device_type,
            'rockwren_version': __version__,
            'unique_id': ubinascii.hexlify(machine.unique_id()),
            'platform': sys.platform,
            'python_version': sys.version,
            'implementation': str(sys.implementation),
        },
            'mqtt': {
            'server': rockwren_env.MQTT_SERVER,
            'port': rockwren_env.MQTT_PORT,
            'command-topic': self.mqtt_client.command_topic,
            'availability-topic': self.mqtt_client.availability_topic,
            'state-topic': self.mqtt_client.state_topic,
        },
            'network': {
            'ssid': rockwren_env.SSID,
            'ip_address': rockwren_env.CONNECTION_PARAMS.get("ip_address"),
            'subnet_mask': rockwren_env.CONNECTION_PARAMS.get("subnet_mask"),
            'gateway': rockwren_env.CONNECTION_PARAMS.get("gateway"),
            'dns_server': rockwren_env.CONNECTION_PARAMS["dns_server"],
        }
        })

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

    def notify_listeners(self):
        """
        Notify all registered listeners of a change of state of the device.
        Listeners are registered using ``Device.register_listener(func).``
        """
        for listener in self.listeners:
            uasyncio.create_task(listener_task(listener))

    def register_listener(self, func):
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
        :return: an array of tuples (device_type, discovery_json).
        """
        return []


def set_global_exception(loop):
    """ Set global exception to catch and output uncaught exceptions to aid debugging. """
    def handle_exception(loop, context):
        trace = io.StringIO()
        sys.print_exception(context["exception"], trace)
        utils.logstream(trace)
        raise context["exception"]
    loop.set_exception_handler(handle_exception)


def fly(the_device: Device):
    """
    Convenience method to start a device with web and mqtt capabilities.
    :param the_device: device implementation
    """
    while True:
        gc.collect()

        # GC when more than 25% of the currently free heap becomes occupied.
        gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())

        web.device = the_device

        stats = os.statvfs('/')
        logging.info(f"Free storage: {stats[0]*stats[3]/1024} KB")

        networking.load_network_config()

        # Initial wifi setup via access point
        if rockwren_env.SSID == '':
            try:
                set_global_exception(uasyncio.get_event_loop())
                accesspoint.start_ap()
            except Exception as ex:
                trace = io.StringIO()
                sys.print_exception(ex, trace)
                utils.logstream(trace)
            finally:
                sys.exit()

        # Normal operation with Wifi setup
        try:
            set_global_exception(uasyncio.get_event_loop())
            rockwren_env.CONNECTION_PARAMS = networking.connect()

            ntptime.settime()

            client = mqtt_client.MqttDevice(the_device, rockwren_env.MQTT_SERVER, rockwren_env.CONNECTION_PARAMS,
                                            command_handler=the_device.command_handler,
                                            mqtt_port=int(rockwren_env.MQTT_PORT))
            client.run(uasyncio.get_event_loop())

            web.run(uasyncio.get_event_loop())

            uasyncio.get_event_loop().run_forever()
        except KeyboardInterrupt:
            logging.info('Keyboard interrupt at loop level.')
            break
        except Exception as ex:
            try:
                trace = io.StringIO()
                sys.print_exception(ex, trace)
                utils.logstream(trace)
                uasyncio.new_event_loop()  # Clear retained state
            finally:
                machine.reset()


async def listener_task(listener):
    listener()
