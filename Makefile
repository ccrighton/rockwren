#!/usr/bin/make -f
#
# SPDX-FileCopyrightText: 2023 Charles Crighton <code@crighton.net.nz>
#
# SPDX-License-Identifier: GPL-3.0-or-later

SHELL := /bin/bash
.ONESHELL:
.DEFAULT_GOAL:=help
.PHONY: help dist license-check dist dist-build clone-mp build-mp-esp8266 build-mpycross build-mp-esp8266-submodules \
        build-esp8266 activate-venv install-requirements copy-esp8266-modules flash-esp8266-firmware flash-esp8266 \
        install-example install-requirements reuse-annotate device-reset
.SILENT: help

ndefapp = $(if $(value $(1)),,$(error $(1) must be set to name of example application e.g. make flash-example APP=pico_switch))
ndeffile = $(if $(value $(1)),,$(error $(1) must be set to name of file to annotate e.g. make reuse-annotate FILE=requirements.txt))

UID := $(shell id -u)
PWD := $(shell pwd)

PORT ?= /dev/ttyUSB0
VENV ?= ~/.virtualenvs/rockwren

help:  ## Display this help
	$(info Rockwren build and flash targets)
	$(info )
	fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\:.*##/:/' | sed -e 's/##//'

dist: test license-check dist-build  ## Package rockwren python distribution

test:  ## Run test cases
	. ~/.virtualenvs/rockwren/bin/activate
	python -m unittest tests/*_test.py -v
	rm -f db.json

license-check:  ## Check reuse license compliance
	reuse lint

dist-build:
	. ~/.virtualenvs/rockwren/bin/activate
	rm -rf dist
	python -m build

clone-mp:
	mkdir build
	cd build
	@if [ ! -d micropython ] ; \
	then \
		git clone --recurse-submodules https://github.com/micropython/micropython.git
	fi

build-mpycross:
	docker run --rm -v ${HOME}:${HOME} -u ${UID} -w ${PWD}/build/micropython larsks/esp-open-sdk make -C mpy-cross

build-mp-esp8266-submodules:
	docker run --rm -v ${HOME}:${HOME} -u ${UID} -w ${PWD}/build/micropython larsks/esp-open-sdk make -C ports/esp8266 submodules

build-mp-esp8266:
	docker run --rm -v ${HOME}:${HOME} -u ${UID} -w ${PWD}/build/micropython larsks/esp-open-sdk make -C ports/esp8266 V=1 -j BOARD=ESP8266_GENERIC

stage-libraries: activate-venv install-requirements dist
	python unpack.py -f dist/micropython-rockwren-*.tar.gz -d build/lib -m rockwren
	python get-libs.py -o build/lib -m micropython-ccrighton-phew
	python get-libs.py -o build/lib -m micropython_umqtt.simple2
	python get-libs.py -o build/lib -m micropython_umqtt.robust2
	#-rm -r build/lib/*/__pycache__

copy-esp8266-modules: stage-libraries
	cp -r build/lib/umqtt ${PWD}/build/micropython/ports/esp8266/modules
	cp -r build/lib/rockwren ${PWD}/build/micropython/ports/esp8266/modules
	cp -r build/lib/phew ${PWD}/build/micropython/ports/esp8266/modules

flash-esp8266-firmware: activate-venv install-requirements
	python -m esptool --port ${PORT} --chip esp8266 --baud 460800 write_flash --flash_size detect 0 ${PWD}/build/micropython/ports/esp8266/build-ESP8266_GENERIC/firmware.bin
	sleep 5

build-esp8266: clone-mp build-mpycross build-mp-esp8266-submodules copy-esp8266-modules build-mp-esp8266  ## Build ESP8266 Firmware

flash-esp8266: flash-esp8266-firmware   ## Flash ESP8266 Rockwren firmware to device. PORT variable can be configured e.g. PORT=/dev/ttyUSB1
	mpremote cp build/lib/rockwren/*.html :lib/rockwren/
	mpremote cp build/lib/rockwren/*.css :lib/rockwren/
	mpremote cp build/lib/rockwren/*.svg :lib/rockwren/
	#
	mpremote reset

install-pico: stage-libraries  ## Install rockwren and dependencies on Raspberry Pi Pico W
	pipkin install --no-index --find-links dist --force-reinstall  rockwren
	pipkin install micropython-umqtt.simple2
	pipkin install micropython-umqtt.robust2
	pipkin install --no-index --find-links phew/dist --force-reinstall  ccrighton-phew
	cd build
	#mpremote cp -r lib :
	#mpremote reset

activate-venv:
	@source ${VENV}/bin/activate

install-requirements: activate-venv
	@pip install -r requirements.txt -q


install-example: activate-venv install-requirements  ## Flash example app to device.  APP variable must be set to name of app e.g. APP=pico_switch
	$(call ndefapp,APP)
	mpremote cp examples/$(APP)/* :

device-reset:  ## Reset the device (needed after an installation to run the app or via console and Ctrl-D)
	mpremote reset

clean:  ## Clean
	rm -r build

git-setup: activate-venv install-requirements  ## Set up git (pre-commit hooks)
	pre-commit install

reuse-annotate-gpl3:  ## Annotate files with copyright and license details. FILE variable must be set e.g. FILE=rockwren/rockwren.py
	$(call ndeffile,FILE)
	reuse annotate --license GPL-3.0-or-later --copyright "Charles Crighton <code@crighton.net.nz>" $(FILE)

reuse-annotate-cc-by-4:  ## Annotate files with copyright and license details. FILE variable must be set e.g. FILE=docs/main-screen.png
	$(call ndeffile,FILE)
	reuse annotate --license CC-BY-4.0 --copyright "Charles Crighton <code@crighton.net.nz>" $(FILE)

publish-testpypi:  ## Publish distribution file to TestPyPI
	. ~/.virtualenvs/rockwren/bin/activate
	python3 -m twine upload --repository testpypi dist/*

publish-pypi:  ## Publish distribution file to PyPI
	. ~/.virtualenvs/rockwren/bin/activate
	 python3 -m twine upload --repository pypi dist/*
