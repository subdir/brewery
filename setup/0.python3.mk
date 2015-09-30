#!/usr/bin/make -f

.PHONY: build install nodevelop

build:

install:
	sudo apt-get update
	sudo apt-get install --yes --no-install-recommends python3

nodevelop:

