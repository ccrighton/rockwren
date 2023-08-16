# SPDX-FileCopyrightText: 2023 Charles Crighton <rockwren@crighton.nz>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import uasyncio
import sys
import os
import ntptime
import rockwren.networking as networking
import rockwren.web as web
import rockwren.accesspoint as accesspoint
import rockwren.mqtt_client as mqtt_client
import rockwren.env as rockwren_env
from phew import server
from rockwren.mqtt_client import MqttDevice
import ujson


class Device:

    def __init__(self, name="RockwrenDevice", device_type="light"):
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

    def json(self):
        return ujson.dumps({'state': self.state})

    def on(self):
        self.state = "ON"
        self.apply_state()

    def off(self):
        self.state = "OFF"
        self.apply_state()

    def toggle(self):
        if self.is_on():
            self.off()
        else:
            self.on()

    def is_on(self):
        if self.state == "ON":
            return True
        else:
            return False

    def apply_state(self):
        """
        Apply the state of the device on change and notify listeners
        The implementation must call ``super.apply_state()`` last
        """
        self.notify_listeners()

    def notify_listeners(self):
        """
        notify all registered listeners of a change of state of the device
        :return:
        """
        for f in self.listeners:
            f()

    def register_listener(self, f):
        """
        Register state change listener functions
        :param f: listener function
        :return:
        """
        self.listeners.append(f)

    def register_web(self, _web: server.Phew):
        self.web = _web

    def register_mqtt_client(self, _mqtt_client: MqttDevice):
        self.mqtt_client = _mqtt_client

    def discovery_function(self):
        return None


def set_global_exception(loop):
    def handle_exception(loop, context):
        import sys
        sys.print_exception(context["exception"])
        sys.exit()
    loop.set_exception_handler(handle_exception)


def fly(the_device: Device):
    """
    Convenience method to start are device with default web and mqtt configuration
    :param device: device implementation
    :return:
    """

    web.device = the_device

    stats = os.statvfs('/')
    print(f"Free storage: {stats[0]*stats[3]/1024} KB")

    networking.load_network_config()

    # Initial wifi setup via access point
    if rockwren_env.ssid == '':
        try:
            set_global_exception()
            accesspoint.start_ap()
        except Exception as e:
            print(e)
        finally:
            sys.exit()

    # Normal operation with Wifi setup
    try:
        set_global_exception(uasyncio.get_event_loop())
        rockwren_env.connection_params = networking.connect()

        ntptime.settime()

        client = mqtt_client.MqttDevice(the_device, rockwren_env.mqtt_server, rockwren_env.connection_params,
                                        discovery_function=the_device.discovery_function(),
                                        command_handler=the_device.command_handler,
                                        mqtt_port=int(rockwren_env.mqtt_port))
        client.run(uasyncio.get_event_loop())

        web.run(uasyncio.get_event_loop())

        uasyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        print('Keyboard interrupt at loop level.')
    except Exception as e:
        sys.print_exception(e)
        uasyncio.new_event_loop()  # Clear retained state
        # machine.reset()
