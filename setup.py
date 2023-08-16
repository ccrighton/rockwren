# SPDX-FileCopyrightText: 2023 Charles Crighton <rockwren@crighton.nz>
#
# SPDX-License-Identifier: GPL-3.0-or-later
from setuptools import setup

setup(
    name="rockwren",
    version="0.0.1",
    description="Device integration solution (MQTT, Web) for MicroPython on the Pico W.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    project_urls={
        "GitHub": "https://bitbucket/ccrighton/rockwren"
    },
    author="Charlie Crighton",
    maintainer="Charlie Crighton",
    maintainer_email="rockwren@crighton.nz",
    license="GPLv3-or-later",
    license_files="LICENSES",
    packages=["rockwren"],
    data_files=[("rockwren", ["rockwren/favicon.svg",
                              "rockwren/index.html",
                              "rockwren/mqtt_config.html",
                              "rockwren/page_not_found.html",
                              "rockwren/restart.html",
                              "rockwren/style.css",
                              "rockwren/viewlogs.html",
                              "rockwren/wifi_setup.html"])]

)
