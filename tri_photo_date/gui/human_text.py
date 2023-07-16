from tri_photo_date.config.config_loader import CONFIG
from tri_photo_date.config.config_paths import LOCALES_DIR

import gettext

from tri_photo_date.utils.small_tools import get_lang

lang = CONFIG["interface"]["lang"]
lang = get_lang(lang)
trad = gettext.translation("base", localedir=LOCALES_DIR, languages=[lang])
trad.install()
_ = trad.gettext  # Greek

WARNING_SWITCH_SIMPLIFY_MODE = _(
    "Attention, les paramètres de la section 'options' ne seront plus\naccessibles mais garderont leur effets.\n\nVous pouvez garder les paramètres actuels ou revenir aux paramètres par défaut."
)

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

MEDIA_FORMATS = {
    _(
        r"{media_photos}"
    ):"jpg,jpeg,png,webp,bmp,ico,tiff,heif,heic,svg,raw,arw,cr2,nrw,k25,apng,avif,gif,svg",
    _(
        r"{media_videos}"
    ):"webm,mkv,flv,ogg,gif,avi,mov,asf,mp4,m4v,mpg,mp2,mpeg,mpv,3gp,3g2,flv",
    _(
        r"{media_videos_n_photos}"
    ):"jpg,jpeg,png,webp,bmp,ico,tiff,heif,heic,svg,raw,arw,cr2,nrw,k25,apng,avif,gif,svg,webm,mkv,flv,ogg,gif,avi,mov,asf,mp4,m4v,mpg,mp2,mpeg,mpv,3gp,3g2,flv"
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


HUMAN_TEXT = {
    "files": {
        "is_max_hash_size": {},
        "max_hash_size": {},
        "is_min_size": {},
        "min_size": {},
        "is_max_size": {},
        "max_size": {}
    },
    "scan": {
        "src_dir": {
            "label" : _("Dossier source"),
            "tooltip" : _("Chemin du dossier \u00e0 analyser, Ajustez le chemin dans la section 'Source'"),
            "placeholder": _("D:\\CleUsb")
        },
        "dest_dir": {
            "label": _("Dossier destination"),
            "tooltip": _("Chemin du dossier \u00e0 analyser, Ajuster le chemin dans la section 'Destination'"),
            "placeholder": _("D:\\User\\Images")
        },
        "extentions": {
            "label": _("Extensions"),
            "tooltip": _("Liste des extentions de fichiers à scanner.\nListe des extention séparées par des virgules\n"),
            "placeholder": "jpg, jpeg, png",
            "combobox_options": [
                "jpg",
                "jpg, jpeg, png",
                "jpg, raw, arw",
                _(r"{media_photos}"),
                _(r"{media_videos}"),
                _(r"{media_videos_n_photos}")
            ]
        },
        "is_recursive": {
            "label": _("R\u00e9cursif"),
            "tooltip": _("Cherche dans les sous dossier du dossier 'Source'")
        },
        "is_meta": {
            "label": _("metadonn\u00e9es"),
            "tooltip": _("Obtient les m\u00e9tadonn\u00e9es des fichiers")
        },
        "is_md5_file": {
            "label": _("empreinte fichier"),
            "tooltip": _("Calcule l'empreinte md5 du fichier")
        },
        "is_md5_data": {
            "label": _("empreinte des donn\u00e9es"),
            "tooltip": _("Calcule l'empreinte md5 des donn\u00e9es")
        },
        "is_use_cached_datas": {
            "label": _("donn\u00e9es du cache"),
            "tooltip": _("Ne recalcule pas les empreintes des fichiers,\nutilise directement les donn\u00e9es du cache associ\u00e9es au chemin du fichier.\n/!\\ N'activez uniquement si les donn\u00e9es n'ont pas \u00e9t\u00e9 modifi\u00e9es depuis le dernier lancement du programme.")
        }
    },
    "source": {
        "dir": {
            "label": _("Dossier"),
            "tooltip": _("Chemin du dossier contenant les photos"),
            "placeholder": _("D:\\CleUsb\\Images"),
            "fileselector": True
        },
        "extentions": {
            "label": _("Extensions"),
            "tooltip": _("Liste des extentions s\u00e9par\u00e9es par des virgules\n\n  1. Definissez les dossiers \u00e0 analyser\n  2. Scannez : bouton '1. Scanner'\n  3. Selectionnez les extentions via 'Outils >  Extentions'\n"),
            "placeholder": "jpg, jpeg, png",
            "combobox_options": [
                "jpg",
                "jpg, jpeg, png",
                "jpg, raw, arw",
                _(r"{media_photos}"),
                _(r"{media_videos}")
            ]
        },
        "cameras": {
            "label": [
                _("Exclure les appareils"),
                _("Inclure les appareils")
            ],
            "tooltip": _("Liste des appareils photos s\u00e9par\u00e9s par des virgules\nNe copie que les photos prises par ces appareils\n\nSi le champs est laiss\u00e9 vide, le param\u00e8tre est ignor\u00e9\n\n  1. Definissez les dossiers \u00e0 analyser\n  2. Scannez : bouton '1. Scanner'\n  3. Selectionnez les appareils via 'Outils >  Appareils'\n"),
            "placeholder": "DSLR100"
        },
        "is_recursive": {
            "label": _("R\u00e9cursif"),
            "tooltip": _("Cherche dans les sous dossier du dossier 'Source'")
        },
        "excluded_dirs": {
            "label": [
                _("Exclure"),
                _("Inclure")
            ],
            "tooltip": _("Liste d'\u00e9l\u00e9ments \u00e0 inclure ou exclure s\u00e9par\u00e9s par des virgules.\nLes chemins pr\u00e9cis\u00e9s sont relatifs au dossier 'Source'"),
            "placeholder": _("chemin/relatif/\u00e0/source"),
            "fileselector": False
        },
        "is_exclude_dir_regex": {
            "label": "Regex",
            "tooltip": _("Utiliser des expressions r\u00e9guli\u00e8re plut\u00f4t que des chemins relatifs")
        }
    },
    "destination": {
        "out_dir": {
            "label": _("Dossier"),
            "tooltip": _("Chemin du dossier o\u00f9 copier les photos"),
            "placeholder": _("C:\\Users\\_Mon_Nom_\\Images"),
            "fileselector": True
        },
        "out_path_str": {
            "label": _("Chemin relatif"),
            "tooltip": _(" Format du chemin relatif au dossier pr\u00e9c\u00e9dent! \n Ce chemin peut \u00eatre personnalist\u00e9 via des tags de m\u00e9tadonn\u00e9s \nou des codes de formatage des dates\n\nFormats:\n  - m\u00e9tadonn\u00e9es : {tag} ou <tag>\n  - date : %x\n\nVoir 'Outils > M\u00e9tadonn\u00e9es' et 'Outils > Date' pour la liste\ncompl\u00e8te et les d\u00e9finitions des chaines de remplacement possibles\n"),
            "placeholder": "%Y/%Y-%m",
            "combobox_options": [
                _("{Ann\u00e9e/Ann\u00e9e-Mois}"),
                _("{Ann\u00e9e/Mois}"),
                _(r"{Appareil}"),
                _("{Appareil/Ann\u00e9e-Mois}"),
                _("{Ann\u00e9e-Mois - Pays}"),
                _("{Ann\u00e9e-Mois - Ville}"),
                _("{Grouper par date}")
            ]
        },
        "filename": {
            "label": _("Nom du fichier"),
            "tooltip": _("Nom \u00e0 donner aux fichiers, supporte les m\u00eames formats que 'Chemin relatif'"),
            "placeholder": "<Iptc.Application2.City>",
            "combobox_options": [
                _("{Garder le nom de fichier}"),
                _("{Ann\u00e9e-Mois-Jour}"),
                _("{Ann\u00e9e-Mois-Jour - Ville}"),
                _("{Ann\u00e9e-Mois-Jour - Pays - Ville}"),
                _(r"{Ville}"),
                _(r"{Pays}")
            ]
        }
    },
    "action": {
        "populate": {
            "label": _("1. Scanner"),
            "tooltip": _("A utliser lors du changement des repertoires <b>source</b> et/ou <b>destination</b> ou si les fichiers ont \u00e9t\u00e9 modifi\u00e9s/d\u00e9plac\u00e9s par un autre programme.<br>Scanne les dossier, calcule les empreintes, recup\u00e8re les metadonn\u00e9es et met \u00e0 jour l'onglet <b>outils</b>")
        },
        "calculate": {
            "label": _("2. Pr\u00e9-calculer"),
            "tooltip": _("A utiliser apr\u00e8s un changement de param\u00e8tre.\nA partir des fichiers trouv\u00e9s pendant le scan, \ngenere les nouveaux chemins pour les images et affiche un aper\u00e7u")
        },
        "execute": {
            "label": _("3. Executer"),
            "tooltip": _("A partir des chemins pr\u00e9-calcul\u00e9s , d\u00e9place/copie les fichiers,\ninscrit les nouvelles m\u00e9tadonn\u00e9es si besoin\n(pensez bien a executer '2. Pr\u00e9-calculer' apr\u00e8s tout changement de param\u00e8tre)")
        }
    },
    "duplicates": {
        "is_duplicate": {
            "label": _("Dupliqu\u00e9s"),
            "tooltip": _("Activez pour ne pas d\u00e9placer les doubles.\nIgnore simplement les fichiers si un a d\u00e9j\u00e0 \u00e9t\u00e9 d\u00e9plac\u00e9")
        },
        "file": {
            "label": _("Fichier"),
            "tooltip": _("Compare les sommes md5 des fichiers")
        },
        "data": {
            "label": _("Donn\u00e9es"),
            "tooltip": _("Compare les md5 des donn\u00e9es brutes \u00e0 l'interieur des fichiers m\u00e9dia.\nUtile pour les fichiers dont les m\u00e9tanonn\u00e9es ont chang\u00e9es")
        },
        "date": {
            "label": _("Date"),
            "tooltip": _("Compare la date des fichiers pour reperer les doubles")
        },
        "is_scan_dest": {
            "label": _("Destination"),
            "tooltip": _("Scanne aussi le dossier destination \u00e0 la recherche de fichiers dupliqu\u00e9s")
        }
    },
    "options": {
        "general": {
            "is_delete_metadatas": {
                "label": _("Effacer metadonn\u00e9es"),
                "tooltip": _("Supprimer les m\u00e9tadonn\u00e9es dans le fichier copi\u00e9")
            },
            "is_date_from_filesystem": {
                "label": _("Date fichier"),
                "tooltip": _("Cherche aussi la date de cr\u00e9ation de fichier \u00e0 d\u00e9faut\nd'informations trouv\u00e9es dans les m\u00e9tadonn\u00e9es")
            },
            "is_force_date_from_filesystem": {
                "label": _("Forcer"),
                "tooltip": _("Prendre la date de cr\u00e9ation du fichier plut\u00f4t\n que de chercher dans les m\u00e9tadonn\u00e9es")
            }
        },
        "name": {
            "guess_date_from_name": {
                "checkbox": True,
                "label": _("Date depuis nom"),
                "tooltip": _("Essaie d'abord d'obtenir la date de prise de vue depuis le nom de fichier.\nTente d'identifier dans le nom de fichier une date suivant le format pr\u00e9cis\u00e9.\nUtilisez les formats definis dans l'onglet 'Date'"),
                "placeholder": "%Y%m%d",
                "combobox_options": [
                    "%Y%m%d",
                    "%y%m%d",
                    "%Y-%m-%d"
                ]
            }
        },
        "group": {
            "group_by_floating_days": {
                "checkbox": True,
                "spinbox": _("jours"),
                "label": _("Grouper | format"),
                "tooltip": _("Groupe les photos par une fenetre de <b>jours</b> glissants selon le <b>format</b> d\u00e9fini.<br>Utiliser le texte de remplacement <b>{group}</b> pour ajuster le chemin relatif et le nom du fichier"),
                "placeholder": _("Sortie du %Y%m%d"),
                "combobox_options": [
                    "%Y%m%d",
                    "%y%m%d",
                    "%Y-%m-%d"
                ]
            }
        }
    },
    "gps": {
        "gps": {
            "label": "GPS",
            "tooltip": _("Essaie de determiner le lieu de prise de vue \u00e0 partir des metadonn\u00e9es gps\nB\u00e9cessite une connection internet\n/!\\ Peut grandement ralentir l'execution du prgramme")
        }
    }
}
