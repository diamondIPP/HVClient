#!/usr/bin/env python
# --------------------------------------------------------
#       Script to start the HV CLI
# created on March 17th 2022 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from HVClient.src.device_reader import *

parser = ArgumentParser()
parser.add_argument('--config', '-c', help='Config file', default='main')
parser.add_argument('--restart', '-R', action='store_true', help='restart hv devices (turn all OFF and set voltage to 0)')
parser.add_argument('--test', '-t', action='store_true', help='start test environment')
args = parser.parse_args()

devices = get_dummies(args.config) if args.test else get_devices(args.config, not args.restart, print_logs=True)
z = devices[0]
