# SPDX-FileCopyrightText: 2023 Charles Crighton <rockwren@crighton.nz>
#
# SPDX-License-Identifier: GPL-3.0-or-later

import sys
import uasyncio

from umqtt.robust2 import MQTTClient
import time
import ubinascii
import machine
import ujson
import rockwren.env as env
import rockwren.rockwren as rockwren
import rockwren.utils as utils


def noop_topic_handler(topic, message):
    pass


class MqttTopicHandlerInterface:

    def topic_handler(self, device, topic, message):
        pass


class MqttDevice:

    def __init__(self, device: rockwren.Device, mqtt_server, connection_params, state_topic="/state",
                 command_topic="/command", availability_topic="/LWT", command_handler=noop_topic_handler,
                 mqtt_port=0, client_id="rockwren", discovery_function=None):
        self.device = device  # Switch, light etc.
        # Register mqtt_publish_state as the listener for changes in state of the device
        self.device.register_listener(self.mqtt_publish_state)
        self.MQTT_SERVER = mqtt_server
        self.MQTT_PORT = mqtt_port
        self.connection_params = connection_params

        self.client_id = client_id
        self.unique_id = ubinascii.hexlify(machine.unique_id()).decode()
        self.device_id = self.client_id + "_" + self.unique_id

        self.device_topic = self.client_id + '/' + self.unique_id
        self._topic_handlers = {}
        self.state_topic = self.device_topic + state_topic
        self.command_topic = self.device_topic + command_topic
        self.availability_topic = self.device_topic + availability_topic
        self.register_topic_handler(command_topic, command_handler)

        if discovery_function is None:
            self._discovery_functions = {device.device_type: default_discovery}
        else:
            self._discovery_functions = {device.device_type: discovery_function}

        self._publish_interval = env.publish_interval
        self._last_publish = 0
        self._mqtt_client = None
        self.status = {}
        self._status_reported = True
        self._commands = []
        self._max_commands = 10

    # Received messages from subscriptions will be delivered to this callback
    def subscription_callback(self, topic, msg, retained, duplicate):
        topic = topic.decode()
        if topic not in self._topic_handlers.keys():
            # Not a registered command topic
            return
        if len(self._commands) > self._max_commands:
            print(f"Command queue full, discarding. {topic} {msg.decode()}")
            return
        try:
            decoded_msg = ujson.loads(msg)
            # Push the (topic, message) tuple
            self._commands.append((topic, decoded_msg))
        except Exception:
            print(f"Unknown message {topic} {msg.decode()}")

    def register_topic_handler(self, topic_suffix, topic_handler):
        self._topic_handlers[self.device_topic + topic_suffix] = topic_handler

    def pop_message(self):
        """ Pop the (topic, message) tuple """
        if len(self._commands) == 0:
            return None, None
        return self._commands.pop(0)  # fifo

    def run(self, uasyncio_loop):
        print(f"Begin connection with MQTT Broker :: {self.MQTT_SERVER}:{self.MQTT_PORT}")
        require_ssl = False
        ssl_params = None

        if env.mqtt_client_key and env.mqtt_client_cert:
            ssl_params = {"key": utils.pem_to_der(env.mqtt_client_key),
                          "cert": utils.pem_to_der(env.mqtt_client_cert),
                          "server_side": False}
            require_ssl = True

        self._mqtt_client = MQTTClient(self.device_id.encode(), self.MQTT_SERVER.encode(),
                                       port=self.MQTT_PORT, keepalive=env.mqtt_keepalive,
                                       ssl=require_ssl, ssl_params=ssl_params)
        self._mqtt_client.DEBUG=True

        self._mqtt_client.set_last_will(self.availability_topic.encode(), b'offline', retain=True)
        self._mqtt_client.connect()

        uasyncio.create_task(self.ensure_connection())
        uasyncio.create_task(self.mqtt_command_handler())

        self._mqtt_client.set_callback(self.subscription_callback)

        self._mqtt_client.subscribe(self.device_topic.encode() + b'/#')
        self._mqtt_client.publish(self.availability_topic.encode(), b'online', retain=True)
        print(f"Connected to MQTT  Broker :: {self.MQTT_SERVER}, and waiting for callback function to be called.")
        self.send_discovery_msgs()

    async def ensure_connection(self):
        """ A asyncio co-routine for reconnecting to mqtt server """
        while True:
            if self._mqtt_client.is_conn_issue():
                while self._mqtt_client.is_conn_issue():
                    print("mqtt trying to reconnect")
                    await uasyncio.sleep(1)
                    # If the connection is successful, the is_conn_issue
                    # method will not return a connection error.
                    try:
                        self._mqtt_client.reconnect()
                    except Exception as e:
                        sys.print_exception(e)
                else:
                    self._mqtt_client.publish(self.availability_topic.encode(), b'online', retain=True)
                    self._mqtt_client.resubscribe()
            await uasyncio.sleep(1)

    def mqtt_publish_state(self):
        print(f"mqtt: {self.state_topic} {self.device.json()}")
        self._mqtt_client.publish(self.state_topic.encode(), self.device.json())
        self._status_reported = True

    def mqtt_check_non_blocking(self):
        # Non-blocking wait for message
        self._mqtt_client.check_msg()
        current_time = time.time()
        if not self._status_reported or (current_time - self._last_publish) >= self._publish_interval:
            self.mqtt_publish_state()
            self._last_publish = current_time

    def register_discovery_function(self, device_type, f):
        '''
        Register functions that produce discovery message objects
        :param device_type: the device type e.g. light, switch, binary_sensor, button
        :param f: function that provides the discovery message
        :return: json encode-able object containing the discovery message
        '''
        self._discovery_functions[device_type] = f

    def send_discovery_msgs(self):
        for device_type, discovery_function in self._discovery_functions.items():
            discovery_topic = "homeassistant/" + device_type + "/" + self.device_id + "/config"
            self._mqtt_client.publish(discovery_topic.encode(), ujson.dumps(discovery_function(self)))
            print(f"Sending discovery message with topic {discovery_topic}")

    async def mqtt_command_handler(self):
        """ MQTT command handler
            Asyncio co-routine """
        while True:
            await uasyncio.sleep(0)

            self.mqtt_check_non_blocking()
            topic, message = self.pop_message()
            if message is None:
                continue

            print(f"mqtt_command_handler: {topic}: {message}")

            handler = self._topic_handlers.get(topic)

            if handler is None:
                continue

            try:
                handler(topic, message)
            except Exception as e:
                print(f"Exception during execution of {handler.__name__} for topic {topic}: {e}")

            self.mqtt_publish_state()


def default_discovery(mqtt_client: MqttDevice):
    return {"unique_id": f"{mqtt_client.device_id}_{mqtt_client.device.device_type}",
            "name": mqtt_client.device.name,
            "platform": "mqtt",
            "schema": "json",
            "state_topic": mqtt_client.state_topic,
            "command_topic": mqtt_client.command_topic,
            "payload_on": "ON",
            "payload_off": "OFF",
            "availability": {
                "topic": mqtt_client.availability_topic
            },
            "device": {
                "identifiers": [mqtt_client.device_id],
                "name": f"Rockwren Pico W LED",
                "sw_version": "0.1",
                "model": "",
                "manufacturer": "Rockwren",
                "configuration_url": f"http://{mqtt_client.connection_params['ip_address']}/"
            }
            }



#    def send_remove_discovery(self):
#            self._mqtt_client.publish(discovery_topic, "")
#            self._mqtt_client.publish(discovery_topic_button, "")
#            self._mqtt_client.publish(discovery_topic_sensor, "")
