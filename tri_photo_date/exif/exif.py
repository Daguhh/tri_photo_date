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
    repl= {
        "%Y": r"\d{4}",
        "%m": r"\d{2}",
        "%d": r"\d{2}",
        "%H": r"\d{2}",
        "%M": r"\d{2}",
        "%S": r"\d{2}",
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
            print(f'Erro with file at {im_path}')
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

    def add_localisation(self, address_dct):

        self.im.modify_iptc(address_dct)

    @staticmethod
    def format_tag(out_fmt, placeholder, value=''):
        # import ipdb; ipdb.set_trace()
        #out_fmt = out_fmt.replace(tag_key, tag_value)
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

        date_str = ''

        # format as in Exifs
        out_fmt = "%Y:%m:%d %H:%M:%S"

        pattern = strftime_to_regex(date_fmt)
        match = re.search(pattern, in_str)

        if match:
            date_str = match.group(0)
            date = datetime.strptime(date_str, date_fmt).date()
            date_str = date.strftime(out_fmt)

        return date_str

