#!/usr/bin/env python3

import hashlib
import shutil
import sys
import os
import re
import time
from pathlib import Path
from datetime import datetime, timezone
import logging

from tri_photo_date.cli.progressbar import cli_progbar
from tri_photo_date.exif import (
    ExifTags,
    EXIF_DATE_FIELD,
    EXIF_LOCATION_FIELD,
    EXIF_CAMERA_FIELD,
    NoExifError,
)
from tri_photo_date.utils.config_loader import CONFIG as CFG

# from tri_photo_date.utils.config_paths import CONFIG_PATH
from tri_photo_date.utils.config_loader import (
    FILE_SIMULATE,
    FILE_COPY,
    FILE_MOVE,
    FILE_ACTION_TXT,
)
from tri_photo_date import gps
from tri_photo_date.photo_database import ImageMetadataDB
from tri_photo_date.utils.converter import bytes2human, limited_string

GROUP_PLACEHOLDER = r"{group}"
DEFAULT_DATE_STR = "1900:01:01 00:00:00"


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


def move_file(in_str, out_str):
    in_path = Path(in_str)
    out_path = Path(out_str)

    if not out_path.parent.exists():
        Path.mkdir(out_path.parent, parents=True, exist_ok=True)

    if CFG["action.action_mode"] == FILE_SIMULATE:
        return False
    elif CFG["action.action_mode"] == FILE_COPY:
        shutil.copyfile(in_path, out_path)
    elif CFG["action.action_mode"] == FILE_MOVE:
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


def get_date_from_exifs_or_file(in_str, metadatas):
    date_str = ""

    # First start looking at file name (user option)
    if CFG["options.name.name_is_guess"]:
        date_fmt = CFG["options.name.name_guess_fmt"]
        date_str = ExifTags.get_date_from_name(date_fmt, in_str)

    if not date_str and CFG["options.general.opt_is_date_from_filesystem"]:
        timestamp = Path(in_str).stat().st_mtime
        date = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        out_fmt = "%Y:%m:%d %H:%M:%S"
        date_str = date.strftime(out_fmt)

    # Try in metadatas
    if not date_str:
        for date_tag in EXIF_DATE_FIELD.values():
            if date_tag in metadatas:
                date_str = metadatas[date_tag]
                break

    if not date_str:
        date_str = DEFAULT_DATE_STR

    # Finally get last modification date (user set option)
    return date_str


def populate_db(progbar=cli_progbar, LoopCallBack=fake_LoopCallBack):
    CFG.load_config()

    in_dir = CFG["source.src_dir"]
    out_dir = CFG["destination.dest_dir"]
    is_use_cache = CFG["scan.scan_is_use_cached_datas"]

    # update image database
    media_extentions = CFG["misc.accepted_formats"]
    with ImageMetadataDB() as db:
        db.clean_all_table()
        progbar.update(0, f"Looking for all files in {out_dir} ...")

        #### Scanning source folder ####
        nb_files = sum([len(f) for *_, f in os.walk(in_dir)])
        progbar.init(nb_files)

        i = 0
        for folder, _, filenames in os.walk(in_dir):
            for filename in filenames:
                i += 1

                # PyQt5 callback to break loop
                if LoopCallBack.run():
                    break

                in_path = Path(folder, filename)
                # if not filename.lower().endswith(media_extentions):
                #    continue

                # Add entry to db
                db.add_image(str(in_path), is_use_cache=is_use_cache)

                # Some user feedback
                progbar.update(
                    i, f"{i} / {nb_files} - Calculating hash and loading metadatas ..."
                )

        #### Scanning destination folder ####
        nb_files = sum([len(f) for *_, f in os.walk(out_dir)])
        progbar.init(nb_files)

        i = 0
        for folder, _, filenames in os.walk(out_dir):
            for filename in filenames:
                i += 1

                if LoopCallBack.run():
                    break

                in_path = Path(folder, filename)
                # if not filename.lower().endswith(media_extentions):
                #    continue

                # add entry to db
                db.scan_dest(str(in_path), is_use_cache=is_use_cache)

                # Soe user feedback
                progbar.update(
                    i, f"{i} / {nb_files} - Scanning files in destination folder..."
                )

            if LoopCallBack.run():
                break

        progbar.update(i, f"{i} / {nb_files} - Fait.")

    LoopCallBack.stopped = True


def compute(progbar=cli_progbar, LoopCallBack=fake_LoopCallBack):
    gps.set_global_config(CFG)
    is_control_hash = CFG["duplicates.dup_is_control"]
    control_dest_duplicates = CFG["duplicates.dup_is_scan_dest"]
    duplicate_ctrl_mode = CFG["duplicates.dup_mode"]
    # is_hash_reset = CFG["hash_reset"]
    in_dir = CFG["source.src_dir"]
    extentions = CFG["source.src_extentions"]
    cameras = CFG["source.src_cameras"]
    # out_dir = CFG['out_dir']
    excluded_dirs = CFG["source.src_excluded_dirs"]
    is_exclude_dir_regex = bool(CFG["source.src_is_exclude_dir_regex"])
    exclude_toggle = CFG["source.src_exclude_toggle"]
    exclude = {
        "dirs": excluded_dirs,
        "is_regex": is_exclude_dir_regex,
        "toggle": exclude_toggle,
    }
    out_path_str = CFG["destination.dest_rel_dir"]
    out_filename = CFG["destination.dest_filename"]
    is_gps = CFG["options.gps.gps_is_gps"]
    recursive = CFG["source.src_is_recursive"]
    is_group_floating_days = CFG["options.group.grp_is_group"]
    group_floating_days_nb = CFG["options.group.grp_floating_nb"]
    group_floating_days_fmt = CFG["options.group.grp_display_fmt"]

    dup_mode = duplicate_ctrl_mode * bool(is_control_hash)
    control_dest_duplicates = control_dest_duplicates * bool(is_control_hash)
    list_files_params = {
        "src_dir": in_dir,
        "extentions": extentions,
        "cameras": cameras,
        "recursive": recursive,
        "dup_mode": dup_mode,
        "exclude": exclude,
    }

    print(list_files_params)
    with ImageMetadataDB() as db:
        db.clean_preview_table()

        nb_files, total_size = db.count(**list_files_params)
        progbar.init(nb_files if nb_files else 1)

        Timer.tic()
        for i, in_str in enumerate(db.list_files(**list_files_params)):
            Timer.toc()

            # get source image metadata
            metadatas = db.get_exifs(in_str)

            # PyQt5 break loop button
            if LoopCallBack.run():
                break

            # skip duplicates
            if control_dest_duplicates:
                if db.exist_in_dest(in_str, dup_mode):
                    continue

            # Generate a path string from user configuration
            out_str = create_out_str(in_str, out_path_str, out_filename)

            # Get date and format output path string
            date_str = get_date_from_exifs_or_file(in_str, metadatas)
            out_str = ExifTags.format_ym(date_str, out_str)

            # Get location from gps, add it to metadatas
            location = None
            if is_gps:
                location = gps.get_image_gps_location(metadatas)
                if location:
                    metadatas.update(location)
                    db.add_location(in_str, location)

            # Format output string with image metadatas
            placeholder_regex = re.compile(r"[{<]([^}>]+)[}>]")
            for tag_key in placeholder_regex.findall(out_str):
                if tag_key == "group":
                    continue  # skip group, done separatly in another loop
                tag_value = metadatas.get(tag_key, "")

                out_str = ExifTags.format_tag(out_str, tag_key, tag_value)

            # rename files with duplicates names in same folder
            if not is_group_floating_days:
                out_str = rename_with_incr(db, out_str)

            # Update the datas base
            db.add_image_to_preview(in_str, out_str, location, date_str)

            # Give user some feedbacks
            progbar.update(
                i, f"{i} / {nb_files} - {Path(in_str).name} - Resolving new path..."
            )

        progbar.update(nb_files, "Fait!")

        # Quit if loop end signal send by user
        if LoopCallBack.run():
            LoopCallBack.stopped = True
            return

        if is_group_floating_days:
            progbar.update(i, "Fait! Tri des fichiers pour groupement par date...")

            # compute group for all files
            db.group_by_n_floating_days(group_floating_days_nb)

            # progbar.init(nb_files)
            Timer.tic()
            for i, in_str in enumerate(db.list_files(**list_files_params)):
                Timer.toc()

                # PyQt5 callback to stop loop
                if LoopCallBack.run():
                    break

                # Get group and format it following user config
                group_date = db.get_date_group(in_str)
                group_str = group_date.strftime(group_floating_days_fmt)

                # Insert it in output path
                group_regex = re.compile(GROUP_PLACEHOLDER)
                out_str = os.path.join(*db.get_out_str(in_str))
                out_str = group_regex.sub(group_str, out_str)

                # rename if needed duplicates names
                out_str = rename_with_incr(db, out_str)

                # Save to db
                db.add_out_path(in_str, out_str)

                # SOme user feedbacks
                progbar.update(
                    i, f"{i} / {nb_files} - {Path(in_str).name} - Group images by date"
                )

    progbar.update(0, " Fait!")

    LoopCallBack.stopped = True


def execute(progbar=cli_progbar, LoopCallBack=fake_LoopCallBack):
    is_gps = CFG["options.gps.gps_is_gps"]
    is_delete_metadatas = CFG["options.general.opt_is_delete_metadatas"]

    with ImageMetadataDB() as db:
        nb_files, total_size = db.count_preview()
        progbar.init(total_size)  # progbar.init(nb_files)

        bytes_moved = 0
        for i, in_str in enumerate(db.get_preview_files()):
            bytes_moved += Path(in_str).stat().st_size

            # PyQt5 loop control
            if LoopCallBack.run():
                break

            # transform relative path into absolute path given user config
            out_rel_str, out_filename = db.get_out_str(in_str)
            out_str = str(CFG["destination.dest_dir"] / out_rel_str / out_filename)

            # SImulate / Move / Copy
            has_moved = move_file(in_str, out_str)

            # Add metadata to new files if needed
            if has_moved and is_gps:
                metadatas = db.get_metadatas(in_str)
                location = gps.get_image_gps_location(metadatas)
                if location:
                    ExifTags.add_location_to_iptc(out_str, location)

            if has_moved and is_delete_metadatas:
                ExifTags.clear_all_metadatas(out_str)

            # User feedbacks
            progbar_text_execute = lambda a, b, c, d, e: "".join(
                (
                    f"{bytes2human(a)}/ {bytes2human(b)}",
                    " - ",
                    FILE_ACTION_TXT[c].format(
                        Path(d).name, limited_string(Path(e).parent.name)
                    ),
                )
            )
            progbar.update(
                bytes_moved,
                progbar_text_execute(
                    bytes_moved, total_size, CFG["action.action_mode"], in_str, out_str
                ),
            )

    progbar.update(
        bytes_moved,
        "Fait! {} fichiers ont été déplacés soit un total de {}".format(
            i, bytes2human(bytes_moved)
        ),
    )

    LoopCallBack.stopped = True


if __name__ == "__main__":
    main()
