#!/bin/bash

set -e
set -o pipefail

pylint
py.test


