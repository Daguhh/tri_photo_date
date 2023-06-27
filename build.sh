# TriPhoteDate build scripts

help () {
echo "usage build.sh [-h|--help] [-b|--build-bin] [-d|--delete-venv]

Build tri_photo_date binaries

options:
  -h, --help            show this help message and exit
  -b, --build-package   build python package
  -B, --build-bin       build linux binary
  -d, --delete-venv     delete build environnement
"
}

if [[ $# -eq 0 ]]; then help; exit 0; fi
if [[ " $@ " =~ " -h " ]] || [[ " $@ " =~ " --help " ]] ; then help; exit 0; fi
if [[ " $@ " =~ " -b " ]] || [[ " $@ " =~ " --build-package " ]] ; then BUILD_PACKAGE=true; fi
if [[ " $@ " =~ " -B " ]] || [[ " $@ " =~ " --build-bin " ]] ; then BUILD_BIN=true; fi
if [[ " $@ " =~ " -d " ]] || [[ " $@ " =~ " --delete-venv " ]] ; then DELETE_VENV=true; fi
if [[ " $@ " =~ " --with-speedbar " ]] ; then SPEED_BAR="--with speedbar"; fi

# test python installation
if ! type "python3" > /dev/null; then
    echo "Please install python"
    exit 0
fi

# test poetry installation
if ! type "poetry" > /dev/null; then
    echo "poetry not installed"
    python3 -m pip install poetry --user
fi

# Create venv
poetry env use system

if [[ "${BUILD_PACKAGE}" == true ]]; then
    poetry build
fi

if [[ "${BUILD_BIN}" == true ]]; then

    # Get venv path
    venv_path=$(poetry env info --path)

    # Get package version
    version=$(poetry version | cut -d" " -f2)

    # Install deps and build deps
    poetry install --no-root --with build_bin $SPEED_BAR

    # RUn pyinstaller
    poetry run pyinstaller \
        --onefile \
        --paths $venv_path\Lib\site-packages \
        --icon="resources/icon.ico" \
        --add-data "resources/icon.ico:." \
        --add-data "resources/strftime_help.html:." \
        --add-data "resources/en/*:./resources/en/" \
        --add-data "resources/fr/*:./resources/fr/" \
        --add-data "tri_photo_date/config/default_config.toml:./config/default_config.toml" \
        --add-data "README.md:." \
        --add-data "LICENSE:." \
        --add-data "tri_photo_date/locales/fr/LC_MESSAGES/base.mo:./locales/fr/LC_MESSAGES/" \
        --add-data "tri_photo_date/locales/en/LC_MESSAGES/base.mo:./locales/en/LC_MESSAGES/" \
        --noconfirm \
        --additional-hooks-dir=hooks \
        --name tri_photo_date_$version.bin \
        tri_photo_date/__main__.py
fi

# Delete venv

if [[ "${DELETE_VENV}" == true ]]; then
    venv_name=$(poetry env list | grep Activated | cut -d" " -f1)
    poetry env remove $venv_name
fi

