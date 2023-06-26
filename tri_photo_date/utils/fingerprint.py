import hashlib
import os
import struct


def set_global_config(config):
    global max_length
    is_max_hash = config["files"]["is_max_hash_size"]
    if is_max_hash:
        max_length = config["files"]["max_hash_size"] * 1000 * 1000  # 1 MB ->5000 MB
    else:
        max_length = 1000 * 1000 * 1000 * 5  # 5GB


def get_file_fingerprint(im_path):
    with open(im_path, "rb") as f:
        md5_file = hashlib.md5()
        i = 0
        while chunk := f.read(4 * 1024 * 1024):
            md5_file.update(chunk)

            i += 4 * 1024 * 1024
            if i > max_length:
                break

    return md5_file.hexdigest()


def get_data_fingerprint(im_path):
    # if im_path.lower().endswith('jpg'):
    try:
        md5_data = jpeg_data_fingerprint(im_path)
        return md5_data
    except AssertionError:
        pass
    # elif im_path.lower().endswith('png'):
    try:
        md5_data = png_data_fingerprint(im_path)
        return md5_data
    except AssertionError:
        pass
    # elif im_path.lower().endswith(('mov', 'mp4'):
    try:
        md5_data = mp4_data_fingerprint(im_path)
        return md5_data
    except AssertionError:
        pass
    # else:

    return None


# https://stackoverflow.com/a/10075170
def png_data_fingerprint(im_str):
    mlength = max_length
    hash = hashlib.md5()
    fh = open(im_str, "rb")
    assert fh.read(8)[1:4] == b"PNG"
    while True:
        try:
            (length,) = struct.unpack(">i", fh.read(4))
        except struct.error:
            break
        if 0 < length:
            break
        if fh.read(4) == b"IDAT":
            hash.update(fh.read(min(mlength, length)))
            mlength = max(mlength - length, 0)
            if mlength == 0:
                break
            fh.read(4)  # CRC
        else:
            fh.seek(length + 4, os.SEEK_CUR)
    return hash.hexdigest()


def jpeg_data_fingerprint(im_str):
    hash = hashlib.md5()
    fh = open(im_str, "rb")
    assert fh.read(2) == b"\xff\xd8"
    while True:
        marker, length = struct.unpack(">2H", fh.read(4))
        assert marker & 0xFF00 == 0xFF00
        if marker == 0xFFDA:  # Start of stream
            i = 0
            while chunk := fh.read(4 * 1024 * 1024):
                hash.update(chunk)

                i += 4 * 1024 * 1024
                if i > max_length:
                    break
            break
        else:
            fh.seek(length - 2, os.SEEK_CUR)
    return hash.hexdigest()


def mp4_data_fingerprint(im_str):
    mlength = max_length
    hash = hashlib.md5()
    fh = open(im_str, "rb")
    assert fh.read(8)[4:9] == b"ftyp"
    l = 0
    fh.seek(0)
    while True:
        try:
            (length,) = struct.unpack(">i", fh.read(4))
            l += length
        except struct.error:
            break
        tmp = fh.read(4)
        if 0 < l:
            break
        if tmp == b"mdat":
            hash.update(fh.read(min(mlength, length)))
            mlength = max(mlength - length, 0)
            if mlength == 0:
                break
            fh.read(4)  # crc
        else:
            fh.seek(l)
    return hash.hexdigest()
