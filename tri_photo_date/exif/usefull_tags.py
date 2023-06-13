USEFULL_TAG_DESCRIPTION = {
    "Exif.Image.ImageWidth": "The number of columns of image data, equal to the number of pixels per row. In JPEG compressed data a JPEG marker is used instead of this tag.",
    "Exif.Image.ImageLength": "The number of rows of image data. In JPEG compressed data a JPEG marker is used instead of this tag.",
    "Exif.Image.DocumentName": "The name of the document from which this image was scanned.",
    "Exif.Image.ImageDescription": 'A character string giving the title of the image. It may be a comment such as"1988 company picnic" or the like. Two-bytes character codes cannot be used. When a 2-bytes code is necessary, the Exif Private tag <UserComment> is to be used.',
    "Exif.Image.Make": "The manufacturer of the recording equipment. This is the manufacturer of the DSC, scanner, video digitizer or other equipment that generated the image. When the field is left blank, it is treated as unknown.",
    "Exif.Image.Model": "The model name or model number of the equipment. This is the model name or number of the DSC, scanner, video digitizer or other equipment that generated the image. When the field is left blank, it is treated as unknown.",
    "Exif.Image.Orientation": "The image orientation viewed in terms of rows and columns.",
    "Exif.Image.Software": "This tag records the name and version of the software or firmware of the camera or image input device used to generate the image. The detailed format is not specified, but it is recommended that the example shown below be followed. When the field is left blank, it is treated as unknown.",
    "Exif.Image.DateTime": "The date and time of image creation. In Exif standard, it is the date and time the file was changed.",
    "Exif.Image.Artist": 'This tag records the name of the camera owner, photographer or image creator. The detailed format is not specified, but it is recommended that the information be written as in the example below for ease of Interoperability. When the field is left blank, it is treated as unknown. Ex.)"Camera owner, John Smith; Photographer, Michael Brown; Image creator, Ken James"',
    "Exif.Image.HostComputer": "This tag records information about the host computer used to generate the image.",
    "Exif.Image.Rating": "Rating tag used by Windows",
    "Exif.Image.DateTimeOriginal": "The date and time when the original image data was generated.",
    "Exif.Image.XPTitle": "Title tag used by Windows, encoded in UCS2",
    "Exif.Image.XPComment": "Comment tag used by Windows, encoded in UCS2",
    "Exif.Image.XPAuthor": "Author tag used by Windows, encoded in UCS2",
    "Exif.Image.XPKeywords": "Keywords tag used by Windows, encoded in UCS2",
    "Exif.Image.XPSubject": "Subject tag used by Windows, encoded in UCS2",
    "Exif.Image.UniqueCameraModel": "Defines a unique, non-localized name for the camera model that created the image in the raw file. This name should include the manufacturer's name to avoid conflicts, and should not be localized, even if the camera name itself is localized for different markets (see LocalizedCameraModel). This string may be used by reader software to index into per-model preferences and replacement profiles.",
    "Exif.Image.LocalizedCameraModel": "Similar to the UniqueCameraModel field, except the name can be localized for different markets to match the localization of the camera name.",
    "Exif.Image.LensInfo": "Contains information about the lens that captured the image. If the minimum f-stops are unknown, they should be encoded as 0/0.",
    "Exif.Image.CameraLabel": "The optional CameraLabel tag shall specify a text label for how the camera is used or assigned in this clip. This tag is similar to CameraLabel in XMP.",
    "Exif.Photo.DateTimeOriginal": "The date and time when the original image data was generated. For a digital still camera the date and time the picture was taken are recorded.",
    "Exif.Photo.DateTimeDigitized": "The date and time when the image was stored as digital data.",
    "Exif.Photo.UserComment": "A tag for Exif users to write keywords or comments on the image besides those in <ImageDescription>, and without the character code limitations of the <ImageDescription> tag.",
    "Exif.Photo.LensMake": "This tag records the lens manufactor as an ASCII string.",
    "Exif.Photo.LensModel": "This tag records the lens's model name and model number as an ASCII string.",
    "Exif.Photo.LensSerialNumber": "This tag records the serial number of the interchangeable lens that was used in photography as an ASCII string.",
    "Exif.GPSInfo.GPSVersionID": "Indicates the version of <GPSInfoIFD>. The version is given as 2.0.0.0. This tag is mandatory when <GPSInfo> tag is present. (Note: The <GPSVersionID> tag is given in bytes, unlike the <ExifVersion> tag. When the version is 2.0.0.0, the tag value is 02000000.H).",
    "Exif.GPSInfo.GPSLatitudeRef": "Indicates whether the latitude is north or south latitude. The ASCII value 'N' indicates north latitude, and 'S' is south latitude.",
    "Exif.GPSInfo.GPSLatitude": "Indicates the latitude. The latitude is expressed as three RATIONAL values giving the degrees, minutes, and seconds, respectively. When degrees, minutes and seconds are expressed, the format is dd/1,mm/1,ss/1. When degrees and minutes are used and, for example, fractions of minutes are given up to two decimal places, the format is dd/1,mmmm/100,0/1.",
    "Exif.GPSInfo.GPSLongitudeRef": "Indicates whether the longitude is east or west longitude. ASCII 'E' indicates east longitude, and 'W' is west longitude.",
    "Exif.GPSInfo.GPSLongitude": "Indicates the longitude. The longitude is expressed as three RATIONAL values giving the degrees, minutes, and seconds, respectively. When degrees, minutes and seconds are expressed, the format is ddd/1,mm/1,ss/1. When degrees and minutes are used and, for example, fractions of minutes are given up to two decimal places, the format is ddd/1,mmmm/100,0/1.",
    "Exif.GPSInfo.GPSAltitudeRef": "Indicates the altitude used as the reference altitude. If the reference is sea level and the altitude is above sea level, 0 is given. If the altitude is below sea level, a value of 1 is given and the altitude is indicated as an absolute value in the GSPAltitude tag. The reference unit is meters. Note that this tag is BYTE type, unlike other reference tags.",
    "Exif.GPSInfo.GPSAltitude": "Indicates the altitude based on the reference in GPSAltitudeRef. Altitude is expressed as one RATIONAL value. The reference unit is meters.",
    "Iptc.Application2.Keywords": "Used to indicate specific information retrieval words. It is expected that a provider of various types of data that are related in subject matter uses the same keyword, enabling the receiving system or subsystems to search across all types of data for related material.",
    "Iptc.Application2.LocationCode": "Indicates the code of a country/geographical location referenced by the content of the object. Where ISO has established an appropriate country code under ISO 3166, that code will be used. When ISO 3166 does not adequately provide for identification of a location or a country, e.g. ships at sea, space, IPTC will assign an appropriate three-character code under the provisions of ISO 3166 to avoid conflicts.",
    "Iptc.Application2.LocationName": "Provides a full, publishable name of a country/geographical location referenced by the content of the object, according to guidelines of the provider.",
    "Iptc.Application2.DateCreated": "Represented in the form CCYYMMDD to designate the date the intellectual content of the object data was created rather than the date of the creation of the physical representation. Follows ISO 8601 standard.",
    "Iptc.Application2.TimeCreated": "Represented in the form HHMMSS:HHMM to designate the time the intellectual content of the object data current source material was created rather than the creation of the physical representation. Follows ISO 8601 standard.",
    "Iptc.Application2.DigitizationDate": "Represented in the form CCYYMMDD to designate the date the digital representation of the object data was created. Follows ISO 8601 standard.",
    "Iptc.Application2.DigitizationTime": "Represented in the form HHMMSS:HHMM to designate the time the digital representation of the object data was created. Follows ISO 8601 standard.",
    "Iptc.Application2.Program": "Identifies the type of program used to originate the object data.",
    "Iptc.Application2.City": "Identifies city of object data origin according to guidelines established by the provider.",
    "Iptc.Application2.SubLocation": "Identifies the location within a city from which the object data originates, according to guidelines established by the provider.",
    "Iptc.Application2.ProvinceState": "Identifies Province/State of origin according to guidelines established by the provider.",
    "Iptc.Application2.CountryCode": "Indicates the code of the country/primary location where the intellectual property of the object data was created, e.g. a photo was taken, an event occurred. Where ISO has established an appropriate country code under ISO 3166, that code will be used. When ISO 3166 does not adequately provide for identification of a location or a new country, e.g. ships at sea, space, IPTC will assign an appropriate three-character code under the provisions of ISO 3166 to avoid conflicts.",
    "Iptc.Application2.CountryName": "Provides full, publishable, name of the country/primary location where the intellectual property of the object data was created, according to guidelines of the provider.",
    "Iptc.Application2.Caption": "A textual description of the object data.",
    "Exif.Samsung2.LocalLocationName": "Local location name",
    "Exif.Samsung2.LocationName": "Location name",
    "Exif.Samsung2.LensType": "Lens type",
}
