#!/usr/bin/env python3

"""
Main functions of TriPhotoDate :

    - populate_db : scan files, get metatdatas and others infos, then store it in a database
    - compute : work on previous database, walk over files, filter given user options, generate a new path, then store it in a database
    - execute : simulate/copy/move file given results stored in the database at previous step

"""

import hashlib
import shutil
import sys
import os
import re
import time
from pathlib import Path
from datetime import datetime, timezone
import logging

from tri_photo_date.exif import ExifTags
from tri_photo_date.config import CONFIG as CFG

# from tri_photo_date.utils.config_paths import CONFIG_PATH
from tri_photo_date.utils.human_texts import *
from tri_photo_date.utils.constants import GROUP_PLACEHOLDER, DEFAULT_DATE_STR, DUP_PROCEDURE_KEEP_FIRST, DUP_PROCEDURE_MOVE_APART
from tri_photo_date import gps
from tri_photo_date.photo_database import ImageMetadataDB
from tri_photo_date.utils import fingerprint
from tri_photo_date.utils.small_tools import (
    fake_LoopCallBack,
    fake_progbar,
    rename_with_incr,
    move_file,
    create_out_str,
    get_date_from_exifs_or_file,
    bytes2human,
    limited_string
)

PLACEHOLDER_REGEX = re.compile(r"[{<]([^}>]+)[}>]")

def populate_db(progbar=fake_progbar, LoopCallBack=fake_LoopCallBack):
    fingerprint.set_global_config(CFG)

    # in_dir = CFG["source.dir"]
    # out_dir = CFG["destination.dir"]
    is_use_cache = CFG["scan"]["is_use_cached_datas"]
    min_size = CFG["files"]["min_size"] * 1000 if CFG["files"]["is_min_size"] else 0
    max_size = (
        CFG["files"]["max_size"] * 1000 * 1000 if CFG["files"]["is_max_size"] else sys.maxsize
    )

    # update image database
    media_extentions = tuple(CFG["scan"]["extentions"])
    with ImageMetadataDB() as db:
        db.clean_all_table()

        #### Scanning source folder ####
        nb_files = sum([len(f) for *_, f in os.walk(Path(CFG["source"]["dir"]))])
        progbar.init(nb_files)

        i = 0
        for folder, _, filenames in os.walk(Path(CFG["source"]["dir"])):
            for filename in filenames:
                i += 1

                # Some user feedback
                progbar.update(i, f"{i}/{nb_files}", PROGBAR_TXT_SCAN_SRCDIR)

                # PyQt5 callback to break loop
                if LoopCallBack.run():
                    break

                in_path = Path(folder, filename)

                if not filename.lower().endswith(media_extentions):
                    continue

                if not in_path.is_file():
                    continue

                if not (min_size < in_path.stat().st_size < max_size):
                    continue

                # Add entry to db
                db.add_image(str(in_path), is_use_cache=is_use_cache)


        if LoopCallBack.run():
            LoopCallBack.stopped = True
            return

        progbar.update(nb_files, PROGBAR_TXT_DONE)
        #### Scanning destination folder ####
        nb_files = sum([len(f) for *_, f in os.walk(Path(CFG["destination"]["dir"]))]) or 1
        progbar.init(nb_files)

        i = 0
        for folder, _, filenames in os.walk(Path(CFG["destination"]["dir"])):
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
                progbar.update(i, f"{i}/{nb_files}", PROGBAR_TXT_SCAN_DESTDIR)

            if LoopCallBack.run():
                break

        progbar.update(nb_files, f"{i} / {nb_files}", " - Fait.")

    LoopCallBack.stopped = True

def compute(progbar=fake_progbar, LoopCallBack=fake_LoopCallBack):
    gps.set_global_config(CFG)

    exclude = {
        "dirs": CFG["source"]["excluded_dirs"],
        "is_regex": bool(CFG["source"]["is_exclude_dir_regex"]),
        "toggle": CFG["source"]["exclude_toggle"],
    }
    exclude_cameras = {
        "cams" : CFG['source']["cameras"],
        "toggle" : CFG['source']['exclude_camera_toggle']
    }

    is_control_hash = CFG["duplicates"]["is_control"]
    control_dest_duplicates = CFG["duplicates"]["is_scan_dest"]
    duplicate_ctrl_mode = CFG["duplicates"]["mode"]

    dup_mode = duplicate_ctrl_mode * bool(is_control_hash)
    control_dest_duplicates = control_dest_duplicates * bool(is_control_hash)

    list_files_params = {
        "dir": Path(CFG["source"]["dir"]),
        "extentions": CFG["source"]["extentions"],
        "exclude_cameras": exclude_cameras,#CFG["source"]["cameras"],
        "recursive": CFG["source"]["is_recursive"],
        "dup_procedure":CFG["duplicates"]['procedure'],
        "dup_mode": dup_mode,
        "exclude": exclude,
    }

    with ImageMetadataDB() as db:
        db.clean_preview_table()

        nb_files, total_size = db.count(**list_files_params)
        progbar.init(nb_files if nb_files else 1)

        if CFG['duplicates']['procedure'] == DUP_PROCEDURE_MOVE_APART:
            for i, in_str in enumerate(db.list_duplicates(**list_files_params)):
                new_filename = rename_with_incr(db.exist_in_duplicates, Path(in_str).name)
                db.add_image_to_duplicates(in_str, new_filename)

        for i, in_str in enumerate(db.list_files(**list_files_params)):

            # Give user some feedbacks
            progbar.update(i, f"{i} / {nb_files}", PROGBAR_TXT_COMPUTE_FILES.format(Path(in_str).name))

            # get source image metadata
            metadatas = db.get_exifs(in_str)

            # PyQt5 break loop button
            if LoopCallBack.run():
                break

            # skip duplicates
            if control_dest_duplicates:
                if db.exist_in_dest(in_str, dup_mode):
                    if CFG['duplicates']['procedure'] == DUP_PROCEDURE_MOVE_APART:
                        db.add_image_to_duplicates(in_str)
                    continue

            # Generate a path string from user configuration
            out_str = create_out_str(
                in_str, CFG["destination"]["rel_dir"], CFG["destination"]["filename"]
            )

            # Get date and format output path string
            date_str = get_date_from_exifs_or_file(
                in_str,
                metadatas,
                CFG["options.name"]["is_guess"],
                CFG["options.name"]["guess_fmt"],
                CFG["options.general"]["is_date_from_filesystem"],
                CFG["options.general"]["is_force_date_from_filesystem"],
            )
            out_str = ExifTags.format_ym(date_str, out_str)

            # Get location from gps, add it to metadatas
            location = None
            if CFG["options.gps"]["is_gps"]:
                location = gps.get_image_gps_location(metadatas)
                if location:
                    metadatas.update(location)
                    db.add_location(in_str, location)

            # Format output string with image metadatas
            for tag_key in PLACEHOLDER_REGEX.findall(out_str):
                if tag_key == "group":
                    continue  # skip group, done separatly in another loop
                tag_value = metadatas.get(tag_key, "").strip() # remove trailling spaces

                out_str = ExifTags.format_tag(out_str, tag_key, tag_value)

            # rename files with duplicates names in same folder
            # Take too much time
            if not CFG["options.group"]["is_group"]:
                new_filename = rename_with_incr(db.exist_in_preview, Path(in_str).name)

            # Update the datas base
            db.add_image_to_preview(in_str, out_str, location, date_str)

        progbar.update(nb_files, PROGBAR_TXT_DONE)

        # Quit if loop end signal send by user
        if LoopCallBack.run():
            LoopCallBack.stopped = True
            return

        if CFG["options.group"]["is_group"]:
            progbar.update(0, PROGBAR_TXT_COMPUTE_GROUPS_START)

            # compute group for all files
            db.group_by_n_floating_days(CFG["options.group"]["floating_nb"])

            # progbar.init(nb_files)
            for i, in_str in enumerate(db.list_files(**list_files_params)):

                # Some user feedbacks
                progbar.update(i, f"{i}/{nb_files}",  PROGBAR_TXT_COMPUTE_GROUPS.format(Path(in_str).name))

                # PyQt5 callback to stop loop
                if LoopCallBack.run():
                    break

                # Get group and format it following user config
                group_date = db.get_date_group(in_str)
                group_str = group_date.strftime(CFG["options.group"]["display_fmt"])

                # Insert it in output path
                group_regex = re.compile(GROUP_PLACEHOLDER)
                out_str = os.path.join(*db.get_out_str(in_str))
                out_str = group_regex.sub(group_str, out_str)

                # rename if needed duplicates names
                out_str = rename_with_incr(db.exist_in_preview, out_str)

                # Save to db
                db.add_out_path(in_str, out_str)

    progbar.update(0, PROGBAR_TXT_DONE)

    LoopCallBack.stopped = True


def execute(progbar=fake_progbar, LoopCallBack=fake_LoopCallBack):

    dest_dir =  Path(CFG["destination"]["dir"])
    duplicates_dir = dest_dir / "duplicates"
    duplicates_dir.mkdir(parents=False, exist_ok=True)

    with ImageMetadataDB() as db:
        nb_files, total_size = db.count_preview()
        progbar.init(total_size)  # progbar.init(nb_files)

        bytes_moved = 0; i=0
        for i, (in_str, new_filename) in enumerate(db.get_duplicates_files()):
            bytes_moved += Path(in_str).stat().st_size

            # PyQt5 loop control
            if LoopCallBack.run():
                break

            move_file(in_str, duplicates_dir / new_filename, mode=CFG["action"]["action_mode"])

        bytes_moved = 0; i=0
        for i, in_str in enumerate(db.get_preview_files()):
            bytes_moved += Path(in_str).stat().st_size

            # PyQt5 loop control
            if LoopCallBack.run():
                break

            # transform relative path into absolute path given user config
            out_rel_str, out_filename = db.get_out_str(in_str)
            out_str = str(Path(CFG["destination"]["dir"], out_rel_str, out_filename))

            # SImulate / Move / Copy
            has_moved = move_file(in_str, out_str, mode=CFG["action"]["action_mode"])

            # Add metadata to new files if needed
            if has_moved and CFG["options.gps"]["is_gps"]:
                metadatas = db.get_exifs(in_str)
                location = gps.get_image_gps_location(metadatas)
                if location:
                    ExifTags.add_location_to_iptc(out_str, location)

            if has_moved and CFG["options.general"]["is_delete_metadatas"]:
                ExifTags.clear_all_metadatas(out_str)

            # User feedbacks
            progbar.update(bytes_moved, f"{bytes2human(bytes_moved)}/{bytes2human(total_size)}", PROGBAR_TXT_EXECUTE_FCT(
                CFG["action"]["action_mode"],
                in_str,
                out_str
            ))

    progbar.update(
        bytes_moved, f"{i}/{bytes2human(bytes_moved)}", PROGBAR_TXT_EXECUTE_DONE_FCT(i, bytes2human(bytes_moved), CFG["action"]["action_mode"])
    )

    LoopCallBack.stopped = True


if __name__ == "__main__":
    main()
