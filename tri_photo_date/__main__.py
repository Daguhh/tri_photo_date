#!/usr/bin/env python3

import sys
from pathlib import Path
import argparse
import logging
from logging.handlers import RotatingFileHandler

from tri_photo_date.utils.config_paths import CONFIG_DIR

##### Set log file #####
print("log file : ", str(CONFIG_DIR / "tri_photo_date.log"))
handler = RotatingFileHandler(
    str(CONFIG_DIR / "tri_photo_date.log"), maxBytes=100000, backupCount=1
)
handler.setLevel(logging.INFO)

# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# handler.setFormatter(formatter)

# Add the handler to the root logger
logging.basicConfig(level=logging.INFO, handlers=[handler])


def run_cli():
    from tri_photo_date.cli.cli import cli_run

    cli_run()
    # ordonate_photos.main()


def run_gui():
    from PyQt5.QtGui import QIcon
    from PyQt5.QtWidgets import QApplication

    from tri_photo_date.gui import MainWindow

    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    sys.exit(app.exec_())


def main():
    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument("--cli", action="store_true", help="run cli")
    parser.add_argument("--gui", action="store_true", help="run gui")

    args, unknown = parser.parse_known_args()

    if args.cli:
        run_cli()

    else:  # args.gui:
        run_gui()


if __name__ == "__main__":
    main()
