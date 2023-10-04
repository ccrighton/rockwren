# SPDX-FileCopyrightText: 2023 Charles Crighton <code@crighton.net.nz>
#
# SPDX-License-Identifier: GPL-3.0-or-later
import ujson
from machine import ADC
from machine import Timer

from rockwren import rockwren


class PicoWTemperature(rockwren.Device):
    """
    Rockwren temperature sensor example.  In this case the the onboard temperature
    measurement is used.
    """

    def __init__(self):
        self.timer = Timer(period=5000, mode=Timer.PERIODIC, callback=self.timer_callback)
        self.adc = ADC(4)
        self.temperature = 0
        super().__init__(name="PicoWTemperature")  # Always call last
        self.template = "/controls.html"
        self.update_temperature()

    def timer_callback(self, timer):
        self.update_temperature()

    def update_temperature(self):
        volts = self.adc.read_u16() * (3.3 / (65536))
        self.temperature = 27 - (volts - 0.706) / 0.001721
        self.apply_state()

    def device_state(self):

        return ujson.dumps({'temperature': self.temperature})

    def discovery_function(self):
        return [("sensor", {"unique_id": f"{self.mqtt_client.device_id}_sensor",
                            "name": "Pico W Temperature",
                            "platform": "mqtt",
                            "state_topic": self.mqtt_client.state_topic,
                            "unit_of_measurement": "C",
                            "value_template": "{{ value_json.temperature }}",
                            "availability": {
                                "topic": self.mqtt_client.availability_topic
                            },
                            "device": {
                                "identifiers": [self.mqtt_client.device_id],
                                "name": f"Pico W Temperature",
                                "sw_version": "1.0",
                                "model": "",
                                "manufacturer": "Rockwren",
                                "configuration_url": f"http://{self.mqtt_client.connection_params['ip_address']}/"
                            }
                            })]


rockwren.fly(PicoWTemperature())
