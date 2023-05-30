import hashlib
import json
import locale
import os
import sqlite3
from pathlib import Path
from datetime import datetime

import PIL
from PIL import Image
#import pyexiv2

#from tri_photo_date.gps import get_image_gps_location
from tri_photo_date.exif import ExifTags, EXIF_LOCATION_FIELD, NoExifError
from tri_photo_date.utils.config_paths import IMAGE_DATABASE_PATH

def get_fingerprint(im_path):

    try:
        with Image.open(im_path) as img:
            md5_data = hashlib.md5()
            while chunk := img.fp.read(4096):
                md5_data.update(chunk)

        with open(im_path, 'rb') as f:
            md5_file = hashlib.md5()
            while chunk := f.read(4096):
                md5_file.update(chunk)

        return md5_file.hexdigest(), md5_data.hexdigest()
    except PIL.UnidentifiedImageError as e:
        return None, None

#def compare_images(image_path1, image_path2):
#    # Open the images
#    image1 = Image.open(image_path1)
#    image2 = Image.open(image_path2)
#
#    # Get the raw byte data for each image
#    data1 = image1.tobytes()
#    data2 = image2.tobytes()
#
#    # Calculate a hash of the byte data for each image
#    hash1 = hashlib.md5(data1).hexdigest()
#    hash2 = hashlib.md5(data2).hexdigest()
#
#    # Compare the hashes to determine if the images are the same
#    if hash1 == hash2:
#        print("The images are the same.")
#    else:
#        print("The images are different.")
#
#def image_exic_cache(func):
#    @wraps(func)
#
#    def wrapper(*args, **kwargs):
#
#        im_path = args
#
#        with ImageMetadataDB() as im_db:
#            if im_db.exist(im_path):
#                return im_db.get_exifs(im_path)
#            else:
#                return im_db.add_image(im_path)
#
class ImageMetadataDB:
    def __init__(self):
        self.db_file = str(IMAGE_DATABASE_PATH)
        self.conn = None

    def __enter__(self):
        # Connect to the SQLite database and create the images table
        self.conn = sqlite3.connect(self.db_file)
        c = self.conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS images
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
                FOREIGN KEY (path, filename) REFERENCES images(path, filename)
            )''')

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
        #self.conn.close()
        self.conn.close()

    def exist(self, im_path):

        c= self.conn.cursor()
        md5_file, md5_data = get_fingerprint(im_path)
        c.execute(
            '''SELECT EXISTS(
                SELECT 1 FROM images WHERE md5_file=? LIMIT 1
            )''',
            (md5_file,))
        res = c.fetchone()

        return res[0]

    def get_file_list_preview(self):
        c = self.conn.cursor()
        c.execute('''
                SELECT new_folder, new_filename FROM tri_preview
                '''
                  )
        return c.fetchall()

    def exist_in_preview(self, im_path):

        new_folder = str(im_path.parent)
        new_filename = str(im_path.name)

        c= self.conn.cursor()
        c.execute(
            '''SELECT EXISTS(
                SELECT 1 FROM
                    tri_preview
                WHERE
                    new_folder = ?
                  AND
                    new_filename = ?
                LIMIT 1
            )''',
            (new_folder, new_filename)
        )

        v = bool(c.fetchone()[0])
        return v

    def add_location(self, im_str, location_metadata):

        c = self.conn.cursor()
        # Update all metadatas in images
        metadatas = self.get_exifs(im_str)
        metadatas.update(location_metadata)
        c = self.conn.cursor()
        c.execute('''
            UPDATE
                images
            SET
                metadata = ?
            WHERE
                path = ?''',
            (json.dumps(metadatas), im_str)

        )

        disp_name = location_metadata[EXIF_LOCATION_FIELD["display_name"]]
        # Put in preview windows
        c.execute('''
            UPDATE
                tri_preview
            SET
                location = ?
            WHERE
                path = ?''',
            (json.dumps(disp_name), im_str)
        )

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

        if res[0] is  None:
            return None
        return datetime.strptime(res[0], date_fmt)

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

    def get_exifs(self, im_path):

        c= self.conn.cursor()
        c.execute(
            '''SELECT metadata FROM images WHERE path=?''',
            (im_path,)
        )
        res = c.fetchone()
        return json.loads(res[0])

    def get_metadatas(self, im_path):

        return self.get_exifs(im_path)

    def scan_dest(self, im_str):

        # new file md5s
        md5_file, md5_data = get_fingerprint(im_str)

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

            if db_md5_file == md5_file and db_md5_data == md5_data:
                # md5 hash has not changed, do not update the row
                return

            elif db_md5_data == md5_data:
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
            c.execute('''
                INSERT INTO
                    scan_dest
                VALUES
                    (?, ?, ?)''',
                (md5_file, md5_data, im_str)
            )

    def clean_all_table(self):

        c = self.conn.cursor()
        c.execute("DELETE FROM images")
        c.execute("DELETE FROM tri_preview")
        c.execute("DELETE FROM scan_dest")

    def clean_dest_table(self):

        c = self.conn.cursor()
        c.execute("DELETE FROM tri_preview")

    def add_image_to_preview(self, im_str):

        c = self.conn.cursor()
        filename = Path(im_str).name

        preview_tuple = (
            im_str, filename, None, None, None, None, None
        )

        c.execute("""
            INSERT INTO
                tri_preview
            VALUES
                (?, ?, ?, ?, ?, ?, ?)""",
            preview_tuple
        )

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
        prev_date = None
        grp_date = None

        for path, date_str in c.fetchall():
            if date_str is None:
                continue
            date =datetime.strptime(date_str, date_fmt)
            if prev_date is None:
                prev_date = date
                grp_date = date
                self.set_group_preview(path, datetime.strftime(grp_date, date_fmt))
            elif (date - prev_date).days < n:
                self.set_group_preview(path, datetime.strftime(grp_date, date_fmt))
            else:
                self.set_group_preview(path, datetime.strftime(date, date_fmt))
                grp_date = date

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

    def add_image(self, im_str):

        # new file md5s
        md5_file, md5_data = get_fingerprint(im_str)

        # Check database
        c = self.conn.cursor()
        c.execute('''
            SELECT
                md5_file, md5_data
            FROM
                images
            WHERE
                path = ?''',
            (im_str,)
        )
        res = c.fetchone()

        if res:
            db_md5_file, db_md5_data = res

            if db_md5_file == md5_file and db_md5_data == md5_data:
                # md5 hash has not changed, do not update the row
                return

            elif db_md5_data == md5_data:
                # md5 hash has changed, update the row
                with ExifTags(im_str) as exifs:
                    metadata = exifs.copy()
                c.execute('''
                    UPDATE
                        images
                    SET
                        md5_file = ?, metadata = ?
                    WHERE
                        path = ?''',
                    (md5_file, json.dumps(metadata), im_str)
                )

            else: # Photo itself had changed, but waht to do????
                with ExifTags(im_str) as exifs:
                    metadata = exifs.copy()
                c.execute('''
                    UPDATE
                        images
                    SET
                        md5_file = ?, md5_data = ?, metadata = ?
                    WHERE path = ?''',
                    (md5_file, md5_data, json.dumps(metadata), im_str)
                )
                pass
        else:

            # md5 hash does not exist in the database, insert a new row
            folder = str(Path(im_str).parent)
            filename = Path(im_str).name
            extention = im_str.split('.')[-1].lower()

            try :
                with ExifTags(im_str) as exifs:
                    metadata = exifs.copy()

                date = metadata.get('Exif.Photo.DateTimeOriginal')
                camera = metadata.get('Exif.Image.Model')

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
            c.execute("INSERT INTO images VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", image_tuple)
            #c.execute("INSERT INTO tri_preview VALUES (?, ?, ?, ?, ?)", preview_tuple)


    def get_camera_list(self):

        c= self.conn.cursor()
        c.execute(
            '''SELECT DISTINCT camera FROM images'''
        )
        res = c.fetchall()
        if not res:
            return []
        return [r[0] for r in res if r[0] is not None]

    def get_tag_list(self):

        c= self.conn.cursor()
        c.execute(
            '''SELECT metadata FROM images'''
        )

        exifs_all = set()
        while row := c.fetchone():
            exifs_all.update(list(json.loads(row[0]).keys()))

        c.execute(
            '''SELECT metadata FROM images'''
        )

        exifs_common = set()
        while row := c.fetchone():
            exifs_common.intersection_update(list(json.loads(row[0]).keys()))

        return exifs_all, exifs_common

    def get_extention_list(self):

        c= self.conn.cursor()
        c.execute(
            '''SELECT DISTINCT extentions FROM images'''
        )
        res = c.fetchall()
        return [r[0] for r in res]

    def count(self, *args, **kwargs):

        nb_files = 0
        nb_bytes = 0

        for f in self.list_files(*args, **kwargs):
            nb_files += 1
            nb_bytes += Path(f).stat().st_size

        return nb_files, nb_bytes

    def get_preview(self, paths):

        paths = list(paths)
        c = self.conn.cursor()
        placeholders = ','.join('?' for _ in paths)
        query = f"SELECT * FROM tri_preview WHERE path IN ({placeholders})"
        c.execute(query, paths)

        res = c.fetchall()

        return res

    def exist_in_dest(self, in_str):

        c = self.conn.cursor()
        c.execute('''
            SELECT
                md5_data
            FROM
                images
            WHERE
                path = ?''',
            (in_str,)
        )

        md5_data = c.fetchone()

        c.execute("""
            SELECT
                *
            FROM
                scan_dest
            WHERE
                md5_data = ?""",
            md5_data
        )

        return bool(c.fetchone())

    def list_files(self, src_dir='', extentions=[], cameras=[], recursive=True, duplicate_md5_file=False, duplicate_md5_data=False, filter_txt=''):

        src_dir = str(src_dir)

        if not duplicate_md5_data and not duplicate_md5_file:
            cmd = 'SELECT path, md5_file FROM images'
        elif duplicate_md5_file:
            cmd = "SELECT path, md5_file, MAX(path) FROM images "
        elif duplicate_md5_data:
            cmd = "SELECT path, md5_data, MAX(path) FROM images"

        if not recursive:
            cmd += " " + "WHERE folder = ? AND path LIKE '%' || ? || '%'"
        else:
            cmd += " " + "WHERE folder LIKE ? || '%' AND path LIKE '%' || ? || '%'"
        tup = (src_dir, filter_txt)


        cmd += " " + f"AND extentions IN ({','.join('?' for _ in extentions)})"
        tup += (*extentions,)

        if cameras and cameras[0]:
            cmd += " " + f"AND camera IN ({','.join('?' for _ in cameras)})"
            tup += (*cameras,)

        if not duplicate_md5_data and not duplicate_md5_file:
            pass
            #cmd = ' ' + 'GROUP BY md5_data'
        elif duplicate_md5_file:
            cmd += ' ' + 'GROUP BY md5_file'
        elif duplicate_md5_data:
            cmd += ' ' + 'GROUP BY md5_data'

        c= self.conn.cursor()
        c.execute(cmd, tup)
        #res = c.fetchall()
        l = c.fetchall()
        for row in l:
        #while (row := c.fetchone()) is not None:
            yield row[0]

    #def move(self, src_dir, extentions, cameras=[], recursive=True, del_duplicates=True):

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
