#!/usr/bin/env python3

import sys
from datetime import datetime
import json
import sqlite3
from functools import wraps
import time
import logging

##### Prevent outdated ssl certificate error on some systems
import certifi  # Prevent error on system with outdated ssl certificates
import ssl  # Prevent error on system with outdated ssl certificates

ctx = ssl.create_default_context(cafile=certifi.where())
import geopy.geocoders

geopy.geocoders.options.default_ssl_context = ctx

from geopy.geocoders import Nominatim
from geopy.distance import distance as GEODistance

from tri_photo_date.exif import ExifTags, EXIF_LOCATION_FIELD, EXIF_GPS_FIELD
from tri_photo_date.utils.config_paths import GPS_DATABASE_PATH
from tri_photo_date.gps.gps_constants import LOCATION_TYPES

# except ImportError:
#     from tri_photo_date.exif import ExifTags, EXIF_LOCATION_FIELD, EXIF_GPS_FIELD
#     from tri_photo_date.utils.config_loader import CONFIG_DIR, CONFIG
#     from tri_photo_date.gps.gps_constants import LOCATION_TYPES


def set_global_config(CONFIG):
    global IS_DEBUG
    IS_DEBUG = CONFIG["options.gps.debug"]  # False

    global GPS_SIMULATE
    GPS_SIMULATE = CONFIG["options.gps.simulate"]  # False

    global GPS_ACCURACY
    GPS_ACCURACY = CONFIG["options.gps.accuracy"]  # 2 km

    global GPS_WAIT
    GPS_WAIT = CONFIG["options.gps.wait"]  # in seconds


# SQLITE_CACHE_PATH = CONFIG_DIR / "gps_cache.db"

# try:
#    from .gps_returns_examples import SaintEtienne, SaintRemi, London
# except ModuleNotFoundError:
#    from gps_returns_examples import SaintEtienne, SaintRemi, London


def DEBUG(func):
    def wrapper(*args, **kwargs):
        if IS_DEBUG:
            print(f"Calling function {func.__name__}")
        result = func(*args, **kwargs)
        if IS_DEBUG:
            print(f"Function {func.__name__} returned {result}")
        return result

    return wrapper


@DEBUG
def get_image_gps_location(im_exif: dict) -> dict:
    # Look for existing location datas
    try:
        # tags = im.read_iptc()
        if any(loc in im_exif for loc in EXIF_LOCATION_FIELD.values()):
            logging.info("Photo already has location metadatas")
            address_tags = {k: im_exif.get(k, "") for k in EXIF_LOCATION_FIELD.values()}
            return address_tags

        # Get location datas
        # tags = im.read_exif()

        lat_lon = getGPS(im_exif)
        if lat_lon is None:
            return
        address = gps2address(*lat_lon)
        address_tags = address2tag(address)
    except NoGpsDataError:
        return None

    # im.modify_iptc(address_tags)
    return address_tags


@DEBUG
def add_tags_to_image(im_path):
    address_tags = []
    try:
        with ExifTags(im_path) as im_exifs:
            address_tags = get_image_gps_location(im_exifs)
            if address_tags is not None:
                im_exifs.add_localisation(address_tags)

    except RuntimeError as e:
        logging.info(f"can't open {im_path}, skipping...")
    except NoGpsDataError:
        logging.info("No GPS data, skipping...")

    return address_tags


@DEBUG
def add_tags_to_image_in_folder(fd_path):
    pass


# barrowed from
# https://gist.github.com/snakeye/fdc372dbf11370fe29eb
@DEBUG
def _convert_to_degress(value):
    """
    Helper function to convert the GPS coordinates stored in the EXIF to degress in float format
    :param value:
    :type value: exifread.utils.Ratio
    :rtype: float
    """
    d = float(value.values[0].num) / float(value.values[0].den)
    m = float(value.values[1].num) / float(value.values[1].den)
    s = float(value.values[2].num) / float(value.values[2].den)

    return d + (m / 60.0) + (s / 3600.0)


@DEBUG
def frac2int(frac: str) -> int:
    try:
        num, den = [int(x) for x in frac.split("/")]
        return num / den
    except ZeroDivisionError as e:
        raise NoGpsDataError("Invalid GPS data : ", frac)


@DEBUG
def exifgps2degree(exif_value):
    degs, mins, secs = (frac2int(x) for x in (exif_value.split(" ")))
    degrees = sum(x / 60**i for i, x in enumerate((degs, mins, secs)))
    return degrees


class NoGpsDataError(Exception):
    def __init__(self, message="", data=None):
        super().__init__(message)
        self.data = data

    def __str__(self):
        return f"{self.__class__.__name__}: {self.args[0]} {self.data}"


@DEBUG
def getGPS(tags):
    try:
        latitude_ref = tags[EXIF_GPS_FIELD["latitude_ref"]]
        latitude = tags[EXIF_GPS_FIELD["latitude"]]
        longitude_ref = tags[EXIF_GPS_FIELD["longitude_ref"]]
        longitude = tags[EXIF_GPS_FIELD["longitude"]]
    except KeyError as e:
        raise NoGpsDataError

    if latitude:
        lat_value = exifgps2degree(latitude)
        if latitude_ref != "N":
            lat_value = -lat_value
    else:
        return

    if longitude:
        lon_value = exifgps2degree(longitude)
        if longitude_ref != "E":
            lon_value = -lon_value
    else:
        return

    return lat_value, lon_value


def cache_gps_data(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        lat, lon = args

        # Load / Create
        cache = sqlite3.connect(GPS_DATABASE_PATH)
        cur = cache.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS cache (lat REAL, lon REAL, result TEXT)"
        )

        # Compute distances between new location and ones in cache
        cur.execute("SELECT lat, lon FROM cache")
        coordinates = cur.fetchall()
        distances = [GEODistance(coor, (lat, lon)).km for coor in coordinates]
        closest_dist = 100

        if distances:
            logging.info("loading data from gps cache")
            closest_ind = distances.index(min(distances))
            closest_dist = distances[closest_ind]
            closest_pt = coordinates[closest_ind]

            if closest_dist < GPS_ACCURACY:
                lat, lon = closest_pt
                cur.execute(
                    "SELECT result FROM cache WHERE lat=? AND lon=?", (lat, lon)
                )
                res = cur.fetchone()
                return json.loads(res[0])

        logging.info("Run function")
        result = func(*args, **kwargs)
        cur.execute(
            "INSERT INTO cache VALUES (?, ?, ?)", (lat, lon, json.dumps(result))
        )
        cache.commit()
        return result

    return wrapper


@DEBUG
@cache_gps_data
def gps2address(lat, lon):
    if not lat or not lon:
        return {}

    user_agent = "tri_photo_date"
    if not GPS_SIMULATE:
        geolocator = Nominatim(user_agent=user_agent)

        lat_lon_str = "{}, {}".format(lat, lon)
        location = geolocator.reverse(lat_lon_str)
        dct = location.raw
        logging.info("Ask OpenStreetMap server")
        time.sleep(GPS_WAIT)
    else:
        logging.info("Simulate gps")
        from .gps_results import example1

        dct = example1

    return dct


class LocationDict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def __getitem__(self, asked_tag):
        tag = ""
        for real_tag in LOCATION_TYPES[asked_tag]:
            if real_tag in self.keys():
                tag = real_tag
                break

        if not tag:
            return ""

        return super().__getitem__(tag)


@DEBUG
def address2tag(address_dct):
    fd = address_dct["display_name"]
    d = LocationDict(address_dct["address"])

    tags = {}

    tags[EXIF_LOCATION_FIELD["city"]] = d["city"]
    tags[EXIF_LOCATION_FIELD["road"]] = d["road"]
    tags[EXIF_LOCATION_FIELD["region"]] = d["region"]
    tags[EXIF_LOCATION_FIELD["country_code"]] = d["country_code"]
    tags[EXIF_LOCATION_FIELD["country"]] = d["country"]
    tags[EXIF_LOCATION_FIELD["display_name"]] = fd

    return tags


if __name__ == "__main__":
    pass
    # f_path = sys.argv[1]
    # add_tags_to_image(f_path)
