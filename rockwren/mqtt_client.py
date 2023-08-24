# SPDX-FileCopyrightText: 2023 Charles Crighton <rockwren@crighton.nz>
#
# SPDX-License-Identifier: GPL-3.0-or-later
"""
MQTT device integration for Home Assistant discovery, connection, reconnection, state notification publication
and command handling for a device.
"""
import io
import sys
import time

import machine
import uasyncio
import ubinascii
import ujson
from umqtt.robust2 import MQTTClient

from . import env
from . import rockwren
from . import utils
from phew import logging


def noop_topic_handler(topic, message):
    """ No operation topic handler
    :param topic: mqtt topic
    :param message: mqtt message
    :return:
    """


class MqttDevice:
    """
    MQTT device integration for Home Assistant discovery, connection, reconnection, state notification publication
    and command handling for a device. Further details for configuring discovery messages can be found on the
    Home Assistant website:
    - https://www.home-assistant.io/integrations/mqtt/
    - https://www.home-assistant.io/integrations/light.mqtt/
    - https://www.home-assistant.io/integrations/switch.mqtt/
    """

    def __init__(self, device: rockwren.Device, mqtt_server, connection_params, state_topic=b"/state",
                 command_topic=b"/command", availability_topic=b"/LWT", command_handler=noop_topic_handler,
                 mqtt_port=0, client_id=b"rockwren", discovery_function=None):
        self.device = device  # Switch, light etc.
        # Register mqtt_publish_state as the listener for changes in state of the device
        self.device.register_listener(self.mqtt_publish_state)
        self.mqtt_server = mqtt_server
        self.mqtt_port = mqtt_port
        self.connection_params = connection_params

        self.client_id = client_id
        self.unique_id = ubinascii.hexlify(machine.unique_id())
        self.device_id = self.client_id + b"_" + self.unique_id

        self.device_topic = self.client_id + b'/' + self.unique_id
        self._topic_handlers = {}
        self.state_topic = self.device_topic + state_topic
        self.command_topic = self.device_topic + command_topic
        self.availability_topic = self.device_topic + availability_topic
        self.register_topic_handler(command_topic, command_handler)

        if discovery_function is None:
            self._discovery_functions = {device.device_type: default_discovery}
        else:
            self._discovery_functions = {device.device_type: discovery_function}

        self._publish_interval = env.PUBLISH_INTERVAL
        self._last_publish = 0
        self._mqtt_client = None
        self.status = {}
        self._status_reported = True
        self._commands = []
        self._max_commands = 10

    def subscription_callback(self, topic, msg, retained, duplicate):
        """ Received messages from subscribed topics will be delivered to this callback """
        topic = topic
        if topic not in self._topic_handlers.keys():
            # Not a registered command topic
            return
        if len(self._commands) > self._max_commands:
            logging.error(f"subscription_callback: Command queue full, discarding. {topic} {msg.decode()}")
            return
        try:
            decoded_msg = ujson.loads(msg)
            # Push the (topic, message) tuple
            self._commands.append((topic, decoded_msg))
        except Exception:
            logging.error(f"subscription_callback: Unknown message {topic} {msg.decode()}")

    def register_topic_handler(self, topic_suffix: bytes, topic_handler) -> None:
        """
        :param topic_suffix: Suffix to associate with the topic_handler function
        :param topic_handler:  Topic handler function
        """
        self._topic_handlers[self.device_topic + topic_suffix] = topic_handler

    def pop_message(self):
        """ Pop the (topic, message) tuple """
        if len(self._commands) == 0:
            return None, None
        return self._commands.pop(0)  # fifo

    def run(self, uasyncio_loop) -> None:
        """
        Initialise the mqtt client, establish the connection, execute the reconnection and command handler tasks
        :param uasyncio_loop: asyncio loop used for the mqtt client.  The mqtt client, reconnection handler and
                              command handler are all run as co-routines for this loop.
        """
        logging.info(f"Begin connection with MQTT Broker :: {self.mqtt_server}:{self.mqtt_port}")
        require_ssl = False
        ssl_params = None

        if env.MQTT_CLIENT_KEY and env.MQTT_CLIENT_CERT:
            ssl_params = {"key": utils.pem_to_der(env.MQTT_CLIENT_KEY),
                          "cert": utils.pem_to_der(env.MQTT_CLIENT_CERT),
                          "server_side": False}
            require_ssl = True

        self._mqtt_client = MQTTClient(self.device_id, self.mqtt_server,
                                       port=self.mqtt_port, keepalive=env.MQTT_KEEPALIVE,
                                       ssl=require_ssl, ssl_params=ssl_params)
        self._mqtt_client.DEBUG = True

        self._mqtt_client.set_last_will(self.availability_topic, b'offline', retain=True)
        self._mqtt_client.connect()

        uasyncio.create_task(self.ensure_connection())
        uasyncio.create_task(self._mqtt_command_handler())

        self._mqtt_client.set_callback(self.subscription_callback)

        self._mqtt_client.subscribe(self.device_topic + b'/#')
        self._mqtt_client.publish(self.availability_topic, b'online', retain=True)
        logging.info(
            f"Connected to MQTT  Broker :: {self.mqtt_server}, and waiting for callback function to be called.")
        self.send_discovery_msgs()

    async def ensure_connection(self):
        """ A asyncio co-routine for reconnecting to mqtt server """
        while True:
            if self._mqtt_client.is_conn_issue():
                while self._mqtt_client.is_conn_issue():
                    logging.info("mqtt trying to reconnect")
                    await uasyncio.sleep(1)
                    # If the connection is successful, the is_conn_issue
                    # method will not return a connection error.
                    try:
                        self._mqtt_client.reconnect()
                    except Exception as ex:
                        trace = io.StringIO()
                        sys.print_exception(ex, trace)
                        # Publish availability status and resubscribe on reconnection
                        logging.error(trace.getvalue())
                self._mqtt_client.publish(self.availability_topic, b'online', retain=True)
                self._mqtt_client.resubscribe()
            await uasyncio.sleep(1)

    def mqtt_publish_state(self) -> None:
        """ Publish the current device state on the state topic to the mqtt server """
        logging.info(f"mqtt: {self.state_topic} {self.device.json()}")
        self._mqtt_client.publish(self.state_topic, self.device.json())
        self._status_reported = True

    def register_discovery_function(self, device_type: bytes, func):
        """
        Register functions that produce discovery message objects.  Used for devices that require more than on
        discovery message.
        :param device_type: the device type e.g. light, switch, binary_sensor, button
        :param func: function that provides the discovery message
        :return: json encode-able object containing the discovery message
        """
        self._discovery_functions[device_type] = func

    def send_discovery_msgs(self):
        """ Send all registered discovery messages for the device. """
        for device_type, discovery_function in self._discovery_functions.items():
            discovery_topic = b"homeassistant/" + device_type + b"/" + self.device_id + b"/config"
            self._mqtt_client.publish(discovery_topic, ujson.dumps(discovery_function(self)))
            logging.info(f"Sending discovery message with topic {discovery_topic}")

    async def _mqtt_command_handler(self) -> None:
        """ MQTT command handler
            Asyncio co-routine """
        while True:
            await uasyncio.sleep(0)

            # Non-blocking wait for message
            self._mqtt_client.check_msg()

            # Publish state if publish interval has been reached
            current_time = time.time()
            if not self._status_reported or (current_time - self._last_publish) >= self._publish_interval:
                self.mqtt_publish_state()
                self._last_publish = current_time

            topic, message = self.pop_message()
            if message is None:
                continue

            logging.debug(f"_mqtt_command_handler: {topic}: {message}")

            handler = self._topic_handlers.get(topic)

            if handler is None:
                continue

            try:
                handler(topic, message)
            except Exception as ex:
                logging.error(f"Exception during execution of {handler.__name__} for topic {topic})")
                trace = io.StringIO()
                sys.print_exception(ex, trace)
                logging.error(trace.getvalue())

            self.mqtt_publish_state()


def default_discovery(mqtt_client: MqttDevice):
    """ Default Home Assistant discovery message for a json based MQTT Light.
        See https://www.home-assistant.io/integrations/light.mqtt/ """
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
