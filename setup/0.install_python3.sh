#!/bin/bash

set -e
set -o pipefail

sudo apt-get update
sudo apt-get install --yes --no-install-recommends python3

