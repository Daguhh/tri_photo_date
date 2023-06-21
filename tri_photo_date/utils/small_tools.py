import re
from pathlib import Path
from datetime import datetime, timezone
import sys
import time
import shutil

from tri_photo_date.exif import (
    ExifTags,
    EXIF_DATE_FIELD,
)

from tri_photo_date.utils.constants import (
    FILE_SIMULATE,
    FILE_COPY,
    FILE_MOVE,
    DEFAULT_DATE_STR,
)

from tri_photo_date.config.config_loader import LANG_LIST

class fake_LoopCallBack:
    stopped = False

    def __init__(self):
        pass

    @classmethod
    def run(cls):
        return False


class Timer:
    old_time = None
    on = True

    @classmethod
    def tic(cls):
        cls.old_time = time.time()

    @classmethod
    def toc(cls):
        if cls.on:
            toc = time.time() - cls.old_time
            # sys.stdout.flush()
            sys.stdout.write("{:40}".format("█" * int(1000 * toc)) + "\r")
            cls.tic()

    @classmethod
    def on(cls):
        cls.on = True

    @classmethod
    def off(cls):
        cls.on = False


Timer.off()

# https://stackoverflow.com/questions/13343700/bytes-to-human-readable-and-back-without-data-loss
def bytes2human(n, format="%(value)i%(symbol)s"):
    """
    >>> bytes2human(10000)
    '9K'
    >>> bytes2human(100001221)
    '95M'
    """
    symbols = ("B", "K", "M", "G", "T", "P", "E", "Z", "Y")
    prefix = {}
    for i, s in enumerate(symbols[1:]):
        prefix[s] = 1 << (i + 1) * 10
    for symbol in reversed(symbols[1:]):
        if n >= prefix[symbol]:
            value = float(n) / prefix[symbol]
            return format % locals()
    return format % dict(symbol=symbols[0], value=n)


def limited_string(s, limit=43, prefix=20, suffix=20):
    if len(s) > limit:
        return s[:prefix] + "..." + s[-suffix:]
    else:
        return s

def gen_regex_index(filename):
    # get x from 'filename (x).ext'

    path = Path(filename)
    reg = re.compile(path.stem + r"(?:\s\(([0-9]+))\)?" + path.suffix.lower())

    def get_ind(s):
        match = reg.fullmatch(s)
        if match is not None:
            return int(match.group(1))
        else:
            return 0

    return get_ind


def rename_with_incr(db, out_str):
    # Could be heavy load when lot of files with same name in same folder
    # Move and rename with increment if needed
    out_path = Path(out_str)
    directory = out_path.parent
    stem = out_path.stem
    ext = out_path.suffix.lower()
    filename = stem + ext

    count = 1
    collidable_files = db.exist_in_preview(out_path)

    get_ind = gen_regex_index(filename)
    indexes = [get_ind(s) for s in collidable_files]

    if indexes:  # duplicates found
        m = max(indexes) + 1
        filename = f"{stem} ({m}){ext}"

    return str(directory / filename)

def get_lang(lang):

    if lang == "locale":
        import locale
        lang = locale.getlocale()[0].split('_')[0]
        if not lang in LANG_LIST:
            lang = 'en'
    return lang

def move_file(in_str, out_str, mode=FILE_SIMULATE):
    in_path = Path(in_str)
    out_path = Path(out_str)

    if not out_path.parent.exists():
        Path.mkdir(out_path.parent, parents=True, exist_ok=True)

    if mode == FILE_SIMULATE:
        return False
    elif mode == FILE_COPY:
        shutil.copyfile(in_path, out_path)
    elif mode == FILE_MOVE:
        shutil.move(in_path, out_path)

    return True


def create_out_str(in_str, out_path_str, out_filename):
    in_path = Path(in_str)

    if out_filename:
        out_name = out_filename + in_path.suffix
    else:
        out_name = in_path.name

    out_str = str(Path(out_path_str) / out_name)

    return out_str


def get_date_from_file_system(in_str):
    timestamp = Path(in_str).stat().st_mtime
    date = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    out_fmt = "%Y:%m:%d %H:%M:%S"
    date_str = date.strftime(out_fmt)

    return date_str


def get_date_from_exifs_or_file(
    in_str,
    metadatas,
    is_guess,
    guess_fmt,
    is_date_from_filesystem,
    is_force_date_from_filesystem,
):
    date_str = ""

    # First start looking at file name (user option)
    if is_guess:
        date_fmt = guess_fmt
        date_str = ExifTags.get_date_from_name(date_fmt, in_str)

    is_force_date_filesystem = bool(is_date_from_filesystem) and bool(
        is_force_date_from_filesystem
    )
    if not date_str and is_force_date_filesystem:
        date_str = get_date_from_file_system(in_str)

    # Try in metadatas
    if not date_str:
        for date_tag in EXIF_DATE_FIELD.values():
            if date_tag in metadatas:
                date_str = metadatas[date_tag]
                break

    if not date_str and is_date_from_filesystem:
        date_str = get_date_from_file_system(in_str)

    if not date_str:
        date_str = DEFAULT_DATE_STR

    # Finally get last modification date (user set option)
    return date_str
