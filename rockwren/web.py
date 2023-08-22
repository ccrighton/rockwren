# SPDX-FileCopyrightText: 2023 Charles Crighton <rockwren@crighton.nz>
#
# SPDX-License-Identifier: GPL-3.0-or-later
"""
Device web interface for initial setup via access point and for configuration.
"""
import machine
import uasyncio
from machine import Pin

from . import env
from . import networking
from . import rockwren
from . import utils
from phew import logging
from phew import server
from phew import template

DIR_PATH = "/lib/rockwren"

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
                                    device=device,
                                    ip_address=env.CONNECTION_PARAMS["ip_address"],
                                    subnet_mask=env.CONNECTION_PARAMS["subnet_mask"],
                                    gateway=env.CONNECTION_PARAMS["gateway"],
                                    dns_server=env.CONNECTION_PARAMS["dns_server"],
                                    mqtt_server=env.MQTT_SERVER,
                                    mqtt_port=env.MQTT_PORT)


@webapp.route("/device/on")
def device_on(request):
    """ Turn device on """
    logging.info(f"Device: {device}")
    if device:
        device.on()
    return server.redirect("/", status=302)


@webapp.route("/device/off")
def device_off(request):
    """ Turn device off """
    logging.info(f"Device: {device}")
    if device:
        device.off()
    return server.redirect("/", status=302)


@webapp.route("/device/toggle")
def device_toggle(request):
    """ Toggle device """
    if device:
        device.toggle()
    return server.redirect("/", status=302)


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


@webapp.route("/mqtt_config", methods=["POST"])
def mqtt_config_save(request):
    """ Handle MQTT configuration form post """
    if not request.form:
        return server.redirect("/mqtt_config", status=302)

    mqtt_config_updated = False

    mqtt_server = request.form.get("mqtt_server", None)
    if mqtt_server:
        print(f"{utils.is_fqdn(mqtt_server)}: '{mqtt_server}'")
        numbers = mqtt_server.split(".")
        if len(numbers) == 4 and all(number.isdigit() for number in numbers):
            networking.save_network_config_key("mqtt_server", mqtt_server)
            mqtt_config_updated = True
        elif utils.is_fqdn(mqtt_server):
            networking.save_network_config_key("mqtt_server", mqtt_server)
            mqtt_config_updated = True
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
        return server.redirect("/restart", status=302)
    else:
        return server.redirect("/mqtt_config", status=302)


@webapp.route("/viewlogs", methods=["GET"])
def view_logs(request):
    """ View device logs """
    log_text = ""
    with open("log.txt") as log_file:
        log_text = log_file.read()

    return template.render_template(DIR_PATH + "/viewlogs.html",
                                    web_path=DIR_PATH,
                                    device=device,
                                    logtext=log_text)


@webapp.catchall()
def page_not_found(request):
    """ 404 page not found """
    return template.render_template(DIR_PATH + "/page_not_found.html", web_path=DIR_PATH), 404
