import os
import sys
import shutil
from pathlib import Path
from configparser import ConfigParser
import logging

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

def repr2value(k, v):  # for python
    a = k
    k = k.split(".")[-1]
    if k in STRING:
        pass
    elif k in PATH:
        v = Path(v)
    elif k in BOOLEAN:
        v = int(v)
    elif k in LIST:
        v = tuple(c.strip() for c in v.split(","))
    elif k in INTEGER:
        v = int(v)
    elif k in FLOAT:
        v = float(v)
    else:
        logging.info(f"This config is not defined : {k} : {v}")

    k = a
    return k, v


def value2repr(k, v):  # for pyqt
    a = k
    k = k.split(".")[-1]
    if k in STRING:
        pass
    elif k in PATH:
        v = str(v)
    elif k in BOOLEAN:
        v = int(v)
    elif k in LIST:
        v = ",".join(v)  # tuple(c.strip() for c in v.split(","))
    elif k in INTEGER:
        v = v
    elif k in FLOAT:
        v = str(v)
    else:
        logging.info(f"This config is not defined : {k} : {v}")

    k = a
    return k, v


def value2conf(k, v):  # for config
    a = k
    k = k.split(".")[-1]
    if k in STRING:
        pass
    elif k in PATH:
        v = str(v)
    elif k in BOOLEAN:
        v = str(v)
    elif k in LIST:
        v = ",".join(v)  # tuple(c.strip() for c in v.split(","))
    elif k in INTEGER:
        v = str(v)
    elif k in FLOAT:
        v = str(v)
    else:
        logging.info(f"This config is not defined : {k} : {v}")

    k = a
    return k, v


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

        self.load_config()

    def generate_config(self):
        logging.info(f"Create config at {self.configfile}")
        shutil.copy(DEFAULT_CONFIG_PATH, self.configfile)

    def __getitem__(self, k):
        if isinstance(k, tuple):
            k = ".".join(k)

        if k not in self.keys():
            logging.info(f"No entry for '{k}' in config")
            self.generate_config()
            self.load_config()

        return super().__getitem__(k)

    def __setitem__(self, k, v):
        if isinstance(k, tuple):
            k = ".".join(k)
        k, v = repr2value(k, v)

        super().__setitem__(k, v)

    def load_config(self):

        self.config = ConfigParser(interpolation=None)
        self.config.read(self.configfile)

        for section in self.config.sections():
            items = self.config.items(section)
            for key, value in items:
                self[".".join((section.lower(), key))] = value

    def save_config(self):
        for key, value in self.items():
            section, param = key.rsplit(".", 1)
            _, value = value2conf(param, value)
            self.config[section.upper()][param] = value

        with open(self.configfile, "w") as f:
            self.config.write(f)

    def get_repr(self, k):
        if isinstance(k, tuple):
            k = ".".join(k)
        if k not in self:  # config['DEFAULT']:
            logging.info(f"No entry for '{k}' in config")
            logging.info("Regenerating config file...")
            self.generate_config()
            self.load_config()

        k, v = value2repr(k, self[k])
        return v  # .config["DEFAULT"][k]

    def reset(self):

        param2keep = ['interface.size','interface.mode','interface.lang']
        config_2_keep = {p:self[p] for p in param2keep}

        self.configfile, conf_swap = DEFAULT_CONFIG_PATH, self.configfile
        self.load_config()
        self.configfile = conf_swap

        for p in param2keep:
            self[p] = config_2_keep[p]

    def walk(self):

        for k,v in self.items():
            yield k.rsplit('.', 1), v





CONFIG = ConfigDict()
