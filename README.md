# Tri photo date

## Foreword

Program is still in progress, please make copies of your photo before using. Nevertheless most function shoud work well at this time.
So feel free to give any feedbacks.

## About

The program offers an interface to sort your photo folders based on their metadata. Paths can be customized with placeholders to then be replaced by specific data for each photo.

Depending on the options enabled, the program achieves the following:

1. Scan folders, get fingerprints, parse metadatas
2. Generate new paths given filter and options:
    1. Filter files:
        - extensions, 
        - camera model, 
        - folder / regex 
        - duplicates
    2. Perform actions:
        - parse photo date through filename 
        - group photo applying a floating window over multiples days
        - resolve place of the shot using GPS datas (module geopy and the service [Nominatim proposed by OpenStreetMap](https://nominatim.openstreetmap.org/ui/search.html))
        - force date from filesystem timestamp
3. Execute:
    1. Simulate/copy/move files
    1. Delete metadats / add new metadatas

<img src="docs/screen_advanced_mode_main_tab_n_preview.png" width="400">

## Run & Install

### Binaries

Compiled binaries are [available to download](https://github.com/Daguhh/tri_photo_date/releases/latest) for both linux and windows. No dependancies required, no install needed

### Python package

Get [python wheel](https://github.com/Daguhh/tri_photo_date/releases/latest), then,
in a virtual env

```shell
python3 -m pip install tri_photo_date-x.y.z-py3-none-any.whl
```
```shell
tri_photo_date
```

### From source code

With poetry:

```shell
git clone https://github.com/Daguhh/tri_photo_date.git
cd tri_photo_date
poetry install
```
```shell
poetry run tri_photo_date
```

## Usage

### TL;DR

Fill and execute action (push button) from top to down.
Use tooltip to get hints on [parameters](tri_photo_date/config/default_config.ini) function and format.

### cli / shell

```bash
poetry run tri_photo_date --help
```
```
usage: tri_photo_date [-h] [-d [DUMP] | -D [DUMP_DEFAULT] | -l [LOAD]] [mode]

Sort image using metadata placeholder

positional arguments:
  mode                  shell/gui, chose interface to run, gui will be run by default

options:
  -h, --help            show this help message and exit
  -d [DUMP], --dump [DUMP]
                        save actual config to path and exit
  -D [DUMP_DEFAULT], --dump-default [DUMP_DEFAULT]
                        save default config to path and exit
  -l [LOAD], --load [LOAD]
                        run the program with given config
```

Also, you can directly run shell commands from command line:
```bash
poetry run tri_photo_date shell set <section> <param> <value>
poetry run tri_photo_date shell scan
poetry run tri_photo_date shell process
poetry run tri_photo_date shell preview
poetry run tri_photo_date shell execute
```

### Simplified mode

```
            ┌──────────────────┐
            │ Set source and   │
            │ destination      │
            └───────┬──────────┘
                    ▼
            ┌──────────────────┐
            │    1. Scan       │
            └───────┬──────────┘
                    ▼
            ┌──────────────────┐
            │ Set paths format │
            │ set filters      │◀────┐
            │ set options      │  ┌──┴────────────┐
            └───────┬──────────┘  │ Check preview │
                    ▼             │     panel     │
            ┌──────────────────┐  └──┬────────────┘
            │ 2. Pre-calculate ├─────┘              
            └───────┬──────────┘  Update preview
                    ▼
            ┌──────────────────┐
            │   3. Execute     │
            └──────────────────┘
```
### Advanced mode

```
                          ┌──────────────────┐
                          │  Set source and  │
                          │    destination   │
                          └───────┬──────────┘
                                  ▼
      Update toolboxes    ┌──────────────────┐
           ┌──────────────┤     1. Scan      │
           │              └───────┬──────────┘
           ▼                      ▼
  ┌──────────────────┐    ┌──────────────────┐
  │   Set checkbox   │    │ Set paths format │
  │ Copy placeholder │◀──▶│ set filters      │◀────┐
  └──────────────────┘    │ set options      │  ┌──┴────────────┐
                          └───────┬──────────┘  │ Check preview │
                                  ▼             │     panel     │
                          ┌──────────────────┐  └──┬────────────┘
                          │ 2. Pre-calculate ├─────┘              
                          └───────┬──────────┘   Update preview
                                  ▼
                          ┌──────────────────┐
                          │   3. Execute     │
                          └──────────────────┘
```

### Command line (expired?)

A small command line utility is available. It's not very elaborate at the moment, but it should allow dealing with multiple preconfigurations to run scripts in the daily routine

```
usage: tri_photo_date [-h] [--cli] [-d [DUMP] | -D [DUMP_DEFAULT] | -l [LOAD]]

Sort image using metadata placeholder

options:
  -h, --help            show this help message and exit
  --cli                 run in cli
  -d [DUMP], --dump [DUMP]
                        save actual config to path and exit
  -D [DUMP_DEFAULT], --dump-default [DUMP_DEFAULT]
                        save default config to path and exit
  -l [LOAD], --load [LOAD]
                        run the program with given config
```


## Files

Tri-photo-date generated files:

| File             | Path                      | Description                  | 
|------------------|---------------------------|------------------------------|
| config.ini       | APPDATA/triphotodate      | Store user parameters        |
| gps.db           | LOCALAPPDATA/triphotodate | Cache for gps data (prevent unnecessay call to nominatim api) |
| images.db        | LOCALAPPDATA/triphotodate | Cache for images datas and store datas during process |
| triphotodate.log | ???????                   | program log file             |

## Credits

### Embed dependancies

- Interface : [PyQt5](https://www.riverbankcomputing.com/software/pyqt/) -  [GNU GPL v3](https://www.gnu.org/licenses/gpl-3.0.en.html)
- Handling Exifs : [pyexiv2](https://github.com/LeoHsiao1/pyexiv2) - [GNU GPL v3](https://www.gnu.org/licenses/gpl-3.0.en.html)
- Addresses resolution: [geopy](https://geopy.readthedocs.io/en/stable/) - [MIT](https://opensource.org/license/mit/)
- SSL certificates : [certifi](https://github.com/certifi/python-certifi) - [MPL](http://mozilla.org/MPL/2.0/)

### Oneline service

This program use the [OpenStreetMap nominatim](https://nominatim.openstreetmap.org/ui/search.html) service for resolving addresses from GPS coordinates:
- Consult [Copyright](https://www.openstreetmap.org/copyright)
- Consult [Usage policy](https://operations.osmfoundation.org/policies/nominatim/)
- Consult [Privacy policy](https://wiki.osmfoundation.org/wiki/Privacy_Policy) du service

