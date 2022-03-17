# ETH High Voltage Client

Client to control and read out several HV supply units


## Installation

setting up the environment and installing all required packages (sudo required):
### on linux
 * 1a. full installation including _python3_, _virtualenv_, _pip_ and the required python packages:
    * `make prepare-dev`
 * 1b. only set up virtual environment and istall required packages (only applies if 1a is not required):
     * `make venv`
 * 2\. set the device rules (ToDo: Linux only, what should be done on MacOSx)
   * `make copy-rules`
   * or manually copy config/88-hv-devices.rules to /etc/udev/rules.d and restart udev
 * 3\. avtivate venv and set aliases
   * `source .bash_aliases`

## Running

### HV Control
 - Gui with control features of the HV devcies
 - starts logging of the currents and voltages
```shell
hv-client [-h] [-c] [-r] [-t]
```
 -  -h, --help:                  show help message and exit
 -  -c, --config \<configfile> : give config file name [default: "main"]
 -  -R, --restart:               restart hv devices (turn all OFF and set voltage to 0)
 -  -t, --test:                  start test environment with dummy devices

### HV Display
 - Gui to display the logged currents and voltages
```shell
hv-display [-h] [-c] [-s]
```
 - -h, --help:                  show help message and exit
 - -c, --config \<configfile> : give config file name [default: "main"]
 - -s, --start_time \<time>:    define time when to start the display [default: today, 00:00], format: hh:mm or dd.mm.

### HV Command Line Interface (CLI)
```shell
hv-cli [-h] [-c] [-r] [-t]
```
 - ditto HV control
