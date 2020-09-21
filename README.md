# ETH High Voltage Client

Client to control and read out several HV supply units


##Installation:

setting up the environment and installing all required packages:
```shell
make prepare-dev
source venv/bin/activate
```

required python packages:
 - qdarkstyle, numpy, PyQt5, pyserial, matplotlib, termcolor, pyvisa
 
setting up the device rules:
```shell
make copy-rules
```
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
