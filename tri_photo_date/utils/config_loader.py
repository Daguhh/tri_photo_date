import os
import sys
import shutil
from pathlib import Path
from configparser import ConfigParser
import logging

#try:
#    from .config_paths import CONFIG_DIR, APP_NAME
#except ModuleNotFoundError:
from tri_photo_date.cli.cli_argparser import cli_arguments,CLI_DUMP,CLI_DUMP_DEFAULT,CLI_LOAD
from tri_photo_date.utils.config_paths import CONFIG_PATH, APP_NAME

DEFAULT_CONFIG = """
[DEFAULT]
# Source
out_dir =
extentions = jpg,png,jpeg
cameras =
is_recursive = 2
excluded_dirs =
is_exclude_dir_regex = 2
exclude_toggle = 0

# parse date from file name
is_guess_date_from_name = 0
guess_date_from_name =
is_date_from_filesystem = 0

# group files by floating window over days
is_group_floating_days = 0
group_floating_days_nb = 1
group_floating_days_fmt =

# Destination
in_dir =
out_path_str = %Y/%Y-%m
filename = fichier

# Options
# FILE_SIMULATE = 1, FILE_COPY = 2, FILE_MOVE = 3
file_action = 1
gps = 0
verbose = 0
is_delete_metadatas = 0

# Duplicates options
is_control_duplicates = 2
# DUP_MD5_FILE = 1, DUP_MD5_DATA = 2, DUP_DATETIME = 3
dup_mode = 1
dup_is_scan_dest = 2

# GPS
gps_debug = 0
gps_simulate = 0
gps_accuracy = 2
gps_wait = 5

# GUI
gui_size = 1
gui_mode = 3
gui_lang = en

# Misc
exif_user_tags =
unidecode = 0
non_def = non_def

# accepted_formats
accepted_formats = jpg, jpeg, png, webp, bmp, ico, tiff, heif, heic, svg, raw, arw, cr2, nrw, k25, apng, avif, gif, svg, webm, mkv, flv, ogg, gif, avi, mov, asf, mp4, m4v, mpg, mp2, mpeg, mpv, 3gp, 3g2, flv
"""

cli_mode, config_path = cli_arguments()

if cli_mode == CLI_DUMP:
    shutil.copy(CONFIG_PATH, config_path)
    sys.exit(0)

if cli_mode == CLI_DUMP_DEFAULT:
    with open(str(config_path), 'w') as f:
        f.write(DEFAULT_CONFIG)
    sys.exit(0)

if cli_mode == CLI_LOAD:
    CONFIG_PATH = config_path


CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)


LANG_LIST = ['fr', 'en']

FILE_ACTION_TXT = {
    1 : "Simulation du déplacement de {} vers {}",
    2 : "Copie du fichier {} vers {}",
    3 : "Déplacement du fichier {} vers {}"
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

STRING = ("non_def", "filename", "out_path_str", "exif_user_tags",'gui_size','guess_date_from_name','gui_lang','group_floating_days_fmt','excluded_dirs')
PATH = ("in_dir", "out_dir")
INTEGER = ("gps_wait", "gui_mode", "file_action", "group_floating_days_nb", 'dup_mode', 'exclude_toggle')
BOOLEAN = (
    "gps",
    "gps_debug",
    "gps_simulate",
    "unidecode",
    "is_guess_date_from_name",
    "verbose",
    "is_recursive",
    "is_group_floating_days",
    "is_control_duplicates",
    "dup_is_scan_dest",
    "is_date_from_filesystem",
    "is_exclude_dir_regex",
    "is_delete_metadatas",
)
LISTE = ("extentions",'cameras','accepted_formats')
FLOAT = ("gps_accuracy",)

def repr2value(k,v):
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

    return k, v

class NoConfigFileError(Exception):

    def __str__(self):
        print(
            'There is no configuration file for path you gave',
            "Please run 'tri_photo_date --cli --dump <path>' to start from actual configuration"
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
        if k not in self.keys():
            logging.info(f"No entry for '{k}' in config")
            logging.info("Regenerating config file...")
            self.generate_config()
            self.load_config()

        return super().__getitem__(k)

    def __setitem__(self, k, v):
        self.repr_dct[k] = v
        k, v = repr2value(k,v)
        super().__setitem__(k, v)

    def load_config(self):
        # cfg = self.config['DEFAULT']
        self.config = ConfigParser(interpolation=None)
        self.config.read(self.configfile)

        self.repr_dct = {}

        for k, v in self.config["DEFAULT"].items():
            self[k] = v

    def save_config(self):
        self.config["DEFAULT"] = self.repr_dct

        with open(self.configfile, "w") as f:
            self.config.write(f)

    def get_repr(self, k):
        if k not in self.config['DEFAULT']:
            logging.info(f"No entry for '{k}' in config")
            logging.info("Regenerating config file...")
            self.generate_config()
            self.load_config()

        return self.config["DEFAULT"][k]

CONFIG = ConfigDict()
