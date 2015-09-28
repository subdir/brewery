#!/bin/bash

set -e
set -o pipefail

sudo apt-get update
sudo apt-get install --yes --no-install-recommends \
    libc6-dev \
    libusb-dev \
    libusb++-dev

sudo apt-get install --yes --no-install-recommends curl gcc make
tmpdir=$(mktemp -d)
(
    cd "${tmpdir}"
    curl \
        'http://www.phidgets.com/downloads/libraries/libphidget_2.1.8.20150410.tar.gz' \
        -o libphidget.tar.gz
    tar --strip-components=1 -xz -f libphidget.tar.gz
    ./configure
    sudo make install
)
sudo rm -rf "${tmpdir}"
sudo apt-get remove --yes curl gcc make

