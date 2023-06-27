from tri_photo_date.photo_database import ImageMetadataDB


def list_available_exts(in_path, recursive=True):
    with ImageMetadataDB() as db:
        exts = db.get_extention_list()

    return sorted(exts)


def list_available_tags(in_path, extentions, recursive=True):
    with ImageMetadataDB() as db:
        exifs_all, exifs_common = db.get_tag_list()

    return sorted(exifs_all), sorted(exifs_common)


def list_available_camera_model(in_path, extentions, recursive=True):
    with ImageMetadataDB() as db:
        cameras = db.get_camera_list()

    return sorted(cameras)
