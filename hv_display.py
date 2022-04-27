#!/usr/bin/env python
# --------------------------------------------------------
#       Script to start the HV Display
# created on September 17th 2020 by M. Reichmann (remichae@phys.ethz.ch)
# --------------------------------------------------------

from HVClient.src.gui import *

parser = ArgumentParser()
parser.add_argument('--config', '-c', help='Config file (name without .cfg)', default='main')
parser.add_argument('--start_time', '-s', nargs='?', help='set start time', default='now')
args = parser.parse_args()

app = QApplication(['High Voltage Display'])
filterwarnings('ignore')

# fix for broken combobox...
exclude = ['QWidget::item:selected', 'QComboBox QAbstractItemView:selected', 'QComboBox::indicator', 'QComboBox::indicator'] + ['QComboBox::item'] * 3
style_str = remove_qss_entry(qdarkstyle.load_stylesheet_pyqt5(), *exclude)
style_str = change_qss_entry(style_str, 'QComboBox {', 'padding-right', '4px')
app.setStyleSheet(style_str)

Gui.query_devices(args.config)
Gui.query_channels(args.config)

device_list = get_logging_devices(args.config, args.start_time)

g = Gui(device_list, from_logs=True)
end(app.exec_())
