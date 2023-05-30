#!/usr/bin/env python3

import sys
import os
from pathlib import Path
import argparse
import logging
from logging.handlers import RotatingFileHandler

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication


#try:
#    from utils.config_config_paths import CONFIG_DIR
#except ModuleNotFoundError:
from tri_photo_date.utils.config_paths import CONFIG_DIR

##### Set log file #####
print('log file : ', str(CONFIG_DIR/'tri_photo_date.log'))
handler = RotatingFileHandler(str('tri_photo_date.log'), maxBytes=50000, backupCount=1)
handler.setLevel(logging.INFO)

#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#handler.setFormatter(formatter)

# Add the handler to the root logger
logging.basicConfig(level=logging.INFO, handlers=[handler])

try:
    from gui import MainWindow
except ModuleNotFoundError:
    from tri_photo_date.gui import MainWindow
try:
    import ordonate_photos
except ModuleNotFoundError:
    from tri_photo_date import ordonate_photos

def run_cli():

    ordonate_photos.main()

def run_gui():

    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec_())

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument('--cli', action='store_true', help='run cli')
    parser.add_argument('--gui', action='store_true', help='run gui')

    args = parser.parse_args()

    if args.cli:
        run_cli()

    else: # args.gui:
        run_gui()

if __name__ == "__main__":

    main()



