# SPDX-FileCopyrightText: 2023 Charles Crighton <code@crighton.net.nz>
#
# SPDX-License-Identifier: GPL-3.0-or-later
from micropython import const
""" Global variables set from jsondb on boot """
SSID = ''
FIRST_BOOT = False
MQTT_SERVER = ''
MQTT_PORT = 0
MQTT_CLIENT_CERT = None
MQTT_CLIENT_KEY = None
PUBLISH_INTERVAL = const(10)
MQTT_KEEPALIVE = const(15)
CONNECTION_PARAMS = []
LIGHT_STATE = ""
