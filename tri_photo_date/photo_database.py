import hashlib
import json
import locale
import os
import sqlite3
from pathlib import Path
from datetime import datetime
import re

# import pyexiv2

# from tri_photo_date.gps import get_image_gps_location
from tri_photo_date.exif import (
    ExifTags,
    EXIF_LOCATION_FIELD,
    NoExifError,
    USEFULL_TAG_DESCRIPTION,
)
from tri_photo_date.config.config_loader import IMAGE_DATABASE_PATH
from tri_photo_date.utils.constants import (
    DUP_MD5_FILE,
    DUP_MD5_DATA,
    DUP_DATETIME,
    DIR_EXCLUDE,
    DIR_INCLUDE,
    DUP_PROCEDURE_KEEP_FIRST,
    DUP_PROCEDURE_MOVE_APART,
)

from tri_photo_date.utils.fingerprint import get_data_fingerprint, get_file_fingerprint

global GLOBAL_COUNT
GLOBAL_COUNT = 0

def _colliding(filename, item):
    global GLOBAL_COUNT
    GLOBAL_COUNT += 1
#    print(GLOBAL_COUNT)
#    print("collide call")
    path = Path(filename)
    reg = re.compile(path.stem + r"(?:\s\([0-9]+\))?" + path.suffix.lower())
    return reg.search(item) is not None


def _match_reg(reg, item):
    reg = re.compile(".*" + reg + ".*")
    match = reg.search(item)
    return match is not None


def get_image_metadatas(im_str):
    try:
        with ExifTags(im_str) as exifs:
            metadata = {
                k: v for k, v in exifs.items() if k in USEFULL_TAG_DESCRIPTION.keys()
            }
    except NoExifError as e:
        metadata = {}

    date = metadata.get("Exif.Photo.DateTimeOriginal", False)
    date = date.strip() if date else None

    camera = metadata.get("Exif.Image.Model", False)
    camera = camera.strip() if camera else None

    return metadata, date, camera


class ImageMetadataDB:
    def __init__(self):
        self.db_file = str(IMAGE_DATABASE_PATH)
        self.conn = None

    def __enter__(self):
        # Connect to the SQLite database and create the images table
        self.conn = sqlite3.connect(self.db_file)

        self.conn.create_function("COLLIDE", 2, _colliding, deterministic=True)
        self.conn.create_function("MATCH", 2, _match_reg, deterministic=True)
        c = self.conn.cursor()

        # Store and cache all scaned file in source folder
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS images_cache
              (
                  md5_file text,
                  md5_data text,
                  path text,
                  folder text,
                  filename text,
                  extentions text,
                  date text,
                  camera text,
                  metadata text,
                  st_size int,
                  PRIMARY KEY (path)
            )
        """
        )

        # Store path of image to process
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS images_to_process
              (
                  path text,
                  PRIMARY KEY (path)
              )
        """
        )

        # Join the list of images (images) to process and their cached data (images_cache)
        c.execute(
            """
            CREATE VIEW IF NOT EXISTS
                images_to_process_view AS
            SELECT
                images_to_process.path,
                images_cache.md5_file,
                images_cache.md5_data,
                images_cache.path,
                images_cache.folder,
                images_cache.filename,
                images_cache.extentions,
                images_cache.date,
                images_cache.camera,
                images_cache.metadata,
                images_cache.st_size
            FROM
                images_to_process
            JOIN
                images_cache
            ON images_to_process.path = images_cache.path;"""
        )

        # Store path of duplicates in "move to separated folder mode"
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS duplicates
              (
                  path text,
                  new_filename text,
                  PRIMARY KEY (path)
              )
        """
        )
        c.execute(
            """
            CREATE VIEW IF NOT EXISTS
                duplicates_view AS
            SELECT
                duplicates.path,
                images_cache.folder,
                images_cache.filename,
                duplicates.new_filename,
                images_cache.md5_file,
                images_cache.md5_data,
                images_cache.date,
                images_cache.camera
            FROM
                duplicates
            JOIN
                images_cache
            ON duplicates.path = images_cache.path;"""
        )

        # Store processed data : new image path, location, group
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS process_preview
            (
                path text,
                filename text,
                new_folder text,
                new_filename text,
                location text,
                groups text,
                date text,
                FOREIGN KEY (path, filename) REFERENCES images_to_process_view(path, filename)
            )"""
        )

        # Store images fingerprints in destination folder
        # /!\ missing date for date comparison for finding duplicate
        c.execute(
            """
            CREATE TABLE IF NOT EXISTS images_in_dest
              (
                  path text,
                  PRIMARY KEY (path)
            )"""
        )

        c.execute(
            """
            CREATE VIEW IF NOT EXISTS
                images_in_dest_view AS
            SELECT
                images_in_dest.path,
                images_cache.md5_file,
                images_cache.md5_data,
                images_cache.path,
                images_cache.folder,
                images_cache.filename,
                images_cache.extentions,
                images_cache.date,
                images_cache.camera,
                images_cache.metadata,
                images_cache.st_size
            FROM
                images_in_dest
            JOIN
                images_cache
            ON images_in_dest.path = images_cache.path;"""
        )

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Close the database connection
        self.conn.commit()
        self.conn.close()

    def clean_all_table(self):
        c = self.conn.cursor()
        c.execute("DELETE FROM images_to_process")
        c.execute("DELETE FROM process_preview")
        c.execute("DELETE FROM images_in_dest")
        self.conn.commit()

    def clean_preview_table(self):
        c = self.conn.cursor()
        c.execute("DELETE FROM process_preview")
        c.execute("DELETE FROM duplicates")
        self.conn.commit()

    def get_image_fingerprint(self, im_str):
        c = self.conn.cursor()

        c.execute(
            """
            SELECT md5_file, md5_data
            FROM images_cache
            WHERE path = ?""",
            (im_str,),
        )

        return c.fetchone()

    def get_file_size(self, im_str):
        c = self.conn.cursor()

        c.execute(
            """
            SELECT st_size
            FROM images_cache
            WHERE path = ?""",
            (im_str,),
        )

        return c.fetchone()[0]

    def add_image_to_scanned_list(self, im_str):
        c = self.conn.cursor()
        c.execute("""INSERT INTO images_to_process VALUES (?)""", (im_str,))
        self.conn.commit()

    def add_image_to_scanned_dest_list(self, im_str):
        c = self.conn.cursor()
        c.execute("""INSERT INTO images_in_dest VALUES (?)""", (im_str,))
        self.conn.commit()

    # def set_image_cache_metadatas(self, im_str, md5_file,  metadata):

    #    c = self.conn.cursor()
    #    c.execute(
    #        """
    #        UPDATE images_cache
    #        SET md5_file = ?, metadata = ?
    #        WHERE path = ?""",
    #        (md5_file, json.dumps(metadata), im_str),
    #    )

    #    self.conn.commit()

    def set_image_cache_values(self, im_str, **kwargs):
        query = "UPDATE images_cache SET {} WHERE path = ?".format(
            ", ".join(f"{row} = ?" for row in kwargs.keys())
        )

        values = list(kwargs.values()) + [im_str]

        c = self.conn.cursor()
        c.execute(query, values)
        self.conn.commit()

    def update_cache(self, im_str, db_md5_file, db_md5_data):
        # no changes
        if (md5_file := get_file_fingerprint(im_str)) == db_md5_file:
            pass

        # metadatas changed
        elif (md5_data := get_data_fingerprint(im_str)) == db_md5_data:
            metadata, date, camera = get_image_metadatas(im_str)
            st_size = Path(im_str).stat().st_size
            values_to_set = {
                "md5_file": md5_file,
                "metadata": json.dumps(metadata),
                "date": date,
                "camera": camera,
                "st_size": st_size,
            }
            self.set_image_cache_values(im_str, **values_to_set)

        # even data changed (copletly new image or something like cropped)
        else:
            metadata, date, camera = get_image_metadatas(im_str)
            st_size = Path(im_str).stat().st_size
            values_to_set = {
                "md5_file": md5_file,
                "md5_data": md5_data,
                "metadata": json.dumps(metadata),
                "date": date,
                "camera": camera,
                "st_size": st_size,
            }
            self.set_image_cache_values(im_str, **values_to_set)

    def set_cache(self, im_str):
        md5_file = get_file_fingerprint(im_str)
        md5_data = get_data_fingerprint(im_str)
        folder = str(Path(im_str).parent)
        filename = Path(im_str).name
        extention = im_str.split(".")[-1].lower()

        metadata, date, camera = get_image_metadatas(im_str)
        st_size = Path(im_str).stat().st_size

        image_tuple = (
            md5_file,
            md5_data,
            im_str,
            folder,
            filename,
            extention,
            date,
            camera,
            json.dumps(metadata),
            st_size,
        )
        # preview_tuple = (
        #    im_str, filename, None, None, None
        # )
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO images_cache VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            image_tuple,
        )
        self.conn.commit()

    def add_image(self, im_str, to_process=True, is_use_cache=False):
        cached_fingerprints = self.get_image_fingerprint(im_str)

        if cached_fingerprints and is_use_cache:  # force cache
            pass
        elif cached_fingerprints:  # exist in db
            self.update_cache(im_str, *cached_fingerprints)
        else:
            self.set_cache(im_str)

        if to_process:
            self.add_image_to_scanned_list(im_str)
        else:
            self.add_image_to_scanned_dest_list(im_str)

    # def scan_dest(self, im_str, is_use_cache=False):
    #     # Same as add_image but for destination folder

    #     cached_fingerprints = self.get_image_fingerprint(im_str)

    #     if cached_fingerprints and is_use_cache: # force cache
    #         pass
    #     elif cached_fingerprints: # exist in db
    #         self.update_cache(im_str, *cached_fingerprints)
    #     else:
    #         self.set_cache(im_str)

    def count(self, *args, **kwargs):
        nb_files = 0
        nb_bytes = 0

        for f in self.list_files(*args, **kwargs):
            nb_files += 1
            nb_bytes += self.get_file_size(f)  # Path(f).stat().st_size

        return nb_files, nb_bytes

    def count_preview(self):
        nb_files = 0
        nb_bytes = 0

        c = self.conn.cursor()

        c.execute(
            """
        SELECT
            path
        FROM
            process_preview
        """
        )
        rows = c.fetchall()
        for row in rows:
            f = row[0]
            nb_files += 1
            nb_bytes += Path(f).stat().st_size

        return nb_files, nb_bytes

    def list_files(
        self,
        dir="",
        extentions=[],
        exclude_cameras={},
        recursive=True,
        filter_txt="",
        dup_procedure=DUP_PROCEDURE_KEEP_FIRST,
        dup_mode=False,
        exclude={},
        is_list_duplicates=False
    ):
        """List files in dir applying user filters"""

        dir = str(dir)

        if dup_procedure == DUP_PROCEDURE_KEEP_FIRST: # Keep only one
            if not dup_mode:
                selection = "md5-file"
            elif dup_mode == DUP_MD5_FILE:
                selection = "md5_file, MAX(path)"
            elif dup_mode == DUP_MD5_DATA:
                selection = "COALESCE(md5_data, md5_file), MAX(path)"
            elif dup_mode == DUP_DATETIME:
                selection = "date, MAX(path)"
        elif dup_procedure == DUP_PROCEDURE_MOVE_APART:
            if not dup_mode:
                selection= "md5_file"
            elif dup_mode == DUP_MD5_FILE:
                selection = "md5_file"
            elif dup_mode == DUP_MD5_DATA:
                selection = "md5_data"
            elif dup_mode == DUP_DATETIME:
                selection = "date"
        cmd_prefix = f"{selection} FROM images_to_process_view WHERE "

        cmd_filters = " "
        if not recursive:
            cmd_filters += "folder = ? AND path LIKE '%' || ? || '%'"
        else:
            cmd_filters += "folder LIKE ? || '%' AND path LIKE '%' || ? || '%'"
        tup = (dir, filter_txt)

        if extentions and extentions[0]:
            cmd_filters += " " + f"AND extentions IN ({','.join('?' for _ in extentions)})"
            tup += (*extentions,)

        if exclude_cameras['cams'] and exclude_cameras['cams'][0]:
            cameras = exclude_cameras['cams']
            if exclude_cameras['toggle'] == DIR_EXCLUDE:
                cmd_filters += " " + f"AND NOT ( camera IN ({','.join('?' for _ in cameras)}) ) "
            elif exclude_cameras['toggle'] == DIR_INCLUDE:
                cmd_filters += " " + f"AND camera IN ({','.join('?' for _ in cameras)}) "
            tup += (*cameras,)

        if exclude["dirs"] and exclude["dirs"][0]:
            # if excluded_dirs and excluded_dirs[0]:
            if not exclude["is_regex"]:
                excluded_dirs = [os.path.join(dir, f) for f in exclude["dirs"]]
                # for excl in excluded_dirs:
                if exclude["toggle"] == DIR_EXCLUDE:
                    # cmd += " " + f"AND path NOT LIKE ? || '%'"
                    cmd_filters += (
                        " AND NOT ( path LIKE ? || '%' "
                        + "OR path LIKE ? || '%' " * (len(excluded_dirs) - 1)
                    )
                elif exclude["toggle"] == DIR_INCLUDE:
                    # cmd += " " + f"AND path LIKE ? || '%'"
                    cmd_filters += (
                        " AND ( path LIKE ? || '%' "
                        + "OR path LIKE ? || '%' " * (len(excluded_dirs) - 1)
                    )
                for excl in excluded_dirs:
                    tup += ("/" + excl.strip("/"),)
                cmd_filters += ") "
            else:
                if exclude["toggle"] == DIR_EXCLUDE:
                    cmd_filters += " " + "AND NOT MATCH(?,path)"
                elif exclude["toggle"] == DIR_INCLUDE:
                    cmd_filters += " " + "AND MATCH(?,path)"
                tup += ("|".join(exclude["dirs"]),)

        cmd_suffix = " "
        if dup_procedure == DUP_PROCEDURE_KEEP_FIRST and not is_list_duplicates:
            if not dup_mode:
                pass
            elif dup_mode == DUP_MD5_FILE:
                cmd_suffix += " " + "GROUP BY md5_file"
            elif dup_mode == DUP_MD5_DATA:
                cmd_suffix += " " + "GROUP BY COALESCE(md5_data, md5_file)"
            elif dup_mode == DUP_DATETIME:
                cmd_suffix += " " + "GROUP BY date"
            cmd = "SELECT path, " + cmd_prefix + cmd_filters + cmd_suffix
        elif dup_procedure == DUP_PROCEDURE_MOVE_APART:
            if not is_list_duplicates:
                if not dup_mode:
                    pass
                elif dup_mode == DUP_MD5_FILE:
                    cmd_suffix += " " + "GROUP BY md5_file HAVING COUNT(*)=1"
                elif dup_mode == DUP_MD5_DATA:
                    cmd_suffix += " " + "GROUP BY COALESCE(md5_data, md5_file) HAVING COUNT(*)=1"
                elif dup_mode == DUP_DATETIME:
                    cmd_suffix += " " + "GROUP BY date HAVING COUNT(*)=1"
                cmd = "SELECT path, " + cmd_prefix + cmd_filters + cmd_suffix
            else:
                if not dup_mode:
                    pass
                elif dup_mode == DUP_MD5_FILE:
                    cmd_suffix += " " + "GROUP BY md5_file HAVING COUNT(*)>1"
                elif dup_mode == DUP_MD5_DATA:
                    cmd_suffix += " " + "GROUP BY COALESCE(md5_data, md5_file) HAVING COUNT(*)>1"
                elif dup_mode == DUP_DATETIME:
                    cmd_suffix += " " + "GROUP BY date HAVING COUNT(*)>1"
                cmd = "SELECT path, " + cmd_prefix + selection + " IN " + '(' + "SELECT " +  cmd_prefix + cmd_filters + cmd_suffix + ') AND ' + cmd_filters
                tup = 2 * tup


        c = self.conn.cursor()
        print(cmd)
        c.execute(cmd, tup)

        while row := c.fetchone():
            yield row[0]

    def list_duplicates(self, *args, **kwargs):

        return self.list_files(*args, **kwargs, is_list_duplicates=True)

    def exist_in_dest(self, in_str, dup_mode):
        c = self.conn.cursor()

        if dup_mode == DUP_MD5_FILE:
            query = "SELECT  md5_file FROM images_to_process_view WHERE path = ?"
        elif dup_mode == DUP_MD5_DATA:
            # Prevent missing md5_data
            query = "SELECT COALESCE(md5_data, md5_file) FROM images_to_process_view WHERE path = ?"
        elif dup_mode == DUP_DATETIME:
            query = "SELECT date FROM images_to_process_view WHERE path = ?"

        c.execute(query, (in_str,))
        res = c.fetchone()

        if dup_mode == DUP_MD5_FILE:
            query = "SELECT * FROM images_in_dest_view WHERE md5_file = ?"
        elif dup_mode == DUP_MD5_DATA:
            # Prevent missing md5_dat
            query = "SELECT * FROM images_in_dest_view WHERE COALESCE(md5_data, md5_file) = ?"
        elif dup_mode == DUP_DATETIME:
            print("Can't check date in destination folder, not implemented yet.")
            return False
            # query = "SELECT * FROM images_in_dest_view WHERE date = ?"

        c.execute(query, res)

        return bool(c.fetchone())

    def add_image_to_duplicates(self, in_str, new_filename):
        c = self.conn.cursor()

        c.execute(
            """
            INSERT INTO
                duplicates
            VALUES
                (?,?)""",
            (in_str, new_filename)
        )

        self.conn.commit()

    def add_image_to_preview(self, in_str, out_str, location, date_str):
        c = self.conn.cursor()

        path = in_str
        filename = Path(in_str).name

        out_path = Path(out_str)
        new_folder = str(out_path.parent)
        new_filename = str(out_path.name)

        if location is not None:
            disp_name = location[EXIF_LOCATION_FIELD["display_name"]]
        else:
            disp_name = None

        if not date_str:
            date_str = None

        preview_tuple = (
            in_str,
            filename,
            new_folder,
            new_filename,
            disp_name,
            None,
            date_str,
        )

        c.execute(
            """
            INSERT INTO
                process_preview
            VALUES
                (?, ?, ?, ?, ?, ?, ?)""",
            preview_tuple,
        )

        self.conn.commit()

    def get_exifs(self, im_path):
        c = self.conn.cursor()
        c.execute(
            """SELECT metadata FROM images_to_process_view WHERE path=?""", (im_path,)
        )
        res = c.fetchone()
        return json.loads(res[0])

    def add_date_to_preview(self, in_str, date_str):
        c = self.conn.cursor()

        c.execute(
            """
            UPDATE
                process_preview
            SET
                date = ?
            WHERE
                path = ?
            """,
            (date_str, in_str),
        )

    def add_location(self, im_str, location_metadata):
        c = self.conn.cursor()
        # Update all metadatas in images
        metadatas = self.get_exifs(im_str)
        metadatas.update(location_metadata)
        c = self.conn.cursor()
        c.execute(
            """
            UPDATE
                images_cache
            SET
                metadata = ?
            WHERE
                path = ?""",
            (json.dumps(metadatas), im_str),
        )
        self.conn.commit()

    #        disp_name = location_metadata[EXIF_LOCATION_FIELD["display_name"]]
    #        # Put in preview windows
    #        c.execute('''
    #            UPDATE
    #                process_preview
    #            SET
    #                location = ?
    #            WHERE
    #                path = ?''',
    #            (json.dumps(disp_name), im_str)
    #        )

    def exist_in_preview(self, im_path):
        # too much call to collide
        new_folder = str(im_path.parent)
        new_filename = str(im_path.name)

        c = self.conn.cursor()

        query = "SELECT new_filename FROM process_preview WHERE new_folder = ?" # AND COLLIDE(?,new_filename)"
        c.execute(
            query,
            (
                new_folder,
            ),
        )

        filenames = c.fetchall()
        reg = re.compile(im_path.stem + r"(?:\s\(([0-9]+)\){0,1})?" + im_path.suffix.lower())

        for filename,*_ in filenames:
            match = reg.fullmatch(filename)
            if match is not None:
                yield int(match.group(1) or 0)

    def exist_in_duplicates(self, new_filename):
        # too much call to collide
        new_filename = Path(new_filename)

        c = self.conn.cursor()

        query = "SELECT new_filename FROM duplicates"
        c.execute(query)

        filenames = c.fetchall()
        reg = re.compile(new_filename.stem + r"(?:\s\(([0-9]+)\){0,1})?" + new_filename.suffix.lower())

        for filename,*_ in filenames:
            match = reg.fullmatch(filename)
            if match is not None:
                yield int(match.group(1) or 0)

    def add_out_path(self, in_str, out_str):
        out_path = Path(out_str)
        new_folder = str(out_path.parent)
        new_filename = str(out_path.name)

        c = self.conn.cursor()
        c.execute(
            """
            UPDATE
                process_preview
            SET
                new_folder = ?, new_filename = ?
            WHERE
                path = ?""",
            (new_folder, new_filename, in_str),
        )
        self.conn.commit()

    def group_by_n_floating_days(self, n=6):
        c = self.conn.cursor()

        c.execute(
            """
            SELECT
                path, date
            FROM
                process_preview
            ORDER BY
                date"""
        )
        # res = c.fetchall()
        # Group the dates by 6-day intervals
        date_fmt = r"%Y:%m:%d %H:%M:%S"
        prev_date = None  # datetime.strptime('1900:01:01 00:00:00', date_fmt)#None
        grp_date = None  # datetime.strptime('1900:01:01 00:00:00', date_fmt)#None

        for path, date_str in c.fetchall():
            if date_str is None:
                continue
            date = datetime.strptime(date_str, date_fmt)
            if prev_date is None:
                grp_date = date
            elif (date - prev_date).days < n:
                pass
            else:  # new group
                grp_date = date
            self.set_group_preview(path, datetime.strftime(grp_date, date_fmt))
            prev_date = date

    def get_date_group(self, im_str):
        c = self.conn.cursor()

        c.execute(
            """
            SELECT
                groups
            FROM
                process_preview
            WHERE
                path = ?""",
            (im_str,),
        )
        res = c.fetchone()
        date_fmt = r"%Y:%m:%d %H:%M:%S"

        if res is None or res[0] is None:
            return None
        return datetime.strptime(res[0], date_fmt)

    def get_out_str(self, in_str):
        c = self.conn.cursor()

        c.execute(
            """
            SELECT
                new_folder, new_filename
            FROM
                process_preview
            WHERE
                path = ?""",
            (in_str,),
        )
        res = c.fetchone()
        if res:
            return res

    # def get_metadatas(self, im_path):
    #    return self.get_exifs(im_path)

    def get_location(self, im_str):
        c = self.conn.cursor()

        c.execute(
            """
            SELECT
                location
            FROM
                process_preview
            WHERE
                path = ?""",
            (im_str,),
        )
        res = c.fetchone()
        if res is not None and res[0] is not None:
            return json.loads(res[0])

    def set_group_preview(self, path, date):
        c = self.conn.cursor()

        c.execute(
            """
            UPDATE
                process_preview
            SET
                groups = ?
            WHERE
                path = ?
            """,
            (date, path),
        )
        self.conn.commit()

    def get_camera_list(self):
        c = self.conn.cursor()
        c.execute("""SELECT DISTINCT camera FROM images_to_process_view""")
        res = c.fetchall()
        if not res:
            return []
        return [r[0] for r in res if r[0] is not None]

    def get_tag_list(self):
        c = self.conn.cursor()
        c.execute("""SELECT metadata FROM images_to_process_view""")

        exifs_all = set()
        while row := c.fetchone():
            exifs_all.update(list(json.loads(row[0]).keys()))

        c.execute("""SELECT metadata FROM images_to_process_view""")

        exifs_common = set()
        while row := c.fetchone():
            exifs_common.intersection_update(list(json.loads(row[0]).keys()))

        return exifs_all, exifs_common

    def get_extention_list(self):
        c = self.conn.cursor()
        c.execute("""SELECT DISTINCT extentions FROM images_to_process_view""")
        res = c.fetchall()
        return [r[0] for r in res]

    def get_preview_files(self, filter_txt=""):  # , paths):
        # paths = list(paths)
        c = self.conn.cursor()
        # placeholders = ','.join('?' for _ in paths)
        # query = f"SELECT * FROM process_preview WHERE path IN ({placeholders})"
        query = f"SELECT path FROM process_preview;"
        c.execute(query)

        while row := c.fetchone():
            yield row[0]

    def get_duplicates_files(self, filter_txt=""):  # , paths):
        # paths = list(paths)
        c = self.conn.cursor()
        # placeholders = ','.join('?' for _ in paths)
        # query = f"SELECT * FROM process_preview WHERE path IN ({placeholders})"
        query = f"SELECT path, new_filename FROM duplicates;"
        c.execute(query)

        while row := c.fetchone():
            yield row

    def get_images_to_process(self, filter_txt=""):  # , paths):
        # paths = list(paths)
        c = self.conn.cursor()
        # placeholders = ','.join('?' for _ in paths)
        # query = f"SELECT * FROM process_preview WHERE path IN ({placeholders})"
        query = f"SELECT folder, filename, camera FROM images_to_process_view WHERE path LIKE '%' || ? || '%';"
        c.execute(query, (filter_txt,))

        while row := c.fetchone():
            yield row

    def get_duplicates(self, filter_txt=""):  # , paths):
        # paths = list(paths)
        c = self.conn.cursor()
        # placeholders = ','.join('?' for _ in paths)
        # query = f"SELECT * FROM process_preview WHERE path IN ({placeholders})"
        query = f"SELECT folder, filename, md5_file, md5_data, date, camera FROM duplicates_view WHERE path LIKE '%' || ? || '%';"
        c.execute(query, (filter_txt,))

        while row := c.fetchone():
            yield row

    def get_preview(self, filter_txt=""):  # , paths):
        # paths = list(paths)
        c = self.conn.cursor()
        # placeholders = ','.join('?' for _ in paths)
        # query = f"SELECT * FROM process_preview WHERE path IN ({placeholders})"
        query = f"SELECT * FROM process_preview WHERE path LIKE '%' || ? || '%';"
        c.execute(query, (filter_txt,))

        while row := c.fetchone():
            yield row
