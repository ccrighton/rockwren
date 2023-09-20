#!/usr/bin/make -f
#
# SPDX-FileCopyrightText: 2023 Charles Crighton <code@crighton.nz>
#
# SPDX-License-Identifier: GPL-3.0-or-later

SHELL := /bin/bash
.ONESHELL:
.DEFAULT_GOAL:=help
.PHONY: build help
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
	fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'

dist: test license-check setup-sdist

test:  ## Run test cases
	. ./venv/Scripts/activate
	python -m unittest rockwren/*_test.py
	rm db.json

license-check:  ## Check reuse license compliance
	reuse lint

setup-sdist:  ## Package rockwren python distribution
	python setup.py sdist

build-esp8266: clone-mp build-mpycross build-mp-esp8266-submodules build-mp-esp8266  ## Build ESP8266 Firmware

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

copy-esp8266-modules:
	cp -r rockwren ${PWD}/build/micropython/ports/esp8266/modules
	cp -r phew/phew ${PWD}/build/micropython/ports/esp8266/modules
	python get-libs.py -o build/lib -m micropython_umqtt.simple2
	python get-libs.py -o build/lib -m micropython_umqtt.robust2
	cp -r build/lib/umqtt ${PWD}/build/micropython/ports/esp8266/modules

flash-esp8266-firmware: activate-venv install-requirements  ## Flash ESP8266 Rockwren firmware to device. PORT variable can be configured e.g. PORT=/dev/ttyUSB1
	python -m esptool --port ${PORT} --chip esp8266 --baud 460800 write_flash --flash_size detect 0 ${PWD}/build/micropython/ports/esp8266/build-ESP8266_GENERIC/firmware.bin

activate-venv:
	@source ${VENV}/bin/activate

install-requirements: activate-venv
	@pip install -r requirements.txt -q


flash-example: activate-venv install-requirements  ## Flash example app to device.  APP variable must be set to name of app e.g. APP=pico_switch
	$(call ndefapp,APP)
	mpremote cp examples/$(APP)/* :

clean:  ## Clean
	rm -r build

git-setup: activate-venv install-requirements  ## Set up git (pre-commit hooks)
	pre-commit install

reuse-annotate:  ## Annotate files with copyright and license details. FILE variable must be set.
	$(call ndeffile,FILE)
	reuse annotate --license GPL-3.0-or-later --copyright "Charles Crighton <code@crighton.nz>" $(FILE)
