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
from tri_photo_date.utils.config_paths import CONFIG_PATH, APP_NAME, DEFAULT_CONFIG_PATH

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


LANG_LIST = ["fr", "en"]

FILE_ACTION_TXT = {
    1: "Simulation du déplacement de {} vers {}",
    2: "Copie du fichier {} vers {}",
    3: "Déplacement du fichier {} vers {}",
}

FILE_SIMULATE = 1
FILE_COPY = 2
FILE_MOVE = 3

GUI_SIMPLIFIED = 1
GUI_NORMAL = 2
GUI_ADVANCED = 3

DUP_MD5_FILE = 1
DUP_MD5_DATA = 2
DUP_DATETIME = 3

DIR_EXCLUDE = 0
DIR_INCLUDE = 1

GROUP_PLACEHOLDER = r"{group}"
DEFAULT_DATE_STR = "1900:01:01 00:00:00"

STRING = (
    "rel_dir",
    "filename",
    "display_fmt",
    "guess_fmt",
    "size",
    "lang",
    "exif_user_tags",
    "non_def",
)
PATH = ("src_dir", "dir", "dir", "scan_dir")
INTEGER = (
    "exclude_toggle",
    "action_mode",
    "mode",
    "floating_nb",
    "wait",
    "mode",
    "max_hash_size",
    "min_size",
    "max_size",
)
BOOLEAN = (
    "is_recursive",
    "is_md5_file",
    "is_md5_data",
    "is_meta",
    "is_use_cached_datas",
    "is_recursive",
    "is_exclude_dir_regex",
    "is_control",
    "is_scan_dest",
    "is_delete_metadatas",
    "is_date_from_filesystem",
    "is_force_date_from_filesystem",
    "is_group",
    "is_guess",
    "is_gps",
    "debug",
    "simulate",
    "verbose",
    "unidecode",
    "is_max_hash_size",
    "is_min_size",
    "is_max_size",
)
LISTE = ("extentions", "cameras", "excluded_dirs", "accepted_formats")
FLOAT = ("accuracy",)


def repr2value(k, v):  # for python
    a = k
    k = k.split(".")[-1]
    if k in STRING:
        pass
    elif k in PATH:
        v = Path(v)
    elif k in BOOLEAN:
        v = int(v)
    elif k in LISTE:
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
    elif k in LISTE:
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
    elif k in LISTE:
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


CONFIG = ConfigDict()
