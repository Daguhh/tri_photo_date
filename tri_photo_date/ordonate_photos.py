#!/usr/bin/env python3

import hashlib
import shutil
import os
import re
import time
from pathlib import Path
from datetime import datetime, timezone
import logging

from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QEventLoop, QTimer

from tri_photo_date.utils.progressbar import cli_progbar
from tri_photo_date.exif import ExifTags, EXIF_DATE_FIELD, EXIF_LOCATION_FIELD, EXIF_CAMERA_FIELD, NoExifError
from tri_photo_date.utils.config_loader import CONFIG as CFG
from tri_photo_date.utils.config_loader import FILE_SIMULATE, FILE_COPY, FILE_MOVE, FILE_ACTION_TXT
from tri_photo_date.gps import add_tags_to_image, get_image_gps_location
from tri_photo_date.photo_database import ImageMetadataDB

GROUP_PLACEHOLDER = r"{group}"
#####################

#class COUNTERS:
#    duplicates = 0
#    nb_files = 0
#
#    @classmethod
#    def reset(cls):
#        cls.duplicates = 0
#        cls.nb_files = 0

def limited_string(s, limit=43, prefix=20, suffix=20):
    if len(s) > limit:
        return s[:prefix] + '...' + s[-suffix:]
    else:
        return s

def bytes2human(n, format="%(value)i%(symbol)s"):
    """
    >>> bytes2human(10000)
    '9K'
    >>> bytes2human(100001221)
    '95M'
    """
    symbols = ('B', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols[1:]):
        prefix[s] = 1 << (i+1)*10
    for symbol in reversed(symbols[1:]):
        if n >= prefix[symbol]:
            value = float(n) / prefix[symbol]
            return format % locals()
    return format % dict(symbol=symbols[0], value=n)


def gen_regex_for_duplicates(filename):
    path = Path(filename)
    reg = re.compile(
        path.stem + r"(?:\s\(([0-9]+))\)?" + path.suffix.lower()
    )
    return reg

def rename_with_incr(db, out_str):
    # Could be heavy load when lot of files with same name in same folder
    # Move and rename with increment if needed
    out_path = Path(out_str)
    directory = out_path.parent
    stem = out_path.stem
    ext = out_path.suffix.lower()
    filename = stem + ext

    count = 1
    collidable_files =  db.exist_in_preview(out_path)
    if collidable_files is not None:
        reg = gen_regex_for_duplicates(filename)
        indexes = [int(reg.fullmatch(s).group(1)) for s in collidable_files if reg.fullmatch(s) is not None]
        #print(collidable_fi)
        m = max(indexes + [-1])
        #print(m)
        filename = f"{stem} ({m+1}){ext}"

    #while filename in collidable_files:
    #    filename = f"{stem} ({count}){ext}"
    #    count += 1

    return str(directory / filename)

def list_available_exts(in_path, recursive=True):
    exts = set()

    #for in_str in list_n_filter(in_path, "", recursive=recursive):
    #    exts.update((Path(in_str).suffix.lower(),))
    with ImageMetadataDB() as db:
        exts = db.get_extention_list()

    logging.info(f"Available extentions:\n{exts}")

    return sorted(exts)

def list_available_tags(in_path, extentions, recursive=True):
    #exifs_all = set()

    with ImageMetadataDB() as db:
        exifs_all, exifs_common = db.get_tag_list()

    logging.info(f"all available exifs tags: {exifs_all} all common exifs tags: {exifs_common}")

    return sorted(exifs_all), sorted(exifs_common)

def list_available_camera_model(in_path, extentions, recursive=True):
    cameras = set()

    with ImageMetadataDB() as db:
        cameras = db.get_camera_list()

    return sorted(cameras)


def move_file(in_str, out_str):
    logging.info(f"Moving : {in_str}")

    in_path = Path(in_str)
    out_path = Path(out_str)

    if not out_path.parent.exists():
        Path.mkdir(out_path.parent, parents=True, exist_ok=True)

    if CFG["file_action"] == FILE_SIMULATE:
        return False
    elif CFG['file_action'] == FILE_COPY:
        shutil.copyfile(in_path, out_path)
    elif CFG['file_action'] == FILE_MOVE:
        shutil.move(in_path, out_path)

    logging.info(f"     ==> {str(out_path)}")

    return True

def create_out_str(in_str, out_path_str, out_filename):

    in_path = Path(in_str)
    out_name = out_filename + in_path.suffix if out_filename else in_path.name
    out_str = str(Path(out_path_str) / out_name)

    return out_str


def get_date_from_exifs_or_file(in_str, metadatas):
    date_str = ""

    # First start looking at file name (user option)
    if CFG['is_guess_date_from_name']:
        date_fmt = CFG['guess_date_from_name_str']
        date_str = ExifTags.get_date_from_name(date_fmt, in_str)

    # Try in metadatas
    if not date_str:
        for date_tag in EXIF_DATE_FIELD.values():
            if date_tag in metadatas:
                date_str = metadatas[date_tag]
                break

    # Finally get last modification date (user set option)
    if not date_str and CFG['date_from_filesystem']:
        timestamp = Path(in_str).stat().st_mtime
        date = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        out_fmt = "%Y:%m:%d %H:%M:%S"
        date_str = date.strftime(out_fmt)

    return date_str

def loop_control(loop_stop, update_text_on_button):

    # PyQt5 loop control
    if loop_stop is not None :
        loop = QEventLoop()
        QTimer.singleShot(0, loop.quit)
        loop.exec_()
        update_text_on_button()
        if loop_stop.stop_signal:
            return True
    return False


#def populate_db(progbar=cli_progbar, loop_stop=None, counterWdg=None, update_text_on_button=None):
def populate_db(progbar=cli_progbar, LoopCallBack=None):

    CFG.load_config()

    in_dir = CFG['in_dir']
    out_dir = CFG['out_dir']

    # update image database
    media_extentions = CFG['accepted_formats']
    with ImageMetadataDB() as db:

        db.clean_all_table()

        progbar.update(0, f"Looking for all files in {out_dir} ...")

        #### Scanning source folder ####
        nb_files = sum([len(f) for *_,f in os.walk(in_dir)])
        progbar.init(nb_files)

        i = 0
        for folder, _, filenames in os.walk(in_dir):
            for filename in filenames:
                i += 1

                if LoopCallBack.run():
                    break

                in_path = Path(folder, filename)
                #if not filename.lower().endswith(media_extentions):
                #    continue

                db.add_image(str(in_path))

                progbar.update(i, f"{i} / {nb_files} - Calculating hash and loading metadatas ...")

            if LoopCallBack.run() :
                break

        #### Scanning destination folder ####
        nb_files = sum([len(f) for *_,f in os.walk(in_dir)])
        progbar.init(nb_files)

        i = 0
        for folder, _, filenames in os.walk(out_dir):
            for filename in filenames:

                in_path = Path(folder, filename)
                if not filename.lower().endswith(media_extentions):
                    continue

                i += 1
                db.scan_dest(str(in_path))

                progbar.update(i, f"{i} / {nb_files} - Scanning files in destination folder...")

            if LoopCallBack.run() :
                break

        progbar.update(i, f"{i} / {nb_files} - Fait.")

    LoopCallBack.stopped = True

def compute(progbar=cli_progbar, LoopCallBack=None):

    is_control_hash = CFG['is_control_duplicates']
    control_dest_duplicates = CFG['dup_is_scan_dest']
    duplicate_ctrl_mode = CFG['dup_mode']
    #is_hash_reset = CFG["hash_reset"]
    in_dir = CFG['in_dir']
    extentions = CFG["extentions"]
    cameras = CFG['cameras']
    #out_dir = CFG['out_dir']
    out_path_str = CFG['out_path_str']
    out_filename = CFG['filename']
    is_gps = CFG['gps']
    recursive = CFG['is_recursive']
    is_group_floating_days = CFG['is_group_floating_days']
    group_floating_days_nb = CFG['group_floating_days_nb']
    group_floating_days_fmt = CFG['group_floating_days_fmt']

    dup_mode = duplicate_ctrl_mode * bool(is_control_hash)
    control_dest_duplicates = control_dest_duplicates * bool(is_control_hash)
    list_files_params = {
        'src_dir' : in_dir,
        'extentions' : extentions,
        'cameras' : cameras,
        'recursive' : recursive,
        'dup_mode' : dup_mode
    }

    import time; tic = time.time()
    with ImageMetadataDB() as db:

        db.clean_preview_table()

        nb_files, total_size = db.count(**list_files_params)#in_dir, extentions, cameras)
        progbar.init(nb_files) #progbar.init(nb_files)

        for i, in_str in enumerate(db.list_files(**list_files_params)):

            ############ PyQt5 loop control ############
            toc = time.time() - tic
            print('#'*int(1000*toc))
            tic = time.time()
            if LoopCallBack.run() :
                break

            ######## test if file already in dest ######
            if control_dest_duplicates:
                if db.exist_in_dest(in_str, dup_mode):
                    continue

            ######## Initiate new file to compute ######
            #db.add_image_to_preview(in_str)

            # gather "placeholdered" absolute out path #
            out_str = create_out_str(in_str,out_path_str,out_filename)

            metadatas = db.get_exifs(in_str)

            ################ Format date ###############
            date_str = get_date_from_exifs_or_file(in_str, metadatas)

            #if date_str:
                #db.add_date_to_preview(in_str, date_str)
            out_str = ExifTags.format_ym(date_str, out_str)

            #################### Format gps ####################
            location=None
            if is_gps:
                location = get_image_gps_location(metadatas)
                if location:
                    metadatas.update(location)
                    db.add_location(in_str, location)

            ################ Format others tags ################
            placeholder_regex = re.compile(r'[{<]([^}>]+)[}>]')
            for tag_key in placeholder_regex.findall(out_str):
                if tag_key == "group" :
                    continue
                tag_value = metadatas.get(tag_key, '')
                out_str = ExifTags.format_tag(out_str, tag_key, tag_value)
            # Rename file with increment if name is duplicate ##
            out_str = rename_with_incr(db, out_str)

            ##### Save the generated out path to database ######
            #db.add_out_path(in_str, out_str)
            db.add_image_to_preview(in_str, out_str, location, date_str)
            progbar.update(i, f"{i} / {nb_files} - {Path(in_str).name} - Resolving new path...")

        progbar.update(i, "Fait!")

        # Quit if loop end signal send by user
        if LoopCallBack.run() :
            LoopCallBack.stopped = True
            return

        ############ Try to group by day floating ##########
        if is_group_floating_days :

            progbar.update(i, "Fait! Tri des fichiers pour groupenement par date...")

            db.group_by_n_floating_days(group_floating_days_nb)

            #progbar.init(nb_files)

            for i, in_str in enumerate(db.list_files(**list_files_params)):
                ############ PyQt5 loop control ############
                if LoopCallBack.run() :
                    break

                group_date = db.get_date_group(in_str)
                if group_date is not None:
                    group_regex = re.compile(GROUP_PLACEHOLDER)
                    group_str = group_date.strftime(group_floating_days_fmt)
                    out_str = os.path.join(*db.get_out_str(in_str))
                    out_str = group_regex.sub(group_str, out_str)
                    db.add_out_path(in_str, out_str)

                progbar.update(i, f"{i} / {nb_files} - {Path(in_str).name} - Group images by date")

    progbar.update(i, " Fait!")
    LoopCallBack.stopped = True

def execute(progbar=cli_progbar, LoopCallBack=None):

    with ImageMetadataDB() as db:

        nb_files, total_size = db.count_preview()
        progbar.init(total_size) #progbar.init(nb_files)
        bytes_moved = 0

        for i, in_str in enumerate(db.get_preview_files()):

            bytes_moved += Path(in_str).stat().st_size

            # PyQt5 loop control
            if LoopCallBack.run() :
                break

            out_rel_str, out_filename = db.get_out_str(in_str)
            out_str = str(CFG['out_dir'] / out_rel_str / out_filename)
            has_moved = move_file(in_str, out_str)

            if has_moved and is_gps:
                metadatas = db.get_metadatas(in_str)
                location = get_image_gps_location(metadatas)
                if location:
                    ExifTags.add_location_to_iptc(out_str, location)
                    #with ExifTags(out_str) as im_exif:
                    #    try:
                    #        im_exif.add_localisation(location)
                    #    except NoExifError as e:
                    #        print("Issue while loading gps, skipping", e)

            progbar_text_execute = lambda a,b,c,d,e: ''.join((
    f"{bytes2human(a)}/ {bytes2human(b)}",
    ' - ',
    FILE_ACTION_TXT[c].format(Path(d).name, limited_string(Path(e).parent.name))
))

            progbar.update(i, progbar_text_execute(bytes_moved, total_size,CFG['file_action'],in_str, out_str))

    progbar.update(bytes_moved, "Fait! {} fichiers ont été déplacés soit un total de {}".format(i, bytes2human(bytes_moved)))

    LoopCallBack.stopped = True

if __name__ == "__main__":
    main()
