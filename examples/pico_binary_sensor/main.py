# SPDX-FileCopyrightText: 2023 Charles Crighton <code@crighton.net.nz>
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


class PicoWBinarySensor(rockwren.Device):

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
            pin_value = self.pin.value()
            if pin_value:
                print("Door Open")
                self.on()  # On means open in Home Assistant
            elif (time.ticks_ms() - debounce_time) > 300:
                print("Door Closed")
                self.off()  # Off means closed in Home Assistant
                debounce_time = time.ticks_ms()

    def register_mqtt_client(self, _mqtt_client: mqtt_client.MqttDevice):
        super().register_mqtt_client(_mqtt_client)

    def discovery_function(self):
        return [("binary_sensor", {"unique_id": f"{self.mqtt_client.device_id}_door",
                                   "name": "Rockwren Pico W Door Position Binary Sensor",
                                   "platform": "door",
                                   "state_topic": self.mqtt_client.state_topic,
                                   "availability": {
                                       "topic": self.mqtt_client.availability_topic
                                   },
                                   "device": {
                                       "identifiers": [self.mqtt_client.device_id],
                                       "name": f"Rockwren Pico W Door Sensor",
                                       "sw_version": "1.0.0",
                                       "model": "",
                                       "manufacturer": "Rockwren",
                                       "configuration_url": f"http://{self.mqtt_client.connection_params['ip_address']}/"
                                   }
                                   })]


rockwren.fly(PicoWBinarySensor())
