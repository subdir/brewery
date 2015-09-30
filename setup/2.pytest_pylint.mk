#!/usr/bin/make -f

.PHONY: build install checkout develop

build:
install:

checkout:
develop:
	sudo apt-get update
	sudo apt-get install --yes --no-install-recommends python3-pip python3-setuptools
	sudo pip3 install pytest pylint

