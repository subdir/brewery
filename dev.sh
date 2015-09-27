#!/bin/bash

set -e -o pipefail

make setup_devenv
devenv/run.sh -- --env="PYTHONPATH=phidgets-python3" "$(< docker/image_dev)" "$@"

