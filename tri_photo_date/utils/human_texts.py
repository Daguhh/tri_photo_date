
from pathlib import Path
import gettext

from tri_photo_date.config.config_loader import CONFIG
from tri_photo_date.config.config_paths import LOCALES_DIR
from tri_photo_date.utils.small_tools import limited_string, bytes2human, get_lang


lang = CONFIG["interface"]["lang"]
lang = get_lang(lang)
trad = gettext.translation("base", localedir=LOCALES_DIR, languages=[lang])
trad.install()
_ = trad.gettext  # Greek

FILE_ACTION_TXT = {
    1: _("Simulation du déplacement de {} vers {}"),
    2: _("Copie du fichier {} vers {}"),
    3: _("Déplacement du fichier {} vers {}"),
}

FILE_ACTION_DONE_EXECUTE_TXT = {
    1: _("Fin de simulation! {} fichiers, {}"),
    2: _("Fait! {} fichiers ont été copiés, soit un total de {}"),
    3: _("Fait! {} fichiers ont été déplacés soit un total de {}")
}


PROGBAR_TXT_SCAN_START = _("Recherche des fichiers dans {} ...")
PROGBAR_TXT_SCAN_SRCDIR = _("Calcul de l'empreinte et chargement des métadonnées...")
PROGBAR_TXT_SCAN_DESTDIR = _("Scan des fichiers dans le dossier de destination...")
PROGBAR_TXT_COMPUTE_FILES = _("{} - Résolution des nouveaux chemins...")
PROGBAR_TXT_DONE = _("Fait!")
PROGBAR_TXT_COMPUTE_GROUPS_START = _("Fait! Tri des fichiers pour groupement par date...")
PROGBAR_TXT_COMPUTE_GROUPS = _("{} - Groupement des fichiers par date")
PROGBAR_TXT_EXECUTE_FCT = lambda c, d, e: limited_string("".join(
                (
                    " - ",
                    limited_string(FILE_ACTION_TXT[c].format(
                        Path(d).name, Path(e).parent.name
                    )),
                )
            ), limit=90)

PROGBAR_TXT_EXECUTE_DONE_FCT = lambda a,b,c : FILE_ACTION_DONE_EXECUTE_TXT[c].format(a,c)


