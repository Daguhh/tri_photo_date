@ECHO OFF
IF NOT EXIST venv\Scripts\activate.bat (
    python -m venv build_env
)
call build_env\Scripts\activate.bat
python -m pip install poetry
python -m poetry install --no-root
python -m pip install pyinstaller
pyinstaller ^
    --onefile ^
    --paths venv\Lib\site-packages ^
    --icon="resources/icon.ico" ^
    --add-data "resources/icon.ico;." ^
    --add-data "resources/strftime_help.html;." ^
    --add-data "resources/en/*;./resources/en/" ^
    --add-data "resources/fr/*;./resources/fr/" ^
    --add-data "tri_photo_date/config/*;./config/" ^
    --add-data "README.md;." ^
    --add-data "LICENSE;." ^
    --add-data "tri_photo_date/locales/fr/LC_MESSAGES/base.mo;./locales/fr/LC_MESSAGES/" ^
    --add-data "tri_photo_date/locales/en/LC_MESSAGES/base.mo;./locales/en/LC_MESSAGES/" ^
    --noconfirm ^
    --additional-hooks-dir=hooks ^
    --name tri_photo_date ^
    tri_photo_date\__main__.py

pause

