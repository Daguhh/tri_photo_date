import os
import sys
from pathlib import Path
from configparser import ConfigParser
import logging

#try:
#    from .config_paths import CONFIG_DIR, APP_NAME
#except ModuleNotFoundError:
from tri_photo_date.utils.config_paths import CONFIG_DIR, APP_NAME

CONFIG_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_CONFIG = """
[DEFAULT]
# Source
out_dir =
extentions = jpg,png,jpeg
cameras =
is_recursive = 1

is_guess_date_from_name = 0
guess_date_from_name =

is_group_floating_days = 0
group_floating_days_nb = 0
group_floating_days_fmt =

# Destination
in_dir =
out_path_str = %Y/%Y-%m
filename = fichier

# Options
file_action = 0
control_hash = 2
hash_populate = 2
hash_reset = 2
gps = 0
verbose = 0

# GPS
gps_debug = 0
gps_simulate = 0
gps_accuracy = 2
gps_wait = 5

# GUI
gui_size = 1
gui_mode = 0
lang = fr

exif_user_tags =
unidecode = 0
non_def = non_def

# accepted_formats
accepted_formats = jpg, jpeg, png, webp, bmp, ico, tiff, heif, heic, svg, raw, arw, cr2, nrw, k25, apng, avif, gif, svg, webm, mkv, flv, ogg, gif, avi, mov, asf, mp4, m4v, mpg, mp2, mpeg, mpv, 3gp, 3g2, flv
"""

LANG_LIST = ['fr', 'en']

FILE_SIMULATE = 0
FILE_COPY = 1
FILE_MOVE = 2

GUI_SIMPLIFIED = 0
GUI_NORMAL = 1
GUI_ADVANCED = 2

STRING = ("non_def", "filename", "out_path_str", "exif_user_tags",'gui_size','guess_date_from_name','lang','group_floating_days_fmt')
PATH = ("in_dir", "out_dir")
INTEGER = ("gps_wait", "gui_mode", "file_action", "group_floating_days_nb")
BOOLEAN = (
    "gps",
    "control_hash",
    "hash_populate",
    "hash_reset",
    "gps_debug",
    "gps_simulate",
    "unidecode",
    "is_guess_date_from_name",
    "verbose",
    "is_recursive",
    "is_group_floating_days",
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


class ConfigDict(dict):
    def __init__(self):
        super(ConfigDict, self).__init__()

        self.configfile = CONFIG_DIR / "config.ini"

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
