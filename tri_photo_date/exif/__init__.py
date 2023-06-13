# try:
#    from .exif import ExifTags
#    from .tags_description import TAG_DESCRIPTION
#    from .usefull_tags import USEFULL_TAG_DESCRIPTION
# except ModuleNotFoundError:
from tri_photo_date.exif.exif import ExifTags, NoExifError
from tri_photo_date.exif.tags_description import TAG_DESCRIPTION
from tri_photo_date.exif.usefull_tags import USEFULL_TAG_DESCRIPTION


EXIF_DATE_FIELD = {
    "date_time_original": "Exif.Photo.DateTimeOriginal",
    "date_time_digitized": "Exif.Photo.DateTimeDigitized",
    "date_time": "Exif.Image.DateTime",
}

EXIF_GPS_FIELD = {
    "latitude_ref": "Exif.GPSInfo.GPSLatitudeRef",
    "latitude": "Exif.GPSInfo.GPSLatitude",
    "longitude_ref": "Exif.GPSInfo.GPSLongitudeRef",
    "longitude": "Exif.GPSInfo.GPSLongitude",
}

"""
0x005a 	90 	Iptc.Application2.City
0x005c 	92 	Iptc.Application2.SubLocation
0x005f 	95 	Iptc.Application2.ProvinceState
0x0064 	100 	Iptc.Application2.CountryCode
0x0065 	101 	Iptc.Application2.CountryName
0x001a 	26 	Iptc.Application2.LocationCode
0x001b 	27 	Iptc.Application2.LocationName
"""

EXIF_LOCATION_FIELD = {
    "city": "Iptc.Application2.City",
    "road": "Iptc.Application2.SubLocation",
    "region": "Iptc.Application2.ProvinceState",
    "country_code": "Iptc.Application2.CountryCode",
    "country": "Iptc.Application2.CountryName",
    "display_name": "Iptc.Application2.LocationName",
}

EXIF_CAMERA_FIELD = {"camera": "Exif.Image.Model"}


# LOCATION_TAGS = [
#    "Iptc.Application2.City",
#    "Iptc.Application2.SubLocation",
#    "Iptc.Application2.ProvinceState",
#    "Iptc.Application2.CountryCode",
#    "Iptc.Application2.CountryName",
#    "Iptc.Application2.LocationCode",
#    "Iptc.Application2.LocationName",
# ]
