# SPDX-FileCopyrightText: 2023 Charles Crighton <rockwren@crighton.nz>
#
# SPDX-License-Identifier: GPL-3.0-or-later
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
