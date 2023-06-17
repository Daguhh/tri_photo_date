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
from tri_photo_date.utils.config_loader import FILE_ACTION_TXT
from tri_photo_date import gps
from tri_photo_date.photo_database import ImageMetadataDB
from tri_photo_date.utils.converter import bytes2human, limited_string
from tri_photo_date.utils import fingerprint
from tri_photo_date.utils.small_tools import fake_LoopCallBack, Timer, gen_regex_index, rename_with_incr, move_file, create_out_str, get_date_from_file_system, get_date_from_exifs_or_file

GROUP_PLACEHOLDER = r"{group}"
DEFAULT_DATE_STR = "1900:01:01 00:00:00"



def populate_db(progbar=cli_progbar, LoopCallBack=fake_LoopCallBack):

    CFG.load_config()
    fingerprint.set_global_config(CFG)

    #in_dir = CFG["source.dir"]
    #out_dir = CFG["destination.dir"]
    is_use_cache = CFG["scan.is_use_cached_datas"]
    min_size = CFG['files.min_size'] *1000 if CFG['files.is_min_size'] else 0
    max_size = CFG['files.max_size'] *1000*1000 if CFG['files.is_max_size'] else sys.maxsize

    # update image database
    media_extentions = CFG["misc.accepted_formats"]
    with ImageMetadataDB() as db:
        db.clean_all_table()
        progbar.update(0, f"Looking for all files in {CFG['source.dir']} ...")

        #### Scanning source folder ####
        nb_files = sum([len(f) for *_, f in os.walk(CFG['source.dir'])])
        progbar.init(nb_files)

        i = 0
        for folder, _, filenames in os.walk(CFG['source.dir']):
            for filename in filenames:
                i += 1

                # PyQt5 callback to break loop
                if LoopCallBack.run():
                    break

                in_path = Path(folder, filename)
                # if not filename.lower().endswith(media_extentions):
                #    continue
                if not (min_size < in_path.stat().st_size < max_size):
                    continue

                # Add entry to db
                db.add_image(str(in_path), is_use_cache=is_use_cache)

                # Some user feedback
                progbar.update(
                    i, f"{i} / {nb_files} - Calculating hash and loading metadatas ..."
                )

        if LoopCallBack.run():
            LoopCallBack.stopped = True
            return

        #### Scanning destination folder ####
        nb_files = sum([len(f) for *_, f in os.walk(CFG['destination.dir'])])
        progbar.init(nb_files)

        i = 0
        for folder, _, filenames in os.walk(CFG['destination.dir']):
            for filename in filenames:
                i += 1

                if LoopCallBack.run():
                    break

                in_path = Path(folder, filename)
                # if not filename.lower().endswith(media_extentions):
                #    continue

                # add entry to db
                db.add_image(str(in_path), to_process=False, is_use_cache=is_use_cache)

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

    # is_hash_reset = CFG["hash_reset"]
    #in_dir = CFG["source.dir"]
    #extentions = CFG["source.extentions"]
    #cameras = CFG["source.cameras"]
    # out_dir = CFG['out_dir']
    #excluded_dirs = CFG["source.excluded_dirs"]
    #is_exclude_dir_regex = bool(CFG["source.is_exclude_dir_regex"])
    #exclude_toggle = CFG["source.exclude_toggle"]
    exclude = {
        "dirs": CFG["source.excluded_dirs"],
        "is_regex": bool(CFG["source.is_exclude_dir_regex"]),
        "toggle": CFG["source.exclude_toggle"],
    }
    # is_gps = CFG["options.gps.is_gps"]
    #recursive = CFG["source.is_recursive"]
    # is_group_floating_days = CFG["options.group.is_group"]
    # group_floating_days_nb = CFG["options.group.floating_nb"]
    # group_floating_days_fmt = CFG["options.group.display_fmt"]

    is_control_hash = CFG["duplicates.is_control"]
    control_dest_duplicates = CFG["duplicates.is_scan_dest"]
    duplicate_ctrl_mode = CFG["duplicates.mode"]

    dup_mode = duplicate_ctrl_mode * bool(is_control_hash)
    control_dest_duplicates = control_dest_duplicates * bool(is_control_hash)

    list_files_params = {
        "dir": CFG["source.dir"],
        "extentions": CFG["source.extentions"],
        "cameras": CFG["source.cameras"],
        "recursive": CFG["source.is_recursive"],
        "dup_mode": dup_mode,
        "exclude": exclude,
    }

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
            out_str = create_out_str(in_str, CFG["destination.rel_dir"], CFG["destination.filename"])

            # Get date and format output path string
            date_str = get_date_from_exifs_or_file(
                in_str,
                metadatas,
                CFG['options.name.is_guess'],
                CFG['options.name.guess_fmt'],
                CFG['options.general.is_date_from_filesystem'],
                CFG['options.general.is_force_date_from_filesystem'],
            )
            out_str = ExifTags.format_ym(date_str, out_str)

            # Get location from gps, add it to metadatas
            location = None
            if CFG["options.gps.is_gps"]:
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
            if not CFG["options.group.is_group"]:
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

        if CFG["options.group.is_group"]:
            progbar.update(i, "Fait! Tri des fichiers pour groupement par date...")

            # compute group for all files
            db.group_by_n_floating_days(CFG["options.group.floating_nb"])

            # progbar.init(nb_files)
            Timer.tic()
            for i, in_str in enumerate(db.list_files(**list_files_params)):
                Timer.toc()

                # PyQt5 callback to stop loop
                if LoopCallBack.run():
                    break

                # Get group and format it following user config
                group_date = db.get_date_group(in_str)
                group_str = group_date.strftime(CFG["options.group.display_fmt"])

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
            out_str = str(CFG["destination.dir"] / out_rel_str / out_filename)

            # SImulate / Move / Copy
            has_moved = move_file(in_str, out_str, mode=CFG["action.action_mode"])

            # Add metadata to new files if needed
            if has_moved and CFG["options.gps.is_gps"]:
                metadatas = db.get_metadatas(in_str)
                location = gps.get_image_gps_location(metadatas)
                if location:
                    ExifTags.add_location_to_iptc(out_str, location)

            if has_moved and CFG["options.general.is_delete_metadatas"]:
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
