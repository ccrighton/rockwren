# SPDX-FileCopyrightText: 2023 Charles Crighton <rockwren@crighton.nz>
#
# SPDX-License-Identifier: GPL-3.0-or-later
""" Access Point for Device WiFi setup. """
import io
import os
import sys

import machine
import network
import uasyncio
from micropython import const

from . import networking
from . import utils

try:
    import usocket as socket
except Exception:
    import socket

from phew import server, template, logging

ap = None
accesspointapp = server.Phew()
dir_path = "/lib/rockwren"
STATUS_CODE_404 = const(404)


def scan_networks(net: network.WLAN):
    """ Scan for WiFI networks. """
    networks = net.scan()  # list with tuples with 6 fields ssid, bssid, channel, RSSI, security, hidden
    networks.sort(key=lambda x: x[3], reverse=True)  # sorted on RSSI (3)
    network_list = []
    for w in networks:
        network_list.append((w[0].decode(), w[3]))
    return network_list


@accesspointapp.route("/", methods=["GET"])
def wifi_setup(request):
    """ Wifi Setup Home """
    network_list = []
    if sys.platform != 'esp8266':
        network_list = scan_networks(ap)

    logging.debug(network_list)
    return template.render_template(dir_path + "/wifi_setup.html",
                                    web_path=dir_path,
                                    networks=network_list,
                                    error="")


@accesspointapp.route("/setup", methods=["POST"])
def wifi_setup_save(request):
    """ WiFI Setup handle post. """
    ssid = request.form.get("ssid", None)
    password = request.form.get("password", None)
    if ssid and password and ssid != "" and password != "":
        try:
            networking.save_network_config(ssid, password)
        except Exception as ex:
            logging.error("wifi_setup_save: failed to save network config")

        return server.redirect("/restart", status=303)

    network_list = scan_networks(ap)

    return template.render_template(dir_path + "/wifi_setup.html",
                                    web_path=dir_path,
                                    networks=network_list,
                                    error="Invalid network parameters")


async def delayed_restart(delay_secs):
    """ Co-routine for delayed restart """
    await uasyncio.sleep(delay_secs)
    machine.reset()


@accesspointapp.route("/restart")
def restart(request):
    """ Restart device. """
    if networking.first_boot_present():
        uasyncio.create_task(delayed_restart(5))
    return template.render_template(dir_path + "/restart.html", web_path=dir_path)


@accesspointapp.route("/favicon.svg", methods=["GET"])
def favicon(request):
    """ Serve favicon. """
    return server.serve_file(dir_path + "/favicon.svg")


@accesspointapp.catchall()
def page_not_found(request):
    """ Handle page not found. """
    return template.render_template(dir_path + "/page_not_found.html",
                                    web_path=dir_path), STATUS_CODE_404


async def serve_client(reader, writer):
    """ Serve client co-routine """
    await accesspointapp.serve_client(reader, writer)


def start_ap():
    """ Start the access point. """
    global ap
    ssid = "rockwren"
    password = "12345678"
    ap = network.WLAN(network.AP_IF)
    print(f"essid={ssid}, password={password}")
    ap.config(essid=ssid, password=password)
    ap.active(True)

    while not ap.active():
        logging.info('Waiting for connection...')
        logging.info(ap.status())

    logging.info('Access point active')
    logging.info(ap.ifconfig())

    try:
        accesspointapp.run()
    except Exception as ex:
        trace = io.StringIO()
        sys.print_exception(ex, trace)
        utils.logstream(trace)
