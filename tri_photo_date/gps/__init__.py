
try:
    from .gps import add_tags_to_image, get_image_gps_location
    from .gps_constants import LOCATION_TYPES
except ModuleNotFoundError:
    from tri_photo_date.gps.gps import add_tags_to_image, get_image_gps_location
    from tri_photo_date.gps.gps_constants import LOCATION_TYPES

