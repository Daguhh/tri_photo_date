
from tri_photo_date.utils.config_loader import CONFIG
from tri_photo_date.utils.config_paths import LOCALES_DIR
lang = CONFIG['lang']

import gettext
trad = gettext.translation('base', localedir=LOCALES_DIR, languages=[lang])
trad.install()
_ = trad.gettext # Greek

MEDIA_FORMATS = {
    _(r"{media_photos}") : "jpg, jpeg, png, webp, bmp, ico, tiff, heif, heic, svg, raw, arw, cr2, nrw, k25, apng, avif, gif, svg",
    _(r"{media_videos}") : "webm, mkv, flv, ogg, gif, avi, mov, asf, mp4, m4v, mpg, mp2, mpeg, mpv, 3gp, 3g2, flv"
}

REL_PATH_FORMATS = {
    _(r"{Année/Année-Mois}") : r"%Y/%Y-%m",
    _(r"{Année/Mois}") : r"%Y/%m",
    _(r"{Appareil/Année-Mois}") : "<Exif.Image.Model>/%Y-%m",
    _(r"{Année-Mois - Pays}") : "%Y-%m - <Iptc.Application2.CountryName>",
    _(r"{Année-Mois - Ville}") : r"%Y-%m - <Iptc.Application2.City>",
    _(r"{Année-Mois-Jour - Ville}") : r"%Y-%m-%d - <Iptc.Application2.City>",
    _(r"{Année-Mois-Jour - Pays - Ville}") : r"%Y-%m-%d - <Iptc.Application2.CountryName> - <Iptc.Application2.City>",
    _(r"{Garder le nom de fichier}") : "",
}

#REL_PATH_GROUP_FORMATS = {
#    _(r"{Group}") :


MAIN_TAB_WIDGETS = {
    'in_dir' : {
        'label' : _("Dossier"),
        'tooltip' : _("Chemin du dossier contenant les photos"),
        'placeholder' : _("D:\CleUsb\Images"),
        'fileselector' : True,
    },
    'extentions': {
        'label' : _("Extensions"),
        'tooltip' : _("Liste des extentions séparées par des virgules\nVoir onglet Extentions"),
        'placeholder' : "jpg, jpeg, png",
        'combobox_options' : ["jpg", "jpg, jpeg, png", "jpg, raw, arw", _(r'{media_photos}'),_(r'{media_videos}')]
    },
    'cameras' : {
        'label' : _('Appareils photo'),
        'tooltip' : _('Liste des appareils photos séparés par des virgules\nNe copie que les photos prises par ces appareils\n\nSi le champs est laissé vide, le paramètre est ignoré'),
        'placeholder' : 'DSLR100',
    },
    'out_dir' : {
        'label' : _("Dossier"),
        'tooltip' : _("Chemin du dossier où copier les photos"),
        'placeholder' : _(r"C:\Users\_Mon_Nom_\Images"),
        'fileselector' : True,
    },
    'out_path_str' : {
        'label' : _("Chemin relatif"),
        'tooltip' : "\n".join((_("Format du chemin relatif au dossier précédent!"), _("Utilisez des Tags de métadonnées (onglet Metadata)"), _("ou des codes de formatage des dates (onglet Date)"),"",_("Pour utiliser un tag de métadonnée, il suffit d'ajouter dans le chemin un tag entre crochets :"),"    <tag>",_("ou"),r"   {tag}",)),
        'placeholder' : "%Y/%Y-%m",
        'combobox_options' : [_("{Année/Année-Mois}"), _("{Année/Mois}"), _(r"{Appareil/Année-Mois}"), _(r"{Année-Mois - Pays}"), _(r"{Année-Mois - Ville}")]
    },
    'filename': {
        'label' : _("Nom du fichier"),
        'tooltip' : _("Nom à donner aux fichiers, supporte les mêmes formats que 'Chemin relatif'"),
        'placeholder' : "<Iptc.Application2.City>",
        'combobox_options' : [_(r"{Garder le nom de fichier}"),_(r"{Année-Mois-Jour - Ville}"),_(r"{Année-Mois-Jour - Pays - Ville}")]
    },
    'guess_date_from_name': {
        'checkbox' : True,
        'label' : _("Date depuis nom"),
        'tooltip' : _("Essaie d'abord d'obtenir la date de prise de vue depuis le nom de fichier.\nTente d'identifier dans le nom de fichier une date suivant le format précisé.\nUtilisez les formats definis dans l'onglet 'Date'"),
        'placeholder' : r'%Y%m%d',
        'combobox_options' : [r'%Y%m%d', r'%y%m%d', r'%Y-%m-%d']
    },
    'group_by_floating_days': {
        'checkbox' : True,
        'spinbox' : _('jours'),
        'label' : _("format"),
        'tooltip' : _("Groupe les photos par une fenetre de <b>jours</b> glissants selon le <b>format</b> défini.<br>Utiliser le texte de remplacement <b>{group}</b> pour ajuster le chemin relatif et le nom du fichier"),
        'placeholder' : _(r'Sortie du %Y%m%d'),
        'combobox_options' : [r'%Y%m%d', r'%y%m%d', r'%Y-%m-%d']
    }
}

            #("file_action", "Simuler", "Ne copie aucun fichier"),
MENU_TOOL_BUTTON = [
            ("verbose", "Debug", _("Affiche les étapes du programme dans le terminal")),
]
MAIN_TAB_BUTTONS = [
            (
                "gps",
                "GPS",
                _("Essaie de determiner le lieu de prise de vue à partir des metadonnées gps\nBécessite une connection internet\n/!\\ Peut grandement ralentir l'execution du prgramme"),
            ),
            (
                "is_recursive",
                _("Recherche récursive"),
                _("Cherche dans les sous dossier du dossier 'Source'"),
            ),
            ("NEW_LINE", "", 0),
            ("control_hash", _("Dupliqués"), _("Ne copie pas les fichiers dupliqués")),
            (
                "hash_populate",
                "Scan dest",
                _("Empeche la copie de fichiers lorsqu'ils sont déjà présent dans le dossier de destinaion"),
            ),
            (
                "hash_reset",
                "Reset",
                _("Oublie les fichiers déjà déplacés entre deux exécutions du programme"),
            ),
        ]

GPS_HELP_TEXT = "\n".join((
    _("Résolution des noms de rue, ville, region, pays :"),
    "",
    _("Ajoute la localisation à partir des données GPS à toutes les photos"),
    _("définies par les paramètres de l'onglet 'Main', section 'Source'. "),
    "",
    _(r"/!\ envoie les coordonnées GPS au site openstreetmap"),
    _("La résolution des noms peut prendre du temps : 3-4 sec par photos")
))
