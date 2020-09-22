.PHONY: help prepare-dev clean

VENV_NAME?=venv
VENV_ACTIVATE=. $(VENV_NAME)/bin/activate
PYTHON=${VENV_NAME}/bin/python3

.DEFAULT: help
help:
	@echo "make prepare-dev"
	@echo "	   prepare development environment, use only once (needs sudo)"
	@echo "make venv"
	@echo "	   only create the virtual environment"
	@echo "make copy-rules"
	@echo "	   copyies the device rules to /etc/udev/rules.d and restarts udev"
	@echo "make clean"
	@echo "	   remove virtualenv and .egg-info"

prepare-dev:
	sudo apt-get -y install python3.6 python3-pip virtualenv
	make venv
	make copy-rules

venv: $(VENV_NAME)/bin/activate
$(VENV_NAME)/bin/activate: setup.py
	test -d $(VENV_NAME) || virtualenv -p python3 $(VENV_NAME)
	${PYTHON} -m pip install -U pip
	${PYTHON} -m pip install -e .
	touch $(VENV_NAME)/bin/activate

copy-rules:
	sudo cp config/88-hv-devices.rules /etc/udev/rules.d/
	sudo udevadm control --reload-rules
	sudo udevadm trigger

clean:
	rm -r *.egg-info
	rm -r $(VENV_NAME)