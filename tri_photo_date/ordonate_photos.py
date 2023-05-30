#!/usr/bin/env python3

import hashlib
import shutil
import os
import re
import time
from pathlib import Path
from datetime import datetime
import logging

from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QEventLoop, QTimer
#from unidecode import unidecode

#try:
#    from utils.progressbar import progressbar as cli_progbar
#    from exif import ExifTags, EXIF_DATE_FIELD, EXIF_LOCATION_FIELD, EXIF_CAMERA_FIELD
#    #from utils.config_loader import ICON_DIR
#    from utils.config_loader import CONFIG as CFG
#    from gps import add_tags_to_image, get_image_gps_location
#except ModuleNotFoundError:
from tri_photo_date.utils.progressbar import cli_progbar
from tri_photo_date.exif import ExifTags, EXIF_DATE_FIELD, EXIF_LOCATION_FIELD, EXIF_CAMERA_FIELD, NoExifError
#from tri_photo_date.utils.config_loader import ICON_DIR
from tri_photo_date.utils.config_loader import CONFIG as CFG
from tri_photo_date.utils.config_loader import FILE_SIMULATE, FILE_COPY, FILE_MOVE
from tri_photo_date.gps import add_tags_to_image, get_image_gps_location
from tri_photo_date.photo_database import ImageMetadataDB

#####################

class COUNTERS:
    duplicates = 0
    nb_files = 0

    @classmethod
    def reset(cls):
        cls.duplicates = 0
        cls.nb_files = 0

###### Tools ###########

#class HashsCls:
#    HASHS = {}
#
#    @classmethod
#    def reset(cls):
#        cls.HASHS = {}
#
#    @classmethod
#    def populate(cls, path, extentions):
#        logging.info(f"Calculating hash of files in {path}")
#        for f in list_n_filter(path, extentions):
#            if Path(f).is_file():
#                cls.HASHS[f] = cls.hash_file(Path(f))
#
#    @classmethod
#    def hash_file(cls, path: Path) -> str:
#        # already calculated
#        if path in cls.HASHS:
#            return cls.HASHS[path]
#
#        with path.open("rb") as file:
#            md5 = hashlib.md5()
#            while chunk := file.read(8192):
#                md5.update(chunk)
#
#        return md5.hexdigest()
#
#def is_exist_file_in_dest(in_path, out_path):
#    if (hash_val := HashsCls.hash_file(in_path)) in HashsCls.HASHS.values():
#        COUNTERS.duplicates += 1
#        return True
#
#    HashsCls.HASHS[in_path] = hash_val
#    return False

def limited_string(s, limit=43, prefix=20, suffix=20):
    if len(s) > limit:
        return s[:prefix] + '...' + s[-suffix:]
    else:
        return s

def rename_with_incr(out_str):
    # Move and rename with increment if needed
    out_path = Path(out_str)
    directory = out_path.parent
    filename = out_path.stem
    ext = out_path.suffix.lower()

    count = 1
    out_path = directory / f"{filename}{ext}"
    with ImageMetadataDB() as db:
        while db.exist_in_preview(out_path):
            out_path = directory / f"{filename} ({count}){ext}"
            count += 1

    return str(out_path)

#def list_n_filter_old(src_dir, extentions, cameras=[]):
#    for folder, _, filenames in os.walk(src_dir):
#        for filename in filenames:
#            if filename.lower().endswith(extentions):
#                if cameras and cameras[0]:
#                    try:
#                        with ExifTags(str(Path(folder, filename))) as im_exif:
#                            if not im_exif.get(EXIF_CAMERA_FIELD['camera'],'xxx') in cameras:
#                                continue
#                    except NoExifError as e:
#                        print(e)
#                        print("Issue while loading gps, skipping")
#                yield Path(folder, filename)

#def test_camera(im_path, cameras):
#    # No filter set
#    if not cameras or not cameras[0]:
#        return True
#
#    try:
#        with ExifTags(str(im_path)) as im_exif:
#            exif_field = EXIF_CAMERA_FIELD['camera']
#            camera = im_exif.get(exif_field,'xxx')
#            if camera in cameras:
#                return True
#    except NoExifError as e:
#        print("Issue while loading gps, skipping", e)
#
#    return False
#
#def list_n_filter(src_dir, extentions, cameras=[], recursive=True):
#
#    with ImageMetadataDB() as db:
#        db.list_files(src_dir, extentions, cameras, recursive)
#
#
#def list_n_filter_old(src_dir, extentions, cameras=[], recursive=True):
#
#    if not recursive:
#
#        folder = src_dir
#        for filename in os.listdir(folder):
#            im_path = Path(folder, filename)
#            if not filename.lower().endswith(extentions):
#                continue
#            if not test_camera(im_path, cameras):
#                continue
#            yield str(im_path)
#
#    else:
#
#        for folder, _, filenames in os.walk(src_dir):
#            for filename in filenames:
#                im_path = Path(folder, filename)
#                if not filename.lower().endswith(extentions):
#                    continue
#                if not test_camera(im_path, cameras):
#                    continue
#                yield str(im_path)

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

    #for in_str in list_n_filter(in_path, extentions, recursive=recursive):
    #    try:
    #        with ExifTags(in_str) as im_exif:
    #            exifs_all.update(im_exif.keys())
    #    except NoExifError as e:
    #        print("Issue while loading gps, skipping", e)

    #exifs_common = exifs_all.copy()
    #for in_str in list_n_filter(in_path, extentions, recursive=recursive):
    #    try:
    #        with ExifTags(in_str) as im_exif:
    #            exifs_common.intersection_update(set(im_exif.keys()))
    #    except NoExifError as e:
    #        print("Issue while loading gps, skipping", e)

    logging.info(f"all available exifs tags: {exifs_all} all common exifs tags: {exifs_common}")

    return sorted(exifs_all), sorted(exifs_common)

def list_available_camera_model(in_path, extentions, recursive=True):
    cameras = set()

    ##for in_str in list_n_filter(in_path, extentions, recursive=recursive):
    ##    try:
    ##        with ExifTags(in_str) as im_exif:
    ##            camera = im_exif.get(EXIF_CAMERA_FIELD['camera'],'')
    ##            cameras.update([camera,])
    ##    except NoExifError as e:
    ##        print("Issue while loading gps, skipping", e)
    with ImageMetadataDB() as db:
        cameras = db.get_camera_list()

    return sorted(cameras)

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

#def count_files(path, extentions, cameras=[], recursive=True):
#
#    nb_files = 0
#    total_size = 0
#    for f in list_n_filter(path, extentions, cameras=cameras, recursive=recursive):
#        nb_files += 1
#        total_size += Path(f).stat().st_size
#
#    #nb_files = len(list())
#    logging.info(f"{nb_files} files for a total of {bytes2human(total_size)} bytes {('taken by '+ str(cameras))*bool(cameras[0]) } found with {CFG['extentions']} in {CFG['in_dir'].name}")
#    COUNTERS.nb_files = nb_files
#
#    return nb_files, total_size

#def add_tags_to_folder(progbar=cli_progbar, labelWdg=False, imageWdg=False):
#
#    path = CFG["in_dir"]
#    extentions = CFG["extentions"]
#    cameras = CFG['cameras']
#    recursive = CFG['is_recursive']
#
#    nb_files, total_size = count_files(path, extentions, cameras)
#    progbar.init(nb_files)
#
#    for i,f in enumerate(list_n_filter(path, extentions, cameras=cameras, recursive=recursive)):
#
#        address_dct = add_tags_to_image(str(f))
#        progbar.update(i)
#        if not address_dct :
#            continue
#        text = address_dct[EXIF_LOCATION_FIELD['display_name']][0]
#        labelWdg.setText(text.replace(',','\n'))
#        imageWdg.setPixmap(QPixmap(str(f)).scaledToHeight(150))

def move_file(in_path, out_path):
    logging.info(f"Moving : {str(in_path)}")

    if not out_path.parent.exists():
        Path.mkdir(out_path.parent, parents=True, exist_ok=True)

    #if CFG["control_hash"]:
    #    if is_exist_file_in_dest(in_path, out_path):
    #        logging.info("     ==> file already exist : skipping")
    #        return False

    #out_path = rename_with_incr(Path(out_path))

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

def populate_db(loop_stop=None, counterWdg=None, update_text_on_button=None):

    CFG.load_config()

    in_dir = CFG['in_dir']
    out_dir = CFG['out_dir']

    # update image database
    media_extentions = CFG['accepted_formats']
    i = 0; j = 0
    with ImageMetadataDB() as db:

        #db.clean_all_table()
        COUNTERS.reset()

        for folder, _, filenames in os.walk(in_dir):
            for filename in filenames:

                # PyQt5 loop control
                if loop_stop is not None :
                    loop = QEventLoop()
                    QTimer.singleShot(0, loop.quit)
                    loop.exec_()
                    update_text_on_button()
                    if loop_stop.stop_signal:
                        break

                in_path = Path(folder, filename)
                if not filename.lower().endswith(media_extentions):
                    continue

                i += 1
                COUNTERS.nb_files += 1
                if counterWdg is not None: counterWdg.update(COUNTERS)

                db.add_image(str(in_path))
            if loop_stop.stop_signal:
                break

        for folder, _, filenames in os.walk(out_dir):
            for filename in filenames:

                # PyQt5 loop control
                if loop_stop is not None :
                    loop = QEventLoop()
                    QTimer.singleShot(0, loop.quit)
                    loop.exec_()
                    update_text_on_button()
                    if loop_stop.stop_signal:
                        break

                in_path = Path(folder, filename)
                if not filename.lower().endswith(media_extentions):
                    continue

                i += 1
                COUNTERS.nb_files += 1
                if counterWdg is not None: counterWdg.update(COUNTERS)

                db.scan_dest(str(in_path))
            if loop_stop.stop_signal:
                break
    if loop_stop is not None : loop_stop.stop_signal = True

#def main(progbar=cli_progbar, counterWdg=False, loop_stop=None):
def compute(progbar=cli_progbar, counterWdg=False, loop_stop=None):

    is_control_hash = CFG['control_hash']
    control_dest_duplicates = CFG['hash_populate']
    #is_hash_reset = CFG["hash_reset"]
    in_dir = CFG['in_dir']
    extentions = CFG["extentions"]
    cameras = CFG['cameras']
    #out_dir = CFG['out_dir']
    out_path_str = CFG['out_path_str']
    out_filename = CFG['filename']
    is_gps = CFG['gps']
    recursive = CFG['is_recursive']
    guess_date_from_name_str = CFG['guess_date_from_name']
    is_guess_date_from_name = CFG['is_guess_date_from_name']
    is_group_floating_days = CFG['is_group_floating_days']
    group_floating_days_nb = CFG['group_floating_days_nb']
    group_floating_days_fmt = CFG['group_floating_days_fmt']

    list_files_params = {
        'src_dir' : in_dir,
        'extentions' : extentions,
        'cameras' : cameras,
        'recursive' : recursive,
        'duplicate_md5_data' : is_control_hash
    }

    with ImageMetadataDB() as db:

        db.clean_dest_table()
        COUNTERS.reset()

        nb_files, total_size = db.count(**list_files_params)#in_dir, extentions, cameras)
        progbar.init(nb_files) #progbar.init(nb_files)

        for i, in_str in enumerate(db.list_files(**list_files_params)):

            ############ PyQt5 loop control ############
            if loop_stop is not None :
                loop = QEventLoop()
                QTimer.singleShot(0, loop.quit)
                loop.exec_()
                if loop_stop.stop_signal:
                    break

            ######## test if file already in dest ######
            if control_dest_duplicates:
                if db.exist_in_dest(in_str):
                    COUNTERS.duplicates += 1
                    continue

            ######## Initiate new file to compute ######
            db.add_image_to_preview(in_str)

            # gather "placeholdered" absolute out path #
            out_str = create_out_str(in_str,out_path_str,out_filename)
            metadatas = db.get_exifs(in_str)

            ################ Format date ###############
            date_str = ""
            if is_guess_date_from_name:
                date_fmt = guess_date_from_name_str
                date_str = ExifTags.get_date_from_name(date_fmt, in_str)
            if not date_str:
                for date_tag in EXIF_DATE_FIELD.values():
                    if date_tag in metadatas:
                        date_str = metadatas[date_tag]
                        break

            if date_str:
                db.add_date_to_preview(in_str, date_str)
            out_str = ExifTags.format_ym(date_str, out_str)

            ############ Try to group by day floating ##########
            if is_group_floating_days:
                db.group_by_n_floating_days(group_floating_days_nb)
                group_date = db.get_date_group(in_str)
                if group_date is not None:
                    group_regex = re.compile(r'{Group}')
                    group_str = group_date.strftime(group_floating_days_fmt)
                    out_str = group_regex.sub(group_str, out_str)


            #################### Format gps ####################
            address_dct = None
            if is_gps:
                #metadata = db.get_metadatas(im_str)
                location = get_image_gps_location(metadatas)
                if location:
                    metadatas.update(location)
                    db.add_location(in_str, location)

            ################ Format others tags ################
            placeholder_regex = re.compile(r'[{<]([^}>]+)[}>]')
            for placeholder in placeholder_regex.findall(out_str):
                tag_value = metadatas.get(placeholder, '')
                out_str = ExifTags.format_tag(out_str, placeholder, tag_value)
            # Rename file with increment if name is duplicate ##
            out_str = rename_with_incr(out_str)

            ##### Save the generated out path to dayabase ######
            db.add_out_path(in_str, out_str)

            progbar.update(i, f"{i} / {nb_files} {Path(in_str).name}")
            COUNTERS.nb_files += 1
            if counterWdg : counterWdg.update(COUNTERS)

    if loop_stop is not None : loop_stop.stop_signal = True

def execute(progbar=cli_progbar, counterWdg=False, loop_stop=None):

    is_control_hash = CFG['control_hash']
    control_dest_duplicates = CFG['hash_populate']
    #is_hash_reset = CFG["hash_reset"]
    in_dir = CFG['in_dir']
    out_dir = CFG['out_dir']
    extentions = CFG["extentions"]
    cameras = CFG['cameras']
    is_gps = CFG['gps']
    recursive = CFG['is_recursive']

    list_files_params = {
        'src_dir' : in_dir,
        'extentions' : extentions,
        'cameras' : cameras,
        'recursive' : recursive,
        'duplicate_md5_data' : is_control_hash
    }

    with ImageMetadataDB() as db:

        COUNTERS.reset()
        nb_files, total_size = db.count(**list_files_params)
        progbar.init(total_size) #progbar.init(nb_files)
        bytes_moved = 0

        for i, in_str in enumerate(db.list_files(**list_files_params)):

            bytes_moved += Path(in_str).stat().st_size

            # PyQt5 loop control
            if loop_stop is not None :
                loop = QEventLoop()
                QTimer.singleShot(0, loop.quit)
                loop.exec_()
                if loop_stop.stop_signal:
                    break

            out_rel_str, out_filename = db.get_out_str(in_str)
            out_str = str(out_dir / out_rel_str / out_filename)
            has_moved = move_file(Path(in_str), Path(out_str))

            if has_moved and is_gps:
                metadatas = db.get_metadatas(in_str)
                location = get_image_gps_location(metadatas)
                if location:
                    with ExifTags(out_str) as im_exif:
                        try:
                            im_exif.add_localisation(location)
                        except NoExifError as e:
                            print("Issue while loading gps, skipping", e)

            #progbar.update(i, in_path.name, out_path.parent.name)
            #print(f"{bytes_moved} / {total_size}")
            progbar.update(bytes_moved, limited_string(f"{bytes2human(bytes_moved)} / {bytes2human(total_size)} - {Path(in_str).name}"), Path(out_str).parent.name)
            COUNTERS.nb_files += 1
            if counterWdg : counterWdg.update(COUNTERS)

    if loop_stop is not None : loop_stop.stop_signal = True

if __name__ == "__main__":
    main()
