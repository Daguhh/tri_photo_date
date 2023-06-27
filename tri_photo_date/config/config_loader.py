import os
import sys
import shutil
from pathlib import Path
#from configparser import ConfigParser
import logging

import tomlkit

# try:
#    from .config_paths import CONFIG_DIR, APP_NAME
# except ModuleNotFoundError:
from tri_photo_date.cli.cli_argparser import (
    cli_arguments,
    CLI_DUMP,
    CLI_DUMP_DEFAULT,
    CLI_LOAD,
)
from tri_photo_date.config.config_paths import CONFIG_PATH, APP_NAME, DEFAULT_CONFIG_PATH, LOCALES_DIR
from tri_photo_date.config.config_types import STRING, LIST, PATH, BOOLEAN, INTEGER, FLOAT

cli_mode, config_path = cli_arguments()

if cli_mode == CLI_DUMP:
    shutil.copy(CONFIG_PATH, config_path)
    sys.exit(0)

if cli_mode == CLI_DUMP_DEFAULT:
    shutil.copy(DEFAULT_CONFIG_PATH, config_path)
    sys.exit(0)

if cli_mode == CLI_LOAD:
    CONFIG_PATH = config_path


CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

LANG_LIST = list(os.listdir(LOCALES_DIR))# ["fr", "en"]

def pyqt2value(k, v):

    if k in BOOLEAN:
        v = bool(v) #2 * int(v)
    elif k in LIST:
        v = tuple(c.strip() for c in v.split(","))
    elif k in FLOAT:
        v = float(v)

    return v

def value2pyqt(k, v):  # for pyqt

    if k in BOOLEAN:
        v = 2 * int(v)
    elif k in LIST:
        v = ",".join(v)  # tuple(c.strip() for c in v.split(","))
    elif k in FLOAT:
        v = str(v)

    return v

TRUE = ['1', 'y','yes', 'true', True]
FALSE = ['0', 'n', 'no', 'false', False]
# STRING, LIST, PATH, BOOLEAN, INTEGER, FLOAT
def shell2value(k, v):  # for pyqt

    if k in BOOLEAN:
        v = 2 * int(v.lower() in TRUE)
    elif k in LIST:
        v = tuple(c.strip() for c in v.split(","))
    elif k in FLOAT:
        v = float(v)
    elif k in INTEGER:
        v = int(v)

    return v

def value2shell(k, v):  # for pyqt

    if k in BOOLEAN:
        v = "true" if v else 'false'
    elif k in LIST:
        v = ", ".join(v)  # tuple(c.strip() for c in v.split(","))
    elif k in FLOAT:
        v = str(v)
    elif k in INTEGER:
        v = str(v)

    return v

class NoConfigFileError(Exception):
    def __str__(self):
        print(
            "There is no configuration file for path you gave",
            "Please run 'tri_photo_date --cli --dump <path>' to start from actual configuration",
        )
        sys.exit(1)

class ConfigDict(dict):
    def __init__(self, config_path=None):
        super(ConfigDict, self).__init__()

        # Try do get user config path
        if config_path is not None:
            self.configfile = Path(config_path)
            if not self.configfile.exists():
                raise NoConfigFileError
        else:
            self.configfile = CONFIG_PATH

        if not self.configfile.exists():
            self.generate_config()

        self.load_config(self.configfile)

    def generate_config(self):
        logging.info(f"Create config at {self.configfile}")
        shutil.copy(DEFAULT_CONFIG_PATH, self.configfile)

    def set_from_pyqt(self, k, v):

        s,p = k.rsplit('.', 1)
        v = pyqt2value(p,v)
        self[s][p] = v

    def get_to_pyqt(self, k):

        s,p = k.rsplit('.', 1)
        return value2pyqt(p, self[s][p])

    def set_from_shell(self, k, v):

        s,p = k.rsplit('.', 1)
        self[s][p] = shell2value(p, v)

    def get_to_shell(self, k):

        s,p = k.rsplit('.', 1)
        return value2shell(p, self[s][p])

    def load_config(self, config_file):

        with open(config_file, 'r') as f:
            self.doc = tomlkit.parse(f.read())
        self.update(self.doc)

    def save_config(self):

        self.doc.update(self)
        with open(self.configfile, 'w') as f:
            f.write(tomlkit.dumps(self.doc))

    def reset(self):

        keep_interface = self['interface']
        self.load_config(DEFAULT_CONFIG_PATH)
        self['interface'] = keep_interface

    def walk(self):

        for k,v in self.items():
            yield k.rsplit('.', 1), v

CONFIG = ConfigDict()
