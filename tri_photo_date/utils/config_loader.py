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
# TriPhotoDate configuration file
#
# /!\ boolean use PyQt5 "notation":
#     - 2 : True
#     - 0 : False
#

[FILES]
# Partially hashs files given the maximum size in Mo
is_max_hash_size = 0
max_hash_size = 0

# Only find files between min and max in Mo
is_min_size = 0
min_size = 0
is_max_size = 0
max_size = 5000

[SCAN]
# Keep empty at this time (overided by source.dir and destination.dir)
src_dir =
dest_dir =

# Useless at this time
is_recursive = 0
is_md5_file = 0
is_md5_data = 0
is_meta = 0

# Directly load from cache if path already exist : doesn't verify if file is the same
is_use_cached_datas = 0

[SOURCE]
# absolute directory of files to process
dir =

# filter file by extentions, extentions separated by commas
extentions = jpg,png,jpeg

# filter by cameras, cameras models deparated by commas (check Exif.ImageModel to find a camera name)
cameras =

# process also <dir> subdirectories
is_recursive = 2

# filter by excluding or including folder or using regex
# relative folder to <dir> or regex, use commas to separate elments in case of multiples values
excluded_dirs =
# activate regex mode
is_exclude_dir_regex = 2
# toggle exclude (0) / include (1)
exclude_toggle = 0

[DESTINATION] =
# Absolute directory where to move/copy photos
dir =
# relative directory to <dir>. This path can be personalized using metadata ro date placeholders
rel_dir =
# file name, follow same format as <rel_dir>, keep empty to keep original filename
filename =

[ACTION]
# action to perform when processing files : simulate (1) / copy (2) / move (3)
action_mode = 1

[DUPLICATES]
# Activate control of duplicates. Only one file in match will be processed
is_control = 2
# Matching mode : md6 file (1) / md5 data (2) / datetime (3)
mode = 1
# Look for match in destination directory too
is_scan_dest = 2

[OPTIONS.GENERAL]
# remove metadata of copied/moved files
is_delete_metadatas = 0
# try to get date from filesystem if no other methods works
is_date_from_filesystem = 0
# Force to take date from filesystem
is_force_date_from_filesystem = 0

[OPTIONS.GROUP]
# Activate grouping photo by day floating
is_group = 0
# floating window size in days
floating_nb = 1
# A placeholder for {group} can be set in customizable paths, it will use this format (use strftime formats)
display_fmt =

[OPTIONS.NAME]
# Try to get date from file name
is_guess = 0
# Format of the date to strip
guess_fmt =

[OPTIONS.GPS]
# Activate location resolution using gps metadatas
is_gps = 0

# Not working yet
debug = 0

# set a fake address
simulate = 0

# gps accuracy in km. If distance between 2 photo in less than accuracy, cached data will be used, avoiding unnecessary call to api
accuracy = 2

# Time between 2 api calls. Prevent api overload
wait = 5

[INTERFACE]
# Gui scale factor
size = 1
# Adjust shown options number and how user interact with the interface : simplified (1) / advanced (3)
mode = 3
# Set interface language en / fr
lang = en

[MISC]
# Not working yet
verbose = 0

# Not implemented yet
exif_user_tags =

# Obolete
unidecode = 0

# Default word if no datas found to fill placeholder
non_def = non_def

# Filter extentions when scanning
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
