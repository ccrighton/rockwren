# SPDX-FileCopyrightText: 2023 Charles Crighton <rockwren@crighton.nz>
#
# SPDX-License-Identifier: GPL-3.0-or-later
import time

import uasyncio
import ujson
from machine import Pin

from rockwren import mqtt_client
from rockwren import rockwren

interrupt_flag = uasyncio.ThreadSafeFlag()


def switch_callback(pin):
    interrupt_flag.set()


class PicoWSwitch(rockwren.Device):

    def __init__(self):
        self.pin = Pin(22, Pin.IN, Pin.PULL_UP)
        self.pin.irq(trigger=Pin.IRQ_FALLING, handler=switch_callback)
        uasyncio.create_task(self.switch_interrupt_handler())

        self.led = Pin("LED", Pin.OUT)
        super().__init__(name="PicoWSwitch", device_type=b"switch")  # Always call last

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

    async def switch_interrupt_handler(self):
        debounce_time = 0
        """ Switch interrupt handler """
        while True:
            await interrupt_flag.wait()
            if (time.ticks_ms() - debounce_time) > 300:
                print("Toggle switch")
                self.toggle()
                debounce_time = time.ticks_ms()

    def register_mqtt_client(self, _mqtt_client: mqtt_client.MqttDevice):
        super().register_mqtt_client(_mqtt_client)

    def discovery_function(self):
        return [("switch", {"unique_id": f"{self.mqtt_client.device_id}_switch",
                            "name": "Rockwren Pico W Switch",
                            "platform": "mqtt",
                            "state_topic": self.mqtt_client.state_topic,
                            "command_topic": self.mqtt_client.command_topic,
                            "payload_on": '{"state": "ON"}',
                            "payload_off": '{"state": "OFF"}',
                            "availability": {
                                "topic": self.mqtt_client.availability_topic
                            },
                            "device": {
                                "identifiers": [self.mqtt_client.device_id],
                                "name": f"Rockwren Pico W Switch",
                                "sw_version": "0.1",
                                "model": "",
                                "manufacturer": "Rockwren",
                                "configuration_url": f"http://{self.mqtt_client.connection_params['ip_address']}/"
                            }
                            })]


rockwren.fly(PicoWSwitch())
