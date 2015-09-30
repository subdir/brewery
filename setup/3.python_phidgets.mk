#!/usr/bin/make -f

.PHONY: build install checkout develop

build:
	sudo apt-get update
	mkdir -p ~/.ssh/
	# github.com keys
	echo '|1|zbWizpAzhpQbpn/csdhkncl9WVY=|M/Vur29dOhXheRL8Fr0goblFpdg= ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAq2A7hRGmdnm9tUDbO9IDSwBK6TbQa+PXYPCPy6rbTrTtw7PHkccKrpp0yVhp5HdEIcKr6pLlVDBfOLX9QUsyCOV0wzfjIJNlGEYsdlLJizHhbn2mUjvSAHQqZETYP81eFzLQNnPHt4EVVUh7VfDESU84KezmD5QlWpXLmvU31/yMf+Se8xhHTvKSCZIFImWwoG6mbUoWf9nzpIoaSjB+weqqUUmpaaasXVal72J+UX2B+2RPW3RcT0eOzQgqlJL3RKrTJvdsjE3JEAvGq3lGHSZXy28G3skua2SmVi/w4yCE6gbODqnTWlg7+wC604ydGXA8VJiS5ap43JXiUFFAaQ==' >> ~/.ssh/known_hosts
	echo '|1|FFV+akl2cOIDhKhlj/PYVAH0J4M=|XFZQeK4RDReqcVmYYVSuW/t28JM= ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAq2A7hRGmdnm9tUDbO9IDSwBK6TbQa+PXYPCPy6rbTrTtw7PHkccKrpp0yVhp5HdEIcKr6pLlVDBfOLX9QUsyCOV0wzfjIJNlGEYsdlLJizHhbn2mUjvSAHQqZETYP81eFzLQNnPHt4EVVUh7VfDESU84KezmD5QlWpXLmvU31/yMf+Se8xhHTvKSCZIFImWwoG6mbUoWf9nzpIoaSjB+weqqUUmpaaasXVal72J+UX2B+2RPW3RcT0eOzQgqlJL3RKrTJvdsjE3JEAvGq3lGHSZXy28G3skua2SmVi/w4yCE6gbODqnTWlg7+wC604ydGXA8VJiS5ap43JXiUFFAaQ==' >> ~/.ssh/known_hosts
	sudo apt-get install --yes --no-install-recommends git ssh
	[ -d "phidgets-python3" ] || git clone git@github.com:subdir/phidgets-python3.git
	cd phidgets-python3 && git checkout master && python3 setup.py build

install:
	cd phidgets-python3 && sudo python3 setup.py install

checkout:
	[ -d "phidgets-python3" ] || git clone git@github.com:subdir/phidgets-python3.git
	cd phidgets-python3 && git checkout master

develop:
	cd phidgets-python3 && python3 setup.py install --user

