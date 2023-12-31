# SPDX-FileCopyrightText: 2023 Charles Crighton <code@crighton.net.nz>
#
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Device web interface for initial setup via access point and for configuration.
"""
import gc
import io
import sys

import machine
import uasyncio
from micropython import const

from . import env
from . import networking
from . import rockwren
from . import utils
from phew import logging
from phew import server
from phew import template

DIR_PATH = "/lib/rockwren"
STATUS_CODE_200 = const(200)
STATUS_CODE_302 = const(302)
STATUS_CODE_400 = const(400)
STATUS_CODE_404 = const(404)

# Web application for controlling the device
webapp = server.Phew()

# device represents the functions of the device
device: rockwren.Device = None


def run(loop) -> None:
    """ Run the web app as a task in the asyncio loop """
    webapp.run_as_task(loop)


@webapp.route("/", methods=["GET"])
def index(request):
    """ Home page """
    return template.render_template(DIR_PATH + "/index.html",
                                    web_path=DIR_PATH,
                                    device=device)


@webapp.route("/device", methods=["GET"])
def device_control(request):
    """ Return json formatted information about the device """
    if device:
        return server.Response(device.information(), 200, {"Content-Type": "application/json"})
    return "Device not found", STATUS_CODE_400


@webapp.route("/device/control", methods=["POST"])
def device_control(request):
    """ Handle device control messages """

    if not request.form:
        return server.Response('{"error": "Bad request"}', STATUS_CODE_400, {"Content-Type": "application/json"})
    if device:
        try:
            resp, status = device.web_post_handler(request.form)
            return server.Response(resp, status, {"Content-Type": "application/json"})
        except Exception as ex:
            try:
                trace = io.StringIO()
                sys.print_exception(ex, trace)
                utils.logstream(trace)
            finally:
                return server.Response('{"error": "Error handling device control request"}', STATUS_CODE_400,
                                       {"Content-Type": "application/json"})
    return server.Response('{"error": "Device not found"}', STATUS_CODE_400, {"Content-Type": "application/json"})


@webapp.route("/device/state", methods=["GET"])
def device_state(request):
    """ Get device state """

    if device:
        return server.Response(device.device_state(), STATUS_CODE_200, {"Content-Type": "application/json"})
    return server.Response('{"error": "Device not found"}', STATUS_CODE_400, {"Content-Type": "application/json"})


async def delayed_restart(delay_secs):
    """ Restart the device after delay_secs seconds. """
    await uasyncio.sleep(delay_secs)
    machine.reset()


@webapp.route("/restart")
def restart(request):
    """ Restart the device after a delay. """
    uasyncio.create_task(delayed_restart(5))
    return template.render_template(DIR_PATH + "/restart.html", web_path=DIR_PATH)


@webapp.route("/mqtt_config", methods=["GET"])
def mqtt_config(request):
    """ MQTT configuration """
    return template.render_template(DIR_PATH + "/mqtt_config.html",
                                    web_path=DIR_PATH,
                                    device=device,
                                    ip_address=env.CONNECTION_PARAMS["ip_address"],
                                    subnet_mask=env.CONNECTION_PARAMS["subnet_mask"],
                                    gateway=env.CONNECTION_PARAMS["gateway"],
                                    dns_server=env.CONNECTION_PARAMS["dns_server"],
                                    mqtt_server=env.MQTT_SERVER,
                                    mqtt_port=str(env.MQTT_PORT),
                                    mqtt_client_cert=env.MQTT_CLIENT_CERT,
                                    mqtt_client_key_stored=env.MQTT_CLIENT_KEY is not None)


@webapp.route("/favicon.svg", methods=["GET"])
def favicon(request):
    """" Serve favicon """
    return server.serve_file(DIR_PATH + "/favicon.svg")


@webapp.route("/log", methods=["GET"])
def favicon(request):
    """" Serve log file """
    if sys.platform == "esp8266":
        """ Do a gc before serving file to ensure sufficient memory """
        gc.collect()
    return server.serve_file("/log.txt")


@webapp.route("/mqtt_config", methods=["POST"])
def mqtt_config_save(request):
    """ Handle MQTT configuration form post """
    if not request.form:
        return server.redirect("/mqtt_config", status=STATUS_CODE_302)

    mqtt_config_updated = False

    mqtt_server = request.form.get("mqtt_server", None)
    if mqtt_server:
        numbers = mqtt_server.split(".")
        if len(numbers) == 4 and all(number.isdigit() for number in numbers):
            networking.save_network_config_key("mqtt_server", mqtt_server)
            mqtt_config_updated = True
        elif utils.is_fqdn(mqtt_server):
            networking.save_network_config_key("mqtt_server", mqtt_server)
            mqtt_config_updated = True
    else:
        networking.save_network_config_key("mqtt_server", "")
    mqtt_port = request.form.get("mqtt_port", None)
    if mqtt_port:
        networking.save_network_config_key("mqtt_port", int(mqtt_port))
        mqtt_config_updated = True

    mqtt_client_cert = request.form.get("mqtt_client_cert", None)
    if mqtt_client_cert:
        networking.save_network_config_key("mqtt_client_cert", mqtt_client_cert)
        mqtt_config_updated = True

    mqtt_client_key = request.form.get("mqtt_client_key", None)
    if mqtt_client_key:
        networking.save_network_config_key("mqtt_client_key", mqtt_client_key)
        mqtt_config_updated = True

    if mqtt_config_updated:
        return server.redirect("/restart", status=STATUS_CODE_302)
    else:
        return server.redirect("/mqtt_config", status=STATUS_CODE_302)


@webapp.route("/viewlogs", methods=["GET"])
def view_logs(request):
    """ View device logs """
    return template.render_template(DIR_PATH + "/viewlogs.html",
                                    web_path=DIR_PATH,
                                    device=device)


@webapp.route("/information", methods=["GET"])
def view_information(request):
    """ View device information """
    return template.render_template(DIR_PATH + "/information.html",
                                    web_path=DIR_PATH,
                                    device=device,
                                    ip_address=env.CONNECTION_PARAMS["ip_address"],
                                    subnet_mask=env.CONNECTION_PARAMS["subnet_mask"],
                                    gateway=env.CONNECTION_PARAMS["gateway"],
                                    dns_server=env.CONNECTION_PARAMS["dns_server"],
                                    mqtt_server=env.MQTT_SERVER,
                                    mqtt_port=env.MQTT_PORT)


@webapp.route("/wifi_config", methods=["GET", "POST"])
def wifi_config(request: server.Request):

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
            network_list = networking.scan_networks(env.CONNECTION_PARAMS["wlan"])
    except:
        pass

    return template.render_template(DIR_PATH + "/wifi_config.html",
                                    web_path=DIR_PATH,
                                    networks=network_list,
                                    error=message)


async def delayed_restart(delay_secs):
    """ Co-routine for delayed restart """
    await uasyncio.sleep(delay_secs)
    machine.reset()


@webapp.route("/restart")
def restart(request):
    """ Restart device. """
    if networking.first_boot_present():
        uasyncio.create_task(delayed_restart(5))
    return template.render_template(DIR_PATH + "/restart.html", web_path=DIR_PATH)


@webapp.catchall()
def page_not_found(request):
    """ 404 page not found """
    return template.render_template(DIR_PATH + "/page_not_found.html", web_path=DIR_PATH), STATUS_CODE_404
