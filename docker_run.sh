#!/bin/bash

set -e
set -o pipefail

docker run \
    --rm \
    -ti \
    --workdir=/home/akimov/srcs/brewery \
    $(find /dev/bus/usb -type c|xargs -I'{}' echo '--device={}') \
    --volume=/home/akimov:/home/akimov \
    python-phidgets \
    "$@"

