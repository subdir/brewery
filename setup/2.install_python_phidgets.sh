#!/bin/bash

set -e
set -o pipefail

sudo apt-get update

sudo apt-get install --yes --no-install-recommends git ssh

if [[ -v DEVENV ]]; then
    sudo apt-get install --yes --no-install-recommends python3-setuptools

    [[ -d "${DEVENV}/phidgets-python3" ]] \
    || git clone git@github.com:subdir/phidgets-python3.git "${DEVENV}/phidgets-python3"
    (
        cd "${DEVENV}/phidgets-python3"
        python3 setup.py develop --user
    )

else
    git clone git@github.com:subdir/phidgets-python3.git
    (
        cd phidgets-python3
        sudo python3 setup.py install
    )
    sudo rm -rf phidgets-python3
fi

sudo apt-get remove --yes git ssh

