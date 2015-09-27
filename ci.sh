#!/bin/bash

make docker/image_ci \
&& devenv/run.sh --no-volumes -- docker/image_ci "$@"

