"""
adapted version for linux and windows of
pyexiv2 hooks from https://github.com/orgs/pyinstaller/discussions/6404#discussioncomment-5390655
"""


import os
import sys
import sysconfig
from PyInstaller.utils.hooks import collect_data_files

python_version = ".".join((str(sys.version_info.major), str(sys.version_info.minor)))
# Collect the required binary files
binaries = []

# Get the system Python library path
python_lib_path = sysconfig.get_path('platlib')

if os.name == "nt":
    libexiv2_path = f"{python_lib_path}/pyexiv2/lib/exiv2.dll"
    pyd_path = f"{python_lib_path}/pyexiv2/lib/py{python_version}-win/exiv2api.pyd"
    cpp_path = f"{python_lib_path}/pyexiv2/lib/exiv2api.cpp"

    # Append the binary files and their destination paths to the binaries list
    binaries.append((libexiv2_path, "pyexiv2/lib"))
    binaries.append((pyd_path, f"pyexiv2/lib/py{python_version}-win"))
    binaries.append((cpp_path, "pyexiv2/lib"))
else:
    libexiv2_path = f"{python_lib_path}/pyexiv2/lib/libexiv2.so"
    exiv2api_path = f"{python_lib_path}/pyexiv2/lib/exiv2api.so"

    # Append the binary files and their destination paths to the binaries list
    binaries.append((libexiv2_path, "pyexiv2/lib"))
    binaries.append((exiv2api_path, f"pyexiv2/lib/py{python_version}-linux"))

# Collect any data files if needed
datas = collect_data_files('pyexiv2')

