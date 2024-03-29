#!/usr/bin/env python3

import sys
from pathlib import Path
import argparse
import logging
from logging.handlers import RotatingFileHandler

from tri_photo_date.config.config_paths import CONFIG_DIR
from tri_photo_date.cli.cli_argparser import parse_arguments

##### Set log file #####
handler = RotatingFileHandler(str(CONFIG_DIR / "tri_photo_date.log"), maxBytes=100000, backupCount=1)
handler.setLevel(logging.INFO)
logging.basicConfig(level=logging.INFO, handlers=[handler])

def run_shell(args):
    logging.info("Running cli")
    from tri_photo_date.cli.shell import shell_run
    shell_run(args)

def run_gui():
    logging.info("Running gui")
    from PyQt5.QtWidgets import QApplication
    from tri_photo_date.gui import MainWindow

    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec_())

def main():

    args, unknown = parse_arguments()

    if args.mode == 'gui' :
        run_gui()
    elif args.mode == 'shell':
        run_shell(unknown)

if __name__ == "__main__":
    main()
