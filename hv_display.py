#!/usr/bin/env python
# --------------------------------------------------------
#       Script to start the HV Display
# created on September 17th 2020 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from src.gui import *

parser = ArgumentParser()
parser.add_argument('--config', '-c', help='Config file (name without .cfg)', default='keithley')
parser.add_argument('--start_time', '-s', nargs='?', help='set start time', default='now')
args = parser.parse_args()

config = load_config(join(dirname(realpath(__file__)), 'config', args.config), 'cfg')
device_list = get_logging_devices(config, args.start_time)

app = QApplication(['High Voltage Display'])
filterwarnings('ignore')
app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
g = Gui(device_list, from_logs=True)
end(app.exec_())
