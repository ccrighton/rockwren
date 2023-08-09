import machine
from time import sleep
from socket import socket
import network
import rockwren.env as env
import rockwren.secrets as secrets
import rockwren.jsondb as jsondb

FIRST_BOOT_KEY = "first_boot"
SSID_KEY = "ssid"
PASSWORD_KEY = "password"
ENV_FILE = "env.json"


'''
Network Connection
'''


def connect(hostname='rockwren'):
    # Connect to WLAN
    network.hostname(hostname)

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(env.ssid, secrets.ssid_password)
    first_boot_retries=0
    while not wlan.isconnected():
        print('Waiting for connection...')
        print(wlan.status())
        sleep(1)
        if env.first_boot:
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


def open_socket(ip):
    # Open a socket
    address = (ip, 80)
    connection = socket.socket()
    connection.bind(address)
    connection.listen(1)
    print(connection)
    return connection


'''
Network Configuration
'''


def reset_network_config():
    db = jsondb.JsonDB(ENV_FILE)
    db[FIRST_BOOT_KEY] = False
    db[SSID_KEY] = ""
    db[PASSWORD_KEY] = ""
    db.save()
    env.first_boot = db[FIRST_BOOT_KEY]
    env.ssid = db[SSID_KEY]
    secrets.ssid_password = db[PASSWORD_KEY]


def load_network_config():
    try:
        db = jsondb.JsonDB(ENV_FILE)
        db.load()
        if db[FIRST_BOOT_KEY] is None:
            db[FIRST_BOOT_KEY] = False
        if db[SSID_KEY] is None:
            db[SSID_KEY] = ""
        if db[PASSWORD_KEY] is None:
            db[PASSWORD_KEY] = ""
        db.save()
        env.first_boot = db[FIRST_BOOT_KEY]
        env.ssid = db[SSID_KEY]
        secrets.ssid_password = db[PASSWORD_KEY]
        try:
            env.mqtt_server = db["mqtt_server"]
        except:
            print("mqtt_server not set using default")
        try:
            env.mqtt_port = db["mqtt_port"]
        except:
            print("mqtt_port not set using default")
        try:
            env.mqtt_client_cert = db["mqtt_client_cert"]
        except:
            print("mqtt_port not set using default")
        try:
            env.mqtt_client_key = db["mqtt_client_key"]
        except:
            print("mqtt_port not set using default")
    except:
        print("Exception loading network config")


def save_network_config(ssid: str, password: str):
    try:
        db = jsondb.JsonDB(ENV_FILE)
        db[FIRST_BOOT_KEY] = True
        db[SSID_KEY] = ssid
        db[PASSWORD_KEY] = password
        db.save()
    except:
        print("Exception saving network config")


def save_network_config_key(key: str, value):
    try:
        db = jsondb.JsonDB(ENV_FILE)
        db.load()
        db[key] = value
        db.save()
    except:
        print("Exception saving network config")


def clear_first_boot():
    db = jsondb.JsonDB(ENV_FILE)
    db.load()
    db[FIRST_BOOT_KEY] = False
    db.save()


def first_boot_present():
    db = jsondb.JsonDB(ENV_FILE)
    db.load()
    result = db[FIRST_BOOT_KEY] is not None and db[FIRST_BOOT_KEY]
    db.save()
    return result
