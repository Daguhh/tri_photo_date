from tri_photo_date import ordonate_photos


def cli_run():
    print("run cli")
    ordonate_photos.populate_db()
    ordonate_photos.compute()
    ordonate_photos.execute()
