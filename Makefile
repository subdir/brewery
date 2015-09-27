.DELETE_ON_ERROR:
.SECONDARY:

SHELL := /bin/bash -e -o pipefail


.PHONY: setup_devenv
setup_devenv: devenv/run.sh phidgets-python3/.git/config


phidgets-python3/.git/config:
	git clone git@github.com:subdir/phidgets-python3.git


devenv/run.sh:
	git submodule init
	git submodule update


docker/image_%: docker/%/Dockerfile
	devenv/docker_build.sh "$$(dirname "$<")" > $@


docker/dev/Dockerfile: docker/Dockerfile-base docker/Dockerfile-test
	cat $^ > $@


docker/ci/Dockerfile: docker/Dockerfile-base docker/Dockerfile-test docker/Dockerfile-prod
	cat $^ > $@

