from tri_photo_date.config.config_loader import CONFIG
from tri_photo_date.config.config_paths import LOCALES_DIR

import gettext

lang = CONFIG[("interface", "lang")]
trad = gettext.translation("base", localedir=LOCALES_DIR, languages=[lang])
trad.install()
_ = trad.gettext  # Greek


WARNING_SWITCH_SIMPLIFY_MODE = _(
    "Attention, les paramètres de la section 'options' ne seront plus\naccessibles mais garderont leur effets.\n\nVous pouvez garder les paramètres actuels ou revenir aux paramètres par défaut."
)

MEDIA_FORMATS = {
    _(
        r"{media_photos}"
    ):"jpg,jpeg,png,webp,bmp,ico,tiff,heif,heic,svg,raw,arw,cr2,nrw,k25,apng,avif,gif,svg",
    _(
        r"{media_videos}"
    ):"webm,mkv,flv,ogg,gif,avi,mov,asf,mp4,m4v,mpg,mp2,mpeg,mpv,3gp,3g2,flv",
}

REL_PATH_FORMATS = {
    _(r"{Année/Année-Mois}"): r"%Y/%Y-%m",
    _(r"{Année/Mois}"): r"%Y/%m",
    _(r"{Appareil}"): "<Exif.Image.Model>",
    _(r"{Appareil/Année-Mois}"): "<Exif.Image.Model>/%Y-%m",
    _(r"{Année-Mois - Pays}"): "%Y-%m - <Iptc.Application2.CountryName>",
    _(r"{Année-Mois - Ville}"): r"%Y-%m - <Iptc.Application2.City>",
    _(r"{Année-Mois-Jour}"): r"%Y-%m-%d",
    _(r"{Année-Mois-Jour - Ville}"): r"%Y-%m-%d - <Iptc.Application2.City>",
    _(
        r"{Année-Mois-Jour - Pays - Ville}"
    ): r"%Y-%m-%d - <Iptc.Application2.CountryName> - <Iptc.Application2.City>",
    _(r"{Ville}"): r"<Iptc.Application2.City>",
    _(r"{Pays}"): r"<Iptc.Application2.CountryName>",
    _(r"{Garder le nom de fichier}"): "",
    _(r"{Grouper par date}"): "{group}",
}


MAIN_TAB_WIDGETS = {
    "dir": {
        "label": _("Dossier source"),
        "tooltip": _(
            "Chemin du dossier à analyser, Ajustez le chemin dans la section 'Source'"
        ),
        "placeholder": _("D:\CleUsb"),
    },
    "dir": {
        "label": _("Dossier destination"),
        "tooltip": _(
            "Chemin du dossier à analyser, Ajuster le chemin dans la section 'Destination'"
        ),
        "placeholder": _(r"D:\User\Images"),
    },
    "scan_exts": {
        "label": _("Extensions"),
        "tooltip": _(
            "Liste des extentions séparées par des virgules\n\n  1. Definissez les dossiers à analyser\n  2. Scannez : bouton '1. Scanner'\n  3. Selectionnez les extentions via 'Outils >  Extentions'\n "
        ),
        "placeholder": "jpg, jpeg, png",
        "combobox_options": [
            "jpg",
            "jpg, jpeg, png",
            "jpg, raw, arw",
            _(r"{media_photos}"),
            _(r"{media_videos}"),
        ],
    },
    "in_dir": {
        "label": _("Dossier"),
        "tooltip": _("Chemin du dossier contenant les photos"),
        "placeholder": _("D:\CleUsb\Images"),
        "fileselector": True,
    },
    "extentions": {
        "label": _("Extensions"),
        "tooltip": _(
            "Liste des extentions séparées par des virgules\n\n  1. Definissez les dossiers à analyser\n  2. Scannez : bouton '1. Scanner'\n  3. Selectionnez les extentions via 'Outils >  Extentions'\n"
        ),
        "placeholder": "jpg, jpeg, png",
        "combobox_options": [
            "jpg",
            "jpg, jpeg, png",
            "jpg, raw, arw",
            _(r"{media_photos}"),
            _(r"{media_videos}"),
        ],
    },
    "cameras": {
        "label": _("Appareils photo"),
        "tooltip": _(
            "Liste des appareils photos séparés par des virgules\nNe copie que les photos prises par ces appareils\n\nSi le champs est laissé vide, le paramètre est ignoré\n\n  1. Definissez les dossiers à analyser\n  2. Scannez : bouton '1. Scanner'\n  3. Selectionnez les appareils via 'Outils >  Appareils'\n"
        ),
        "placeholder": "DSLR100",
    },
    "excluded_dirs": {
        "label": (_("Exclure"), _("Inclure")),
        "tooltip": _(
            "Liste d'éléments à inclure ou exclure séparés par des virgules.\nLes chemins précisés sont relatifs au dossier 'Source'"
        ),
        "placeholder": _("chemin/relatif/à/source"),
        "fileselector": False,
    },
    "out_dir": {
        "label": _("Dossier"),
        "tooltip": _("Chemin du dossier où copier les photos"),
        "placeholder": _(r"C:\Users\_Mon_Nom_\Images"),
        "fileselector": True,
    },
    "out_path_str": {
        "label": _("Chemin relatif"),
        "tooltip": "\n".join(
            (
                _(" Format du chemin relatif au dossier précédent! "),
                _(" Ce chemin peut être personnalisté via des tags de métadonnés "),
                _("ou des codes de formatage des dates"),
                "",
                _("Formats:\n  - métadonnées : {tag} ou <tag>\n  - date : %x\n"),
                "Voir 'Outils > Métadonnées' et 'Outils > Date' pour la liste\ncomplète et les définitions des chaines de remplacement possibles\n",
            )
        ),
        "placeholder": "%Y/%Y-%m",
        "combobox_options": [
            _("{Année/Année-Mois}"),
            _("{Année/Mois}"),
            _(r"{Appareil}"),
            _(r"{Appareil/Année-Mois}"),
            _(r"{Année-Mois - Pays}"),
            _(r"{Année-Mois - Ville}"),
            _("{Grouper par date}"),
        ],
    },
    "filename": {
        "label": _("Nom du fichier"),
        "tooltip": _(
            "Nom à donner aux fichiers, supporte les mêmes formats que 'Chemin relatif'"
        ),
        "placeholder": "<Iptc.Application2.City>",
        "combobox_options": [
            _(r"{Garder le nom de fichier}"),
            _(r"{Année-Mois-Jour}"),
            _(r"{Année-Mois-Jour - Ville}"),
            _(r"{Année-Mois-Jour - Pays - Ville}"),
            _(r"{Ville}"),
            _(r"{Pays}"),
        ],
    },
    "guess_date_from_name": {
        "checkbox": True,
        "label": _("Date depuis nom"),
        "tooltip": _(
            "Essaie d'abord d'obtenir la date de prise de vue depuis le nom de fichier.\nTente d'identifier dans le nom de fichier une date suivant le format précisé.\nUtilisez les formats definis dans l'onglet 'Date'"
        ),
        "placeholder": r"%Y%m%d",
        "combobox_options": [r"%Y%m%d", r"%y%m%d", r"%Y-%m-%d"],
    },
    "group_by_floating_days": {
        "checkbox": True,
        "spinbox": _("jours"),
        "label": _("Grouper | format"),
        "tooltip": _(
            "Groupe les photos par une fenetre de <b>jours</b> glissants selon le <b>format</b> défini.<br>Utiliser le texte de remplacement <b>{group}</b> pour ajuster le chemin relatif et le nom du fichier"
        ),
        "placeholder": _(r"Sortie du %Y%m%d"),
        "combobox_options": [r"%Y%m%d", r"%y%m%d", r"%Y-%m-%d"],
    },
}

# ("file_action", "Simuler", "Ne copie aucun fichier"),
MENU_TOOL_BUTTON = [
    ("verbose", "Debug", _("Affiche les étapes du programme dans le terminal")),
]

MAIN_TAB_BUTTONS = {
    "is_meta": {
        "label": _("metadonnées"),
        "tooltip": _("Obtient les métadonnées des fichiers"),
    },
    "is_md5_file": {
        "label": _("empreinte fichier"),
        "tooltip": _("Calcule l'empreinte md5 du fichier"),
    },
    "is_md5_data": {
        "label": _("empreinte des données"),
        "tooltip": _("Calcule l'empreinte md5 des données"),
    },
    "is_use_cached_datas": {
        "label": _("données du cache"),
        "tooltip": _(
            "Ne recalcule pas les empreintes des fichiers,\nutilise directement les données du cache associées au chemin du fichier.\n/!\\ N'activez uniquement si les données n'ont pas été modifiées depuis le dernier lancement du programme."
        ),
    },
    "gps": {
        "label": "GPS",
        "tooltip": _(
            "Essaie de determiner le lieu de prise de vue à partir des metadonnées gps\nBécessite une connection internet\n/!\\ Peut grandement ralentir l'execution du prgramme"
        ),
    },
    "is_recursive": {
        "label": _("Récursif"),
        "tooltip": _("Cherche dans les sous dossier du dossier 'Source'"),
    },
    "is_scan_dest": {
        "label": _("Destination"),
        "tooltip": _(
            "Scanne aussi le dossier destination à la recherche de fichiers dupliqués"
        ),
    },
    "is_exclude_dir_regex": {
        "label": _("Regex"),
        "tooltip": _(
            "Utiliser des expressions régulière plutôt que des chemins relatifs"
        ),
    },
    "is_delete_metadatas": {
        "label": _("Effacer metadonnées"),
        "tooltip": _("Supprimer les métadonnées dans le fichier copié"),
    },
    "is_date_from_filesystem": {
        "label": _("Date fichier"),
        "tooltip": _(
            "Cherche aussi la date de création de fichier à défaut\nd'informations trouvées dans les métadonnées"
        ),
    },
    "is_force_date_from_filesystem": {
        "label": _("Forcer"),
        "tooltip": _(
            "Prendre la date de création du fichier plutôt\n que de chercher dans les métadonnées"
        ),
    },
}

ACTION_BUTTONS = {
    "populate": {
        "label": _("1. Scanner"),
        "tooltip": _(
            "A utliser lors du changement des repertoires <b>source</b> et/ou <b>destination</b> ou si les fichiers ont été modifiés/déplacés par un autre programme.<br>Scanne les dossier, calcule les empreintes, recupère les metadonnées et met à jour l'onglet <b>outils</b>"
        ),
    },
    "calculate": {
        "label": _("2. Pré-calculer"),
        "tooltip": _(
            "A utiliser après un changement de paramètre.\nA partir des fichiers trouvés pendant le scan, \ngenere les nouveaux chemins pour les images et affiche un aperçu"
        ),
    },
    "execute": {
        "label": _("3. Executer"),
        "tooltip": _(
            "A partir des chemins pré-calculés , déplace/copie les fichiers,\ninscrit les nouvelles métadonnées si besoin\n(pensez bien a executer '2. Pré-calculer' après tout changement de paramètre)"
        ),
    },
}

DUP_RADIO_BUTTONS = {
    "duplicate": {
        "label": _("Dupliqués"),
        "tooltip": _(
            "Activez pour ne pas déplacer les doubles.\nIgnore simplement les fichiers si un a déjà été déplacé"
        ),
    },
    "file": {
        "label": _("Fichier"),
        "tooltip": _("Compare les sommes md5 des fichiers"),
    },
    "data": {
        "label": _("Données"),
        "tooltip": _(
            "Compare les md5 des données brutes à l'interieur des fichiers média.\nUtile pour les fichiers dont les métanonnées ont changées"
        ),
    },
    "date": {
        "label": _("Date"),
        "tooltip": _("Compare la date des fichiers pour reperer les doubles"),
    },
}
#            ),
#            ("NEW_LINE", "", 0),
#            ("control_hash", _("Dupliqués"), _("Ne copie pas les fichiers dupliqués")),
#            (
#                "hash_populate",
#                "Scan dest",
#                _("Empeche la copie de fichiers lorsqu'ils sont déjà présent dans le dossier de destinaion"),
#            ),
#            (
#                "hash_reset",
#                "Reset",
#                _("Oublie les fichiers déjà déplacés entre deux exécutions du programme"),
#            ),
#        ]

GPS_HELP_TEXT = "\n".join(
    (
        _("Résolution des noms de rue, ville, region, pays :"),
        "",
        _("Ajoute la localisation à partir des données GPS à toutes les photos"),
        _("définies par les paramètres de l'onglet 'Main', section 'Source'. "),
        "",
        _(r"/!\ envoie les coordonnées GPS au site openstreetmap"),
        _("La résolution des noms peut prendre du temps : 3-4 sec par photos"),
    )
)
