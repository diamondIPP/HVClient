#!/usr/bin/env python
# --------------------------------------------------------
#       Script to start the HV Client
# created on September 17th 2020 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from HVClient.src.gui import *

parser = ArgumentParser()
parser.add_argument('--config', '-c', help='Config file', default='main')
parser.add_argument('--restart', '-R', action='store_true', help='restart hv devices (turn all OFF and set voltage to 0)')
parser.add_argument('--test', '-t', action='store_true', help='start test environment')
args = parser.parse_args()


app = QApplication(['High Voltage Client'])
app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
filterwarnings('ignore')

Gui.query_devices(args.config)
Gui.query_channels(args.config)

device_list = get_dummies(args.config) if args.test else get_devices(args.config, not args.restart, print_logs=True)

g = Gui(device_list)

end(app.exec_())
