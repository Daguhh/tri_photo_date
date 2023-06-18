
from pathlib import Path
import gettext

from tri_photo_date.config.config_loader import CONFIG
from tri_photo_date.config.config_paths import LOCALES_DIR
from tri_photo_date.utils.small_tools import limited_string, bytes2human


lang = CONFIG[("interface", "lang")]
trad = gettext.translation("base", localedir=LOCALES_DIR, languages=[lang])
trad.install()
_ = trad.gettext  # Greek

FILE_ACTION_TXT = {
    1: _("Simulation du déplacement de {} vers {}"),
    2: _("Copie du fichier {} vers {}"),
    3: _("Déplacement du fichier {} vers {}"),
}


PROGBAR_TXT_SCAN_START = _("Recherche des fichiers dans {} ...")
PROGBAR_TXT_SCAN_SRCDIR = _("{} / {} - Calcul de l'empreinte et chargement des métadonnées...")
PROGBAR_TXT_SCAN_DESTDIR = _("{} / {} - Scan des fichiers dans le dossier de destination...")
PROGBAR_TXT_COMPUTE_FILES = _("{} / {} - {} - Résolution des nouveaux chemins...")
PROGBAR_TXT_DONE = _("Fait!")
PROGBAR_TXT_COMPUTE_GROUPS_START = _("Fait! Tri des fichiers pour groupement par date...")
PROGBAR_TXT_COMPUTE_GROUPS = _("{} / {} - {} - Groupement des fichiers par date")
PROGBAR_TXT_EXECUTE_FCT = lambda a, b, c, d, e: limited_string("".join(
                (
                    f"{bytes2human(a)}/ {bytes2human(b)}",
                    " - ",
                    FILE_ACTION_TXT[c].format(
                        Path(d).name, limited_string(Path(e).parent.name)
                    ),
                )
            ), limit=90)

PROGBAR_TXT_EXECUTE_DONE = _("Fait! {} fichiers ont été déplacés soit un total de {}")


