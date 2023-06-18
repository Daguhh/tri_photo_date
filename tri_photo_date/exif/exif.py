#!/usr/bin/env python3

import re
from datetime import datetime
import warnings
import locale
import sys
import logging
import traceback

import pyexiv2


class NoExifError(Exception):
    def __init__(self, message, error_code):
        super().__init__(message)
        self.error_code = error_code


def strftime_to_regex(fmt):
    repl = {
        "%a": r"\w{3}",
        "%A": r"\w{3,} ",
        "%w": r"\d",
        "%d": r"[0123]\d",
        "%-d": r"[123]{0,1}\d",
        "%b": r"\w{3}",
        "%B": r"\w{3,}",
        "%m": r"[0123]\d",
        "%-m": r"[0123]{0,1}\d",
        "%y": r"\d{2}",
        "%Y": r"\d{4}",
        "%H": r"[012]\d",
        "%-H": r"[012]{0,1}\d",
        "%I": r"[012]\d",
        "%-I": r"[012]{0,1}\d",
        "%p": r"\w+",
        "%M": r"[012345]\d",
        "%-M": r"[012345]{0,1}\d",
        "%S": r"[012345]\d",
        "%-S": r"[012345]{0,1}\d",
        "%f": r"\d{6}",
        "%z": r"[+-]\d{4}(\d{2}(\.\d{6}){0,1}){0,1}",
        "%Z": r"\w* ",
        "%j": r"[0123]\d{2}",
        "%-j": r"[0123]{0,1}\d{2}",
        "%U": r"\d{2}",
        "%-U": r"\d{1,2}",
        "%W": r"\d{2]",
        "%-W": r"\d{1,2}",
    }

    pattern = re.sub(r"%[a-zA-Z]", lambda x: repl[x.group()], fmt)
    return pattern


class ExifTags(dict):
    def __init__(self, im_path):
        super().__init__()

        try:
            encoding = locale.getpreferredencoding()
            self.im = pyexiv2.Image(str(im_path), encoding=encoding)
            exifs = self.im.read_exif()
            exifs.update(self.im.read_iptc())
            exifs.update(self.im.read_xmp())
        except UnicodeDecodeError:
            print(f"Erro with file at {im_path}")
            raise NoExifError("Unicode error", 1)
        except Exception as e:
            print(e)
            traceback.print_exc()
            raise NoExifError("other_error", 2)

        self.update(exifs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.im.close()

    def _clear_all_metadatas(self):
        self.im.clear_exif()
        self.im.clear_iptc()
        self.im.clear_xmp()
        self.im.clear_comment()
        self.im.clear_icc()
        self.im.clear_thumbnail()

    @staticmethod
    def clear_all_metadatas(out_str):
        with ExifTags(out_str) as im_exif:
            im_exif._clear_all_metadatas()

    def _add_location_to_iptc(self, address_dct):
        self.im.modify_iptc(address_dct)

    @staticmethod
    def add_location_to_iptc(im_str, address_dct):
        with ExifTags(out_str) as im_exif:
            try:
                im_exif._add_location_to_iptc(location)
            except NoExifError as e:
                print("Issue while loading gps, skipping", e)

    @staticmethod
    def format_tag(out_fmt, placeholder, value=""):
        # import ipdb; ipdb.set_trace()
        # out_fmt = out_fmt.replace(tag_key, tag_value)
        if not value:
            value = "non_def"

        placeholder = f"[<{{]{placeholder}[}}>]"
        out_fmt = re.sub(placeholder, value, out_fmt)
        return out_fmt

    @staticmethod
    def format_ym(date_str, out_fmt):
        in_fmt = "%Y:%m:%d %H:%M:%S"
        # out_fmt = '%Y-%m-%d'

        try:
            dt_obj = datetime.strptime(date_str, in_fmt)
        except ValueError:
            dt_obj = datetime.strptime("1900:01:01 00:00:00", in_fmt)

        out_fmt = datetime.strftime(dt_obj, out_fmt)

        return out_fmt

    @staticmethod
    def get_date_from_name(date_fmt, in_str):
        date_str = ""

        # format as in Exifs
        out_fmt = "%Y:%m:%d %H:%M:%S"

        pattern = strftime_to_regex(date_fmt)
        match = re.search(pattern, in_str)

        if match:
            date_str = match.group(0)
            try:
                date = datetime.strptime(date_str, date_fmt).date()
            except ValueError as e:
                # logging.WARNING("Wrong format for parsing date from filename :", in_str)
                return ""
            date_str = date.strftime(out_fmt)

        return date_str
