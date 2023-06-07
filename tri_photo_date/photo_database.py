import hashlib
import json
import locale
import os
import sqlite3
from pathlib import Path
from datetime import datetime
import re

#import pyexiv2

#from tri_photo_date.gps import get_image_gps_location
from tri_photo_date.exif import ExifTags, EXIF_LOCATION_FIELD, NoExifError, USEFULL_TAG_DESCRIPTION
from tri_photo_date.utils.config_paths import IMAGE_DATABASE_PATH
from tri_photo_date.utils.config_loader import DUP_MD5_FILE, DUP_MD5_DATA, DUP_DATETIME, DIR_EXCLUDE, DIR_INCLUDE
from tri_photo_date.utils.fingerprint import get_data_fingerprint, get_file_fingerprint


def _colliding(filename, item):
    path = Path(filename)
    reg = re.compile(
        path.stem + r"(?:\s\([0-9]+\))?" + path.suffix.lower()
    )
    return reg.search(item) is not None

def _match_reg(reg, item):
    reg = re.compile('.*' + reg + '.*')
    match = reg.search(item)
    return match is not None

class ImageMetadataDB:
    def __init__(self):
        self.db_file = str(IMAGE_DATABASE_PATH)
        self.conn = None

    def __enter__(self):
        # Connect to the SQLite database and create the images table
        self.conn = sqlite3.connect(self.db_file)

        self.conn.create_function("COLLIDE",2,_colliding, deterministic=True)
        self.conn.create_function("MATCH",2,_match_reg, deterministic=True)
        c = self.conn.cursor()

        # Store and cache all scaned file in source folder
        c.execute('''
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
                  PRIMARY KEY (path)
            )
        ''')

        # Store path of image to process
        c.execute('''
            CREATE TABLE IF NOT EXISTS images
              (
                  path text,
                  PRIMARY KEY (path)
              )
        ''')

        # Join the list of images (images) to process and their cached data (images_cache)
        c.execute('''
            CREATE VIEW IF NOT EXISTS
                images_view AS
            SELECT
                images.path,
                images_cache.md5_file,
                images_cache.md5_data,
                images_cache.path,
                images_cache.folder,
                images_cache.filename,
                images_cache.extentions,
                images_cache.date,
                images_cache.camera,
                images_cache.metadata
            FROM
                images
            JOIN
                images_cache
            ON images.path = images_cache.path;''')

        # Store processed data : new image path, location, group
        c.execute('''
            CREATE TABLE IF NOT EXISTS tri_preview
            (
                path text,
                filename text,
                new_folder text,
                new_filename text,
                location text,
                groups text,
                date text,
                FOREIGN KEY (path, filename) REFERENCES images_view(path, filename)
            )''')

        # Store images fingerprints in destination folder
        # /!\ missing date for date comparison for finding duplicate
        c.execute('''
            CREATE TABLE IF NOT EXISTS scan_dest
              (
                  md5_file text,
                  md5_data text,
                  path text,
                  PRIMARY KEY (path)
            )''')

        return self

    def __exit__(self, exc_type, exc_value, traceback):
        # Close the database connection
        self.conn.commit()
        self.conn.close()

    def clean_all_table(self):

        c = self.conn.cursor()
        c.execute("DELETE FROM images")
        c.execute("DELETE FROM tri_preview")
        c.execute("DELETE FROM scan_dest")
        self.conn.commit()

    def clean_preview_table(self):

        c = self.conn.cursor()
        c.execute("DELETE FROM tri_preview")
        self.conn.commit()

    def add_image(self, im_str):
        # Check if file exist in cache
        # Check if md5 file has changed
        # Check if md5 data has changed
        #
        # Get metadata from cache or image
        # Get date and camera from metadata
        #
        # Insert/update db

        c = self.conn.cursor()

        c.execute('''
            SELECT
                md5_file, md5_data
            FROM
                images_cache
            WHERE
                path = ?''',
            (im_str,)
        )
        res = c.fetchone()

        if res:

            db_md5_file, db_md5_data = res

            md5_file = get_file_fingerprint(im_str)
            if db_md5_file == md5_file:
                # md5 hash has not changed, do not update the row
                pass

            md5_data = get_data_fingerprint(im_str)
            if db_md5_data == md5_data:
                # md5 hash has changed, update the row
                try:
                    with ExifTags(im_str) as exifs:
                        metadata = {k:v for k,v in exifs.items() if k in USEFULL_TAG_DESCRIPTION.keys()}
                except NoExifError as e:
                    metadata = {}
                c.execute('''
                    UPDATE
                        images_cache
                    SET
                        md5_file = ?, metadata = ?
                    WHERE
                        path = ?''',
                    (md5_file, json.dumps(metadata), im_str)
                )

            else: # Photo itself had changed, but waht to do????
                try:
                    with ExifTags(im_str) as exifs:
                        metadata = {k:v for k,v in exifs.items() if k in USEFULL_TAG_DESCRIPTION.keys()}

                    date = metadata.get('Exif.Photo.DateTimeOriginal', None)
                    camera = metadata.get('Exif.Image.Model', None)

                except NoExifError as e:
                    metadata = {}
                    date = None
                    camera = None

                c.execute('''
                    UPDATE
                        images_cache
                    SET
                        md5_file = ?, md5_data = ?, metadata = ?, date = ?, camera = ?
                    WHERE path = ?''',
                    (md5_file, md5_data, json.dumps(metadata), date, camera, im_str)
                )
                pass
        else:

            # md5 hash does not exist in the database, insert a new row
            md5_file = get_file_fingerprint(im_str)
            md5_data = get_data_fingerprint(im_str)
            folder = str(Path(im_str).parent)
            filename = Path(im_str).name
            extention = im_str.split('.')[-1].lower()

            try :
                with ExifTags(im_str) as exifs:
                    metadata = {k:v for k,v in exifs.items() if k in USEFULL_TAG_DESCRIPTION.keys()}

                date = metadata.get('Exif.Photo.DateTimeOriginal', None)
                camera = metadata.get('Exif.Image.Model', None)

            except NoExifError as e:
                metadata = {}
                date = None
                camera = None

            image_tuple = (
                md5_file,md5_data,im_str,folder,filename,extention,date,camera,json.dumps(metadata)
            )
            #preview_tuple = (
            #    im_str, filename, None, None, None
            #)
            c.execute("INSERT INTO images_cache VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", image_tuple)
            #c.execute("INSERT INTO tri_preview VALUES (?, ?, ?, ?, ?)", preview_tuple)

        # Add after in case of user interuption during 'add_image'
        c.execute('''INSERT INTO images VALUES (?)''', (im_str,))

        self.conn.commit()

    def scan_dest(self, im_str):
        # Same as add_image but for destination folder

        # Check database
        c = self.conn.cursor()
        c.execute('''
            SELECT
                md5_file, md5_data
            FROM
                scan_dest
            WHERE
                path = ?''',
            (im_str,)
        )
        res = c.fetchone()

        if res:
            db_md5_file, db_md5_data = res
            md5_file = get_file_fingerprint(im_str)

            if db_md5_file == md5_file and db_md5_data == md5_data:
                # md5 hash has not changed, do not update the row
                return

            md5_data = get_data_fingerprint(im_str)
            if db_md5_data == md5_data:
                # md5 hash has changed, update the row
                with ExifTags(im_str) as exifs:
                    metadata = exifs.copy()
                c.execute('''
                    UPDATE
                        scan_dest
                    SET
                        md5_file = ?
                    WHERE
                        path = ?''',
                    (md5_file, json.dumps(metadata), im_str)
                )
            else: # Photo itself had changed, but waht to do????
                with ExifTags(im_str) as exifs:
                    metadata = exifs.copy()
                c.execute('''
                    UPDATE
                        scan_dest
                    SET
                        md5_file = ?, md5_data = ?
                    WHERE
                        path = ?''',
                    (md5_file, md5_data, json.dumps(metadata), im_str)
                )
        else:
            md5_file = get_file_fingerprint(im_str)
            md5_data = get_data_fingerprint(im_str)
            c.execute('''
                INSERT INTO
                    scan_dest
                VALUES
                    (?, ?, ?)''',
                (md5_file, md5_data, im_str)
            )

        self.conn.commit()

#    def exist(self, im_path):
#
#        c= self.conn.cursor()
#        md5_file, md5_data = get_fingerprint(im_path)
#        c.execute(
#            '''SELECT EXISTS(
#                SELECT 1 FROM images_view WHERE md5_file=? LIMIT 1
#            )''',
#            (md5_file,))
#        res = c.fetchone()
#
#        return res[0]

    def count(self, *args, **kwargs):

        nb_files = 0
        nb_bytes = 0

        for f in self.list_files(*args, **kwargs):
            nb_files += 1
            nb_bytes += Path(f).stat().st_size

        return nb_files, nb_bytes

    def count_preview(self):

        nb_files = 0
        nb_bytes = 0

        c = self.conn.cursor()

        c.execute('''
        SELECT
            path
        FROM
            tri_preview
        ''')
        rows = c.fetchall()
        for row in rows:
            f = row[0]
            nb_files += 1
            nb_bytes += Path(f).stat().st_size

        return nb_files, nb_bytes

    def list_files(self, src_dir='', extentions=[], cameras=[], recursive=True, filter_txt='', dup_mode=False, exclude=[]):
        """List files in src_dir applying user filters"""

        src_dir = str(src_dir)

        if not dup_mode:
            cmd = 'SELECT path, md5_file FROM images_view'
        elif dup_mode == DUP_MD5_FILE:
            cmd = "SELECT path, md5_file, MAX(path) FROM images_view"
        elif dup_mode == DUP_MD5_DATA:
            # Prevent missing md5_data
            cmd = "SELECT path, COALESCE(md5_data, md5_file), MAX(path) FROM images_view"
        elif dup_mode == DUP_DATETIME:
            cmd = "SELECT path, date, MAX(path) FROM images_view"

        if not recursive:
            cmd += " " + "WHERE folder = ? AND path LIKE '%' || ? || '%'"
        else:
            cmd += " " + "WHERE folder LIKE ? || '%' AND path LIKE '%' || ? || '%'"
        tup = (src_dir, filter_txt)

        if extentions and extentions[0]:
            cmd += " " + f"AND extentions IN ({','.join('?' for _ in extentions)})"
            tup += (*extentions,)

        if cameras and cameras[0]:
            cmd += " " + f"AND camera IN ({','.join('?' for _ in cameras)})"
            tup += (*cameras,)

        if exclude['dirs'] and exclude['dirs'][0]:
        #if excluded_dirs and excluded_dirs[0]:
            if not exclude['is_regex']:
                excluded_dirs = [os.path.join(src_dir, f) for f in exclude['dirs']]
                #for excl in excluded_dirs:
                if exclude['toggle'] == DIR_EXCLUDE:
                    #cmd += " " + f"AND folder NOT LIKE ? || '%'"
                    cmd += " AND NOT ( folder LIKE ? || '%' " + "OR folder LIKE ? || '%' " * (len(excluded_dirs)-1)
                elif exclude['toggle'] == DIR_INCLUDE:
                    #cmd += " " + f"AND folder LIKE ? || '%'"
                    cmd += " AND ( folder LIKE ? || '%' " + "OR folder LIKE ? || '%' " * (len(excluded_dirs)-1)
                for excl in excluded_dirs:
                    tup += ('/' + excl.strip('/'),)
                cmd += ') '
            else:
                if exclude['toggle'] == DIR_EXCLUDE:
                    cmd += " " + 'AND NOT MATCH(?,folder)'
                elif exclude['toggle'] == DIR_INCLUDE:
                    cmd += " " + 'AND MATCH(?,folder)'
                tup += ('|'.join(exclude['dirs']),)

        if not dup_mode:
            pass
        elif dup_mode == DUP_MD5_FILE:
            cmd += ' ' + 'GROUP BY md5_file'
        elif dup_mode == DUP_MD5_DATA:
            cmd += ' ' + 'GROUP BY COALESCE(md5_data, md5_file)'
        elif dup_mode == DUP_DATETIME:
            cmd += ' ' + 'GROUP BY date'

        c= self.conn.cursor()
        print(cmd,'\n',tup)
        c.execute(cmd, tup)

        while row := c.fetchone():
            yield row[0]

    def exist_in_dest(self, in_str, dup_mode):

        c = self.conn.cursor()

        if dup_mode == DUP_MD5_FILE:
            query = "SELECT  md5_file FROM images_view WHERE path = ?"
        elif dup_mode == DUP_MD5_DATA:
            # Prevent missing md5_data
            query = "SELECT COALESCE(md5_data, md5_file) FROM images_view WHERE path = ?"
        elif dup_mode == DUP_DATETIME:
            query = "SELECT date FROM images_view WHERE path = ?"

        c.execute(query, (in_str,))
        res = c.fetchone()

        if dup_mode == DUP_MD5_FILE:
            query = "SELECT * FROM scan_dest WHERE md5_file = ?"
        elif dup_mode == DUP_MD5_DATA:
            # Prevent missing md5_dat
            query = "SELECT * FROM scan_dest WHERE COALESCE(md5_data, md5_file) = ?"
        elif dup_mode == DUP_DATETIME:
            print("Can't check date in destination folder, not implemented yet.")
            return False
            #query = "SELECT * FROM scan_dest WHERE date = ?"

        c.execute(query, res)

        return bool(c.fetchone())

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
            date_str=None

        preview_tuple = (
            in_str, filename, new_folder, new_filename, disp_name, None, date_str
        )

        c.execute("""
            INSERT INTO
                tri_preview
            VALUES
                (?, ?, ?, ?, ?, ?, ?)""",
            preview_tuple
        )

        self.conn.commit()

    def get_exifs(self, im_path):

        c= self.conn.cursor()
        c.execute(
            '''SELECT metadata FROM images_view WHERE path=?''',
            (im_path,)
        )
        res = c.fetchone()
        return json.loads(res[0])

    def add_date_to_preview(self, in_str,  date_str):

        c = self.conn.cursor()

        c.execute("""
            UPDATE
                tri_preview
            SET
                date = ?
            WHERE
                path = ?
            """,
            (date_str, in_str)
        )

    def add_location(self, im_str, location_metadata):

        c = self.conn.cursor()
        # Update all metadatas in images
        metadatas = self.get_exifs(im_str)
        metadatas.update(location_metadata)
        c = self.conn.cursor()
        c.execute('''
            UPDATE
                images_cache
            SET
                metadata = ?
            WHERE
                path = ?''',
            (json.dumps(metadatas), im_str)

        )
        self.conn.commit()

#        disp_name = location_metadata[EXIF_LOCATION_FIELD["display_name"]]
#        # Put in preview windows
#        c.execute('''
#            UPDATE
#                tri_preview
#            SET
#                location = ?
#            WHERE
#                path = ?''',
#            (json.dumps(disp_name), im_str)
#        )

    def exist_in_preview(self, im_path):

        new_folder = str(im_path.parent)
        new_filename = str(im_path.name)

        c= self.conn.cursor()

        query = 'SELECT new_filename FROM tri_preview WHERE new_folder = ? AND COLLIDE(?,new_filename)'
        #query = 'SELECT new_filename FROM tri_preview WHERE new_folder = ? AND new_filename REGEXP ? '

        c.execute(query, (new_folder, new_filename,))

        #return [row[0] for row in c.fetchall()]
        while row := c.fetchone() :
            yield row[0]

    def add_out_path(self, in_str, out_str):

        out_path = Path(out_str)
        new_folder = str(out_path.parent)
        new_filename = str(out_path.name)

        c = self.conn.cursor()
        c.execute('''
            UPDATE
                tri_preview
            SET
                new_folder = ?, new_filename = ?
            WHERE
                path = ?''',
            (new_folder, new_filename, in_str)
        )
        self.conn.commit()

    def group_by_n_floating_days(self, n=6):

        c = self.conn.cursor()

        c.execute("""
            SELECT
                path, date
            FROM
                tri_preview
            ORDER BY
                date""")
        #res = c.fetchall()
        # Group the dates by 6-day intervals
        date_fmt = r"%Y:%m:%d %H:%M:%S"
        prev_date = None #datetime.strptime('1900:01:01 00:00:00', date_fmt)#None
        grp_date = None #datetime.strptime('1900:01:01 00:00:00', date_fmt)#None

        for path, date_str in c.fetchall():
            if date_str is None:
                continue
            date = datetime.strptime(date_str, date_fmt)
            if prev_date is None:
                grp_date = date
            elif (date - prev_date).days < n:
                pass
            else:
                grp_date = date
            self.set_group_preview(path, datetime.strftime(grp_date, date_fmt))
            prev_date = date

    def get_date_group(self, im_str):

        c = self.conn.cursor()

        c.execute('''
            SELECT
                groups
            FROM
                tri_preview
            WHERE
                path = ?''',
            (im_str,)
        )
        res = c.fetchone()
        date_fmt = r"%Y:%m:%d %H:%M:%S"

        if res is None or res[0] is None:
            return None
        return datetime.strptime(res[0], date_fmt)

    def get_out_str(self, in_str):

        c = self.conn.cursor()

        c.execute('''
            SELECT
                new_folder, new_filename
            FROM
                tri_preview
            WHERE
                path = ?''',
            (in_str,)
        )
        res = c.fetchone()
        if res:
            return res

    def get_metadatas(self, im_path):

        return self.get_exifs(im_path)

    def get_location(self, im_str):

        c = self.conn.cursor()

        c.execute('''
            SELECT
                location
            FROM
                tri_preview
            WHERE
                path = ?''',
            (im_str,)
        )
        res = c.fetchone()
        if res is not None and res[0] is not None:
            return json.loads(res[0])

    def set_group_preview(self, path, date):

        c = self.conn.cursor()

        c.execute("""
            UPDATE
                tri_preview
            SET
                groups = ?
            WHERE
                path = ?
            """,
            (date, path)
        )
        self.conn.commit()

    def get_camera_list(self):

        c= self.conn.cursor()
        c.execute(
            '''SELECT DISTINCT camera FROM images_view'''
        )
        res = c.fetchall()
        if not res:
            return []
        return [r[0] for r in res if r[0] is not None]

    def get_tag_list(self):

        c= self.conn.cursor()
        c.execute(
            '''SELECT metadata FROM images_view'''
        )

        exifs_all = set()
        while row := c.fetchone():
            exifs_all.update(list(json.loads(row[0]).keys()))

        c.execute(
            '''SELECT metadata FROM images_view'''
        )

        exifs_common = set()
        while row := c.fetchone():
            exifs_common.intersection_update(list(json.loads(row[0]).keys()))

        return exifs_all, exifs_common

    def get_extention_list(self):

        c= self.conn.cursor()
        c.execute(
            '''SELECT DISTINCT extentions FROM images_view'''
        )
        res = c.fetchall()
        return [r[0] for r in res]

    def get_preview_files(self, filter_txt=''):#, paths):

        #paths = list(paths)
        c = self.conn.cursor()
        #placeholders = ','.join('?' for _ in paths)
        #query = f"SELECT * FROM tri_preview WHERE path IN ({placeholders})"
        query = f"SELECT path FROM tri_preview;"
        c.execute(query)

        while row := c.fetchone():
            yield row[0]

    def get_preview(self, filter_txt=''):#, paths):

        #paths = list(paths)
        c = self.conn.cursor()
        #placeholders = ','.join('?' for _ in paths)
        #query = f"SELECT * FROM tri_preview WHERE path IN ({placeholders})"
        query = f"SELECT * FROM tri_preview WHERE path LIKE '%' || ? || '%';"
        c.execute(query, (filter_txt,))

        while row := c.fetchone():
            yield row

#    def get_file_list_preview(self):
#        c = self.conn.cursor()
#        c.execute('''
#                SELECT new_folder, new_filename FROM tri_preview
#                '''
#                  )
#        return c.fetchall()

#    def populate_database(self):
#        # Loop through each image in the images directory
#        for root, dirs, files in os.walk(self.images_dir):
#            for file in files:
#                # Only process image files
#                if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tif', '.tiff')):
#                    # Calculate the MD5 hash of the image file
#                    path = os.path.join(root, file)
#                    with open(path, 'rb') as f:
#                        image_data = f.read()
#                        md5sum = hashlib.md5(image_data).hexdigest()
#
#                    # Read the image metadata using pyexiv2
#                    metadata = pyexiv2.ImageMetadata(path)
#                    metadata.read()
#                    name = metadata.get('Xmp.dc.title')
#                    date = metadata.get('Exif.Photo.DateTimeOriginal')
#                    camera = metadata.get('Exif.Image.Model')
#                    metadata_dict = {}
#                    for key, value in metadata.items():
#                        metadata_dict[key] = str(value.raw_value)
#
#                    # Insert the image metadata into the SQLite database
#                    image_tuple = (md5sum, name, date, camera, str(metadata_dict))
#                    c = self.conn.cursor()
#                    c.execute("INSERT INTO images VALUES (?, ?, ?, ?, ?)", image_tuple)
#                    self.conn.commit()
#
