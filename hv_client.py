#!/usr/bin/env python
# --------------------------------------------------------
#       Script to start the HV Client
# created on September 17th 2020 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from src.gui import *

parser = ArgumentParser()
parser.add_argument('--config', '-c', help='Config file', default='keithley')
parser.add_argument('--restart', '-R', action='store_true', help='restart hv devices (turn all OFF and set voltage to 0)')
parser.add_argument('--test', '-t', action='store_true', help='start test environment')
args = parser.parse_args()

config = load_config(join(dirname(realpath(__file__)), 'config', args.config), 'cfg')
device_list = get_dummies(config) if args.test else get_devices(config, not args.restart, print_logs=True)

app = QApplication(['High Voltage Client'])
filterwarnings('ignore')
app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
g = Gui(device_list)
end(app.exec_())
