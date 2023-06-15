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
from tri_photo_date.utils.config_paths import CONFIG_PATH, APP_NAME

DEFAULT_CONFIG = """
[FILES]
# Partially hashs files given the maximum size in Mo
files_is_max_hash_size = 0
files_max_hash_size = 0

# Only find files between min and max in Mo
files_is_min_size = 0
files_min_size = 0
files_is_max_size = 0
files_max_size = 5000

[SCAN]
scan_src_dir =
scan_dest_dir =
scan_is_recursive = 0
scan_is_md5_file = 0
scan_is_md5_data = 0
scan_is_meta = 0
scan_is_use_cached_datas = 0

[SOURCE]
src_dir =
src_extentions = jpg,png,jpeg
src_cameras =
src_is_recursive = 2
src_excluded_dirs =
src_is_exclude_dir_regex = 2
src_exclude_toggle = 0

[DESTINATION] =
dest_dir =
dest_rel_dir =
dest_filename =

[ACTION]
action_mode = 1

[DUPLICATES]
dup_is_control = 2
dup_mode = 1
dup_is_scan_dest = 2

[OPTIONS.GENERAL]
opt_is_delete_metadatas = 0
opt_is_date_from_filesystem = 0

[OPTIONS.GROUP]
grp_is_group = 0
grp_floating_nb = 1
grp_display_fmt =

[OPTIONS.NAME]
name_is_guess = 0
name_guess_fmt =

[OPTIONS.GPS]
gps_is_gps = 0
gps_debug = 0
gps_simulate = 0
gps_accuracy = 2
gps_wait = 5

[INTERFACE]
gui_size = 1
gui_mode = 3
gui_lang = en

[MISC]
verbose = 0
exif_user_tags =
unidecode = 0
non_def = non_def
accepted_formats = jpg, jpeg, png, webp, bmp, ico, tiff, heif, heic, svg, raw, arw, cr2, nrw, k25, apng, avif, gif, svg, webm, mkv, flv, ogg, gif, avi, mov, asf, mp4, m4v, mpg, mp2, mpeg, mpv, 3gp, 3g2, flv
"""


cli_mode, config_path = cli_arguments()

if cli_mode == CLI_DUMP:
    shutil.copy(CONFIG_PATH, config_path)
    sys.exit(0)

if cli_mode == CLI_DUMP_DEFAULT:
    with open(str(config_path), "w") as f:
        f.write(DEFAULT_CONFIG)
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

STRING = (
    "dest_rel_dir",
    "dest_filename",
    "grp_display_fmt",
    "name_guess_fmt",
    "gui_size",
    "gui_lang",
    "exif_user_tags",
    "non_def",
)
PATH = ("src_src_dir", "scan_dest_dir", "dest_dir", "scan_dir")
INTEGER = (
    "src_exclude_toggle",
    "action_mode",
    "dup_mode",
    "grp_floating_nb",
    "gps_wait",
    "gui_mode",
    "files_max_hash_size",
    "files_min_size",
    "files_max_size",
)
BOOLEAN = (
    "scan_is_recursive",
    "scan_is_md5_file",
    "scan_is_md5_data",
    "scan_is_meta",
    "scan_is_use_cached_datas",
    "src_is_recursive",
    "src_is_exclude_dir_regex",
    "dup_is_control",
    "dup_is_scan_dest",
    "opt_is_delete_metadatas",
    "opt_is_date_from_filesystem",
    "grp_is_group",
    "name_is_guess",
    "gps_is_gps",
    "gps_debug",
    "gps_simulate",
    "verbose",
    "unidecode",
    "files_is_max_hash_size",
    "files_is_min_size",
    "files_is_max_size",
)
LISTE = ("src_extentions", "src_cameras", "src_excluded_dirs", "accepted_formats")
FLOAT = ("gps_accuracy",)


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

        if config_path is not None:
            self.configfile = Path(config_path)
            if not self.configfile.exists():
                raise NoConfigFileError
        else:
            self.configfile = CONFIG_PATH

        if not self.configfile.exists():
            logging.info("No configfile found, generationg one")
            self.generate_config()

        else:
            logging.info(f"config is here : {self.configfile}")

        # self.configfile = Path(__file__).parent.resolve() / "config.ini"
        self.load_config()

    def generate_config(self):
        logging.info(f"Creating config at {self.configfile}")
        with open(self.configfile, "w") as f:
            f.write(DEFAULT_CONFIG)

    def __getitem__(self, k):
        if isinstance(k, tuple):
            k = ".".join(k)

        if k not in self.keys():
            logging.info(f"No entry for '{k}' in config")
            logging.info("Regenerating config file...")
            self.generate_config()
            self.load_config()

        return super().__getitem__(k)

    def __setitem__(self, k, v):
        print('set :',k,v)
        if isinstance(k, tuple):
            k = ".".join(k)
        # k = ','.join(x.lower() for x in k)
        # self.repr_dct[k] = v
        k, v = repr2value(k, v)

        super().__setitem__(k, v)

    def load_config(self):
        # cfg = self.config['DEFAULT']
        self.config = ConfigParser(interpolation=None)
        self.config.read(self.configfile)

        # self.repr_dct = {}

        for section in self.config.sections():
            items = self.config.items(section)
            for key, value in items:
                self[".".join((section.lower(), key))] = value
        # for k, v in self.config.read_dict():
        # self[k] = v

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
