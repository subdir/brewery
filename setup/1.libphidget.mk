#!/usr/bin/make -f

.PHONY: build install nodevelop

build:
	sudo apt-get update
	sudo apt-get install --yes --no-install-recommends \
	    curl \
	    tar \
	    gcc \
	    libc6-dev \
	    libusb-dev \
	    libusb++-dev
	curl \
	    'http://www.phidgets.com/downloads/libraries/libphidget_2.1.8.20150410.tar.gz' \
	    -o libphidget.tar.gz
	tar -xz -f libphidget.tar.gz
	cd libphidget-2.1.8.20150410 && ./configure && make && DESTDIR=`pwd`/dist make -e install

install:
	sudo apt-get update
	sudo apt-get install --yes --no-install-recommends libc6 libusb-0.1-4
	sudo cp -r libphidget-2.1.8.20150410/dist/* /

nodevelop:

