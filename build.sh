python3 -m venv venv
source venv/bin/activate
poetry install
python3 -m pip install pyinstaller
pyinstaller \
    --onefile \
    --paths .venv\Lib\site-packages \
    --icon="resources/icon.ico" \
    --add-data "resources/icon.ico:." \
    --add-data "resources/acknowledgments.md:." \
    --add-data "resources/about.md:." \
    --add-data "resources/strftime_help.html:." \
    --add-data "README.md:." \
    --add-data "LICENSE:." \
    --add-data "tri_photo_date/locales/fr/LC_MESSAGES/base.mo:./locales/fr/LC_MESSAGES/" \
    --add-data "tri_photo_date/locales/en/LC_MESSAGES/base.mo:./locales/en/LC_MESSAGES/" \
    --noconfirm \
    --additional-hooks-dir=hooks \
    tri_photo_date/run.py

