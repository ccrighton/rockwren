import machine
import uasyncio
from machine import Pin
import rockwren.env as env
import rockwren.networking as networking
import rockwren.rockwren as rockwren
from phew import server, template, logging

dir_path=__file__[:__file__.rfind('/')]

webapp = server.Phew()

# device represents the functions of the device
device: rockwren.Device = None


def run(loop):
    webapp.run_as_task(loop)


@webapp.route("/", methods=["GET"])
def mqtt_config(request):
    return template.render_template(dir_path + "/index.html",
                                    web_path=dir_path,
                                    device=device,
                                    ip_address=env.connection_params["ip_address"],
                                    subnet_mask=env.connection_params["subnet_mask"],
                                    gateway=env.connection_params["gateway"],
                                    dns_server=env.connection_params["dns_server"],
                                    mqtt_server=env.mqtt_server,
                                    mqtt_port=env.mqtt_port)


@webapp.route("/device/on")
def device_on(request):
    logging.info(f"Device: {device}")
    if device:
        device.on()
    return server.redirect("/", status=302)


@webapp.route("/device/off")
def device_off(request):
    logging.info(f"Device: {device}")
    if device:
        device.off()
    return server.redirect("/", status=302)


@webapp.route("/device/toggle")
def device_toggle(request):
    if device:
        device.toggle()
    return server.redirect("/", status=302)


async def delayed_restart(delay_secs):
    await uasyncio.sleep(delay_secs)
    machine.reset()


@webapp.route("/restart")
def restart(request):
    uasyncio.create_task(delayed_restart(5))
    return template.render_template(dir_path + "/restart.html", web_path=dir_path)


@webapp.route("/mqtt_config", methods=["GET"])
def mqtt_config(request):
    return template.render_template(dir_path + "/mqtt_config.html",
                                    web_path=dir_path,
                                    device=device,
                                    ip_address=env.connection_params["ip_address"],
                                    subnet_mask=env.connection_params["subnet_mask"],
                                    gateway=env.connection_params["gateway"],
                                    dns_server=env.connection_params["dns_server"],
                                    mqtt_server=env.mqtt_server,
                                    mqtt_port=env.mqtt_port)


@webapp.route("/favicon.svg", methods=["GET"])
def favicon(request):
    return server.serve_file(dir_path + "/favicon.svg")


@webapp.route("/mqtt_config", methods=["POST"])
def mqtt_config_save(request):
    if not request.form:
        return server.redirect("/mqtt_config", status=302)

    mqtt_config_updated = False

    mqtt_server = request.form.get("mqtt_server", None)
    if mqtt_server:
        numbers = mqtt_server.split(".")
        if len(numbers) == 4:
            networking.save_network_config_key("mqtt_server", mqtt_server)
            mqtt_config_updated = True
    mqtt_port = request.form.get("mqtt_port", None)
    if mqtt_port:
        networking.save_network_config_key("mqtt_port", int(mqtt_port))
        mqtt_config_updated = True

    if mqtt_config_updated:
        return server.redirect("/restart", status=302)
    else:
        return server.redirect("/mqtt_config", status=302)


@webapp.catchall()
def page_not_found(request):
    return template.render_template(dir_path + "/page_not_found.html", web_path=dir_path), 404
