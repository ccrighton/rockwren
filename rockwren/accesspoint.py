# SPDX-FileCopyrightText: 2023 Charles Crighton <code@crighton.net.nz>
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

from phew import logging
from phew import server
from phew import template
from . import networking
from . import utils

try:
    import usocket as socket
except Exception:
    import socket


ap = None
accesspointapp = server.Phew()
dir_path = "/lib/rockwren"
STATUS_CODE_404 = const(404)


@accesspointapp.route("/", methods=["GET", "POST"])
def wifi_setup(request):
    message = None
    if request.method == "POST":
        """ WiFI Setup handle post. """
        ssid = request.form.get("ssid", None)
        password = request.form.get("password", None)
        if ssid and password and ssid != "" and password != "":
            try:
                networking.save_network_config(ssid, password)
                return server.redirect("/restart", status=303)
            except Exception as ex:
                message = "wifi_config: failed to save network config"
                logging.error(message)

        else:
            message = "wifi_config: Invalid network parameters"
            logging.error(message)

    network_list = []
    try:
        if sys.platform != 'esp8266':
            network_list = networking.scan_networks(ap)
    except:
        pass

    return template.render_template(dir_path + "/wifi_setup.html",
                                    web_path=dir_path,
                                    networks=network_list,
                                    error=message)


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
