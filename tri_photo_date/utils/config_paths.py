import sys
import os
from pathlib import Path
import logging
import tri_photo_date

APP_NAME = "tri_photo_date"

#### Resource : in function of packaging ####
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    logging.info("running in a PyInstaller bundle")
    RUNTIME_PATH = Path(sys._MEIPASS)
    ICON_PATH = RUNTIME_PATH / "icon.ico"
    README_PATH = RUNTIME_PATH / "README.md"
    HELP_PATH = RUNTIME_PATH / "resources" / "{}" / "help.md"
    LICENSE_PATH = RUNTIME_PATH / "LICENSE"
    AKNOLEG_PATH = RUNTIME_PATH / "resources" / "{}" / "acknowledgments.md"
    ABOUT_PATH = RUNTIME_PATH / "resources" / "{}" / "about.md"
    STRFTIME_HELP_PATH = RUNTIME_PATH / "strftime_help.html"
    LOCALES_DIR = RUNTIME_PATH / "locales"
    DEFAULT_CONFIG_PATH = RUNTIME_PATH / "config" / "default_config.ini"

elif "site-packages" in os.path.abspath(tri_photo_date.__file__):
    logging.info("running in a normal Python process")
    RUNTIME_PATH = Path(os.path.abspath(tri_photo_date.__file__))
    ICON_PATH = RUNTIME_PATH.parent.parent / "resources" / "icon.ico"
    README_PATH = RUNTIME_PATH.parent.parent / "README.md"
    HELP_PATH = RUNTIME_PATH.parent.parent / "resources" / "{}" / "help.md"
    LICENSE_PATH = RUNTIME_PATH.parent.parent / "LICENSE"
    AKNOLEG_PATH = (
        RUNTIME_PATH.parent.parent / "resources" / "{}" / "acknowledgments.md"
    )
    ABOUT_PATH = RUNTIME_PATH.parent.parent / "resources" / "{}" / "about.md"
    STRFTIME_HELP_PATH = RUNTIME_PATH.parent.parent / "resources" / "strftime_help.html"
    LOCALES_DIR = RUNTIME_PATH.parent / "locales"
    DEFAULT_CONFIG_PATH = RUNTIME_PATH.parent.parent / "config" / "default_config.ini"

else:
    logging.info("The package is running as source code")
    RUNTIME_PATH = Path(os.path.abspath(tri_photo_date.__file__))
    ICON_PATH = RUNTIME_PATH.parent.parent / "resources" / "icon.ico"
    README_PATH = RUNTIME_PATH.parent.parent / "README.md"
    HELP_PATH = RUNTIME_PATH.parent.parent / "resources" / "{}" / "help.md"
    LICENSE_PATH = RUNTIME_PATH.parent.parent / "LICENSE"
    AKNOLEG_PATH = (
        RUNTIME_PATH.parent.parent / "resources" / "{}" / "acknowledgments.md"
    )
    ABOUT_PATH = RUNTIME_PATH.parent.parent / "resources" / "{}" / "about.md"
    STRFTIME_HELP_PATH = RUNTIME_PATH.parent.parent / "resources" / "strftime_help.html"
    LOCALES_DIR = RUNTIME_PATH.parent / "locales"
    DEFAULT_CONFIG_PATH = RUNTIME_PATH.parent.parent / "config"  / "default_config.ini"


#### CONFIG ####
if os.name == "nt":
    CONFIG_DIR = Path(os.environ["APPDATA"]) / APP_NAME
else:
    CONFIG_DIR = Path.home() / ".config" / APP_NAME

CONFIG_DIR = CONFIG_DIR.resolve()
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

CONFIG_PATH = CONFIG_DIR / "config.ini"


#### CACHE ####
if os.name == "nt":
    CACHE_DIR = Path(os.environ["LOCALAPPDATA"]) / APP_NAME
else:
    CACHE_DIR = Path.home() / ".cache" / APP_NAME

CACHE_DIR = CACHE_DIR.resolve()
CACHE_DIR.mkdir(parents=True, exist_ok=True)

IMAGE_DATABASE_PATH = CACHE_DIR / "images.db"
GPS_DATABASE_PATH = CACHE_DIR / "nominatim.db"
# IMAGE_DATABASE_PATH = IMAGE_DATABASE_PATH.resolve()
