# SPDX-FileCopyrightText: 2023 Charles Crighton <rockwren@crighton.nz>
#
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Network connectivity methods
"""
import sys
from socket import socket
from time import sleep

import machine
import network

from . import env
from . import jsondb
from . import secrets

FIRST_BOOT_KEY = "first_boot"
SSID_KEY = "ssid"
PASSWORD_KEY = "password"
ENV_FILE = "env.json"


def connect(hostname='rockwren'):
    """
    Establish WiFi Network Connection
    """

    # Connect to WLAN
    network.hostname(hostname)

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(env.SSID, secrets.SSID_PASSWORD)
    first_boot_retries = 0
    while not wlan.isconnected():
        print('Waiting for connection...')
        print(wlan.status())
        sleep(1)
        if env.FIRST_BOOT:
            if first_boot_retries >= 10:
                # failed to connect to SSID reset SSID and password and restart as AP for configuration
                reset_network_config()
                machine.reset()
            first_boot_retries += 1

    # Once initial connection to network complete, clear first_boot
    clear_first_boot()

    ip_address, subnet_mask, gateway, dns_server = wlan.ifconfig()
    print(f'Connected on {ip_address}')
    return {"ip_address": ip_address, "subnet_mask": subnet_mask, "gateway": gateway, "dns_server": dns_server}


def open_socket(ip_address, port):
    """
    Open a socket for an ip address and port
    :param ip_address: IP Address
    :return: connection
    """
    # Open a socket
    address = (ip_address, port)
    connection = socket.socket()
    connection.bind(address)
    connection.listen(1)
    print(connection)
    return connection


def reset_network_config() -> None:
    """ Reset network configuration.
        Removes ssid and ssid password and resets first boot.  Rockwren will reenter access point mode on reboot after
        calling this method. """
    database = jsondb.JsonDB(ENV_FILE)
    database[FIRST_BOOT_KEY] = False
    database[SSID_KEY] = ""
    database[PASSWORD_KEY] = ""
    database.save()
    env.FIRST_BOOT = database[FIRST_BOOT_KEY]
    env.SSID = database[SSID_KEY]
    secrets.SSID_PASSWORD = database[PASSWORD_KEY]


def load_network_config():
    """ Load network configuration from the json db file"""
    try:
        database = jsondb.JsonDB(ENV_FILE)
        database.load()
        if database.get(FIRST_BOOT_KEY) is None:
            database[FIRST_BOOT_KEY] = False
        if database.get(SSID_KEY) is None:
            database[SSID_KEY] = ""
        if database.get(PASSWORD_KEY) is None:
            database[PASSWORD_KEY] = ""
        database.save()
        env.FIRST_BOOT = database[FIRST_BOOT_KEY]
        env.SSID = database[SSID_KEY]
        secrets.SSID_PASSWORD = database[PASSWORD_KEY]
        try:
            env.MQTT_SERVER = database["mqtt_server"]
        except Exception:
            print("mqtt_server not set using default")
        try:
            env.MQTT_PORT = database["mqtt_port"]
        except Exception:
            print("mqtt_port not set using default")
        try:
            env.MQTT_CLIENT_CERT = database["mqtt_client_cert"]
        except Exception:
            print("mqtt_client_cert not set using default")
        try:
            env.MQTT_CLIENT_KEY = database["mqtt_client_key"]
        except Exception:
            print("mqtt_client_key not set using default")
    except Exception as ex:
        print("Exception loading network config: ")
        sys.print_exception(ex)


def save_network_config(ssid: str, password: str):
    """ Save network configuration to the json db file"""
    try:
        database = jsondb.JsonDB(ENV_FILE)
        database[FIRST_BOOT_KEY] = True
        database[SSID_KEY] = ssid
        database[PASSWORD_KEY] = password
        database.save()
    except Exception as ex:
        print("Exception saving network config: ")
        sys.print_exception(ex)


def save_network_config_key(key: str, value) -> None:
    """
    Save a network configuration key/value pair to the json db file.
    :param key: network config key
    :param value: network config value
    """
    try:
        database = jsondb.JsonDB(ENV_FILE)
        database.load()
        database[key] = value
        database.save()
    except Exception as ex:
        print("Exception saving network config: ")
        sys.print_exception(ex)


def clear_first_boot() -> None:
    """ Clear first boot setting the save in json db """
    database = jsondb.JsonDB(ENV_FILE)
    database.load()
    database[FIRST_BOOT_KEY] = False
    database.save()


def first_boot_present() -> bool:
    """ :returns True if first boot present otherwise False """
    database = jsondb.JsonDB(ENV_FILE)
    database.load()
    result = database.get(FIRST_BOOT_KEY) is not None and database[FIRST_BOOT_KEY]
    database.save()
    return result
