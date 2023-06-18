from tri_photo_date import sort_photos


def cli_run():
    print("run cli")
    sort_photos.populate_db()
    sort_photos.compute()
    sort_photos.execute()
