@echo off
setlocal

:: test if python is installed
where python >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo 'python' command is not available
    goto end
)

:: test if poetry is installed
python -m poetry --version >NUL 2>NUL
if %ERRORLEVEL% NEQ 0 (
    echo Poetry package not found.
    python -m pip install poetry
)

:: create venv
python -m poetry env use system

:: get venv path
for /f "delims=" %%a in ('python -m poetry env info --path') do (SET "venv_path=%%a")

:: get package version
:: for /f "delims= " %%a in ('python -m poetry --version') do (set version=%%a)
for /f "tokens=2 delims= " %%a in ('python -m poetry version') do (SET "pkg_version=%%a")



:: install deps and build deps
python -m poetry install --no-root --with build_bin

:: run pyinstaller
python -m poetry run pyinstaller ^
    --onefile ^
    --paths="%venv_path%/Lib/site-packages" ^
    --icon="resources/icon.ico" ^
    --add-data "resources/icon.ico;." ^
    --add-data "resources/strftime_help.html;." ^
    --add-data "resources/en/*;./resources/en/" ^
    --add-data "resources/fr/*;./resources/fr/" ^
    --add-data "tri_photo_date/config/config_default.toml;./config/" ^
    --add-data "README.md;." ^
    --add-data "LICENSE;." ^
    --add-data "tri_photo_date/locales/fr/LC_MESSAGES/base.mo;./locales/fr/LC_MESSAGES/" ^
    --add-data "tri_photo_date/locales/en/LC_MESSAGES/base.mo;./locales/en/LC_MESSAGES/" ^
    --noconfirm ^
    --additional-hooks-dir=hooks ^
    --name "tri_photo_date_%pkg_version%" ^
    tri_photo_date/__main__.py

:end
endlocal
