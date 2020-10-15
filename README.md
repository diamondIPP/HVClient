# ETH High Voltage Client

Client to control and read out several HV supply units


## Installation

setting up the environment and installing all required packages (sudo required):
### on linux
```shell
make prepare-dev
source venv/bin/activate
```

This install python3, virtualenv, and pip other required python packages such as:
 - qdarkstyle, numpy, PyQt5, pyserial, matplotlib, termcolor, pyvisa

If python3, pip and virtualenv are already install installed:
    - _create virtual environment and install required packages:_ 
```shell
make venv
source venv/bin/activate
```
    
 - _setting up the device rules:_ `make copy-rules` (ToDo: Linux only, what should be done on OSx)
 - or manually copy config/88-hv-devices.rules to /etc/udev/rules.d and restart udev


## Running

### HV Control
 - Gui with control features of the HV devcies
 - starts logging of the currents and voltages
```shell
./hv_client.py [-h] [-c] [-r] [-t]
```
 -  -h, --help:                  show help message and exit
 -  -c, --config \<configfile> : give config file name [default: "main"]
 -  -R, --restart:               restart hv devices (turn all OFF and set voltage to 0)
 -  -t, --test:                  start test environment with dummy devices

### HV Display
 - Gui to display the logged currents and voltages
```shell
./hv_display.py [-h] [-c] [-s]
```
 -  -h, --help:                  show help message and exit
 -  -c, --config \<configfile> : give config file name [default: "main"]
 -  -s, --start_time \<time>:    define time when to start the display [default: today, 00:00], format: hh:mm or dd.mm.
