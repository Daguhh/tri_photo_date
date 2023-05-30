# Tri photo date

## Foreword

Program is still in progress, please make copies of your photo before using. Nevertheless most function shoud work well at this time.
So feel free to give any feedbacks.

## About

The program offers, through an interface, to sort your photo folders based on their metadata. 
Paths can be customized with placeholders to be then replaced by datas specific to each photo.

Depending on the options enabled, the program achieves in order:

1. Calculation of file fingerprints for duplicate identification (md5) 
2. Recover metadata 
3. Resolution of the location name/addresse of the shotting using gps coordinates (module geopy and the service [Nomeinatim proposed by OpenStreetMap](https://nominatim.openstreetmap.org/ui/search.html) 
4. Generation of a new path to record photos 
5. Copy of the photo

## Install

### Binaries

Compiled binaries are (should) avaible to download for both linux and windows. No dependancies required, no install needed

### Python package

With poetry:

```shell
git clone https://github.com/Daguhh/tri_photo_date.git
cd tri_photo_date
poetry install
```

```shell
some tri_photo_date command
```

### As source code 

In a virtual environnement :

```shell
git clone https://github.com/Daguhh/tri_photo_date.git
cd tri_photo_date
poetry shell
poetry install --no-root
```
```shell
python3 tri_photo_date
```

## Usage

### Simplified mode

![simplified main tab](docs/screen_simplified_mode_main_tab.png)

1. Fill source and destination sections, set path,  choose preselection using combobox
2. Run **'1. Scan'** : it will search for all medias in those folders.
3. Run **'2. Pre-calculate'** : program generate output path for you images and fill preview pane
4. CHeck preview pane using vertical button on the right. Repeat previous step until you're fine with parameters
5. Choose if you want to simulate/copy/move files 
6. Run **'3. Execute'** : program will perform action you choose, wait until it ends

### Advanced mode

![advanced main tab](docs/screen_advanced_mode_main_tab.png) ![tool tab](docs/screen_tool_tab.png)

Here is typicals steps users should perform to run the program:

1. Fill source folder and destination folder 
2. Run **'1. Scan'** : it will search for all medias in those folders and populate the **tools** tab
3. Go to **tools** tab. In the differents toolboxes, you will find all necessary datas to inform 
fields **source** and **destination** in **main** tab. 
Use checkbox when you can or use copy/paste to get placerholders.
4. Set **options** section, use tootlip to get information on waht to do.
5. Run **'2. Pre-calculate'** : it will use all parameters to pre-generate path where to move photos.
It include getting photo metadata, resolving location, replacing placerholders and all options you checked.
6. On right side click the vertical button "Show preview". It will display a table showing gathered 
data and calculated folders and filenames for each photos.
7. Adapt parameters in **main** tab if needed and re-run **2. Pre-calculate** until you fine with the parameters.
8. Please check if you simulate/copy/move the files and run **3. Execute**. Wait until the process end.
9. You can quit, parameters are automaticly saved for next section.


## Files

Tri-photo-date generated files:

| File | Path | Description |
|------|------|-------------|
| config.ini | APPDATA/triphotodate | Store user parameters |
| gps.db | APPDATA/triphotodate | Cache for gps data (prevent unnecessay call to nominatim api) |
| images.db | APPDATA/triphotodate | Cache for images datas and store datas during process |
| triphotodate.log | ??????? | program log file |



