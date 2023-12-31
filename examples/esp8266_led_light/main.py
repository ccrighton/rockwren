# SPDX-FileCopyrightText: 2023 Charles Crighton <code@crighton.net.nz>
#
# SPDX-License-Identifier: GPL-3.0-or-later
from machine import Pin

from rockwren import mqtt_client
from rockwren import rockwren


class Esp8266LED(rockwren.Device):

    def __init__(self):
        self.led = Pin(2, Pin.OUT)
        self.template = "/controls.html"
        super().__init__(name="ESP8266LED")  # Always call last

    def apply_state(self):

        # esp8266 onboard LED is inverted. High turns LED off, Low turns LED on.
        if self.state == "ON":
            self.led.off()
        elif self.state == "OFF":
            self.led.on()

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


rockwren.fly(Esp8266LED())
