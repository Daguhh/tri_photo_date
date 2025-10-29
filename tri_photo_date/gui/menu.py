import sys
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIntValidator
from PyQt6.QtWidgets import (
    QMainWindow,
    QApplication,
    QMenu,
    QMessageBox,
    QMenuBar,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QLabel,
    QPushButton,
    QSpinBox,
    QCheckBox,
)

from PyQt6.QtGui import QAction, QActionGroup
import logging
#import pkg_resources

from pathlib import Path
import os

from tri_photo_date.config.config_loader import LANG_LIST
from tri_photo_date.config.config_paths import (
    LICENSE_PATH,
    AKNOLEG_PATH,
    README_PATH,
    CONFIG_PATH,
    ABOUT_PATH,
    LOCALES_DIR,
    HELP_PATH,
)
from tri_photo_date.utils.constants import (
    GUI_ADVANCED,
    GUI_NORMAL,
    GUI_SIMPLIFIED,
)
from tri_photo_date.gui.human_text import WARNING_SWITCH_SIMPLIFY_MODE

def set_global_config(lang='en', size="1", mode=GUI_ADVANCED):

    global LANG
    LANG = lang

    import gettext

    trad = gettext.translation("base", localedir=LOCALES_DIR, languages=[lang])
    trad.install()

    global _
    _ = trad.gettext  # Greek

    os.environ["QT_SCALE_FACTOR"] = size

    global GUI_MODE
    GUI_MODE = mode



class WindowMenu(QMenuBar):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        # File menu
        file_menu = self.addMenu(_("Fichier"))

        self.load_action = QAction(_("Charger"), self)
        file_menu.addAction(self.load_action)
        self.load_action.setDisabled(True)

        self.save_action = QAction(_("Sauvegarder"), self)
        file_menu.addAction(self.save_action)
        self.save_action.setDisabled(True)

        self.quit_action = QAction(_("Quitter"))
        file_menu.addAction(self.quit_action)
        self.quit_action.triggered.connect(lambda _ : self.parent.quit())

        #file_menu.setDisabled(True)

        # Edit menu
        edit_menu = self.addMenu(_("Edition"))

        self.config_action = QAction(_("Ouvrir le fichier de configuration"), self)
        edit_menu.addAction(self.config_action)

        self.set_settings_action = QAction(_("Configurer les filtres des fichiers"), self)
        edit_menu.addAction(self.set_settings_action)

        # option_2_action = QAction('Option 2', self)
        # edit_menu.addAction(option_2_action)

        ### Interface menu ###
        view_menu = self.addMenu(_("Interface"))

        # Interface mode
        mode_menu = QMenu(_("Apparence"), self)
        full_action = QAction(_("Avancée"), checkable=True)
        simplify_action = QAction(_("Simplifiée"), checkable=True)

        full_action.setData(GUI_ADVANCED)
        simplify_action.setData(GUI_SIMPLIFIED)

        self.mode_group = QActionGroup(self)
        self.mode_group.setExclusionPolicy(
            QActionGroup.ExclusionPolicy.ExclusiveOptional
        )
        mode_menu.addAction(self.mode_group.addAction(full_action))
        mode_menu.addAction(self.mode_group.addAction(simplify_action))

        # for action in self.mode_group.actions():
        #    if action.data() == GUI_MODE
        #        action.setChecked(True)
        # mode_menu.setDisabled(True)

        # Interface size
        size_menu = QMenu(_("Taille"), self)
        self.size_group = QActionGroup(self)
        self.size_group.setExclusionPolicy(
            QActionGroup.ExclusionPolicy.ExclusiveOptional
        )
        for s in ["0.8", "0.9", "1", "1.1", "1.2", "1.3", "1.5", "1.75", "2"]:
            size_act = QAction(str(s), checkable=True)
            size_act.setData(s)
            size_menu.addAction(self.size_group.addAction(size_act))
            # size_act.triggered.connect(lambda x: self.set_interface_size(s))

        # for action in self.size_group.actions():
        #    # print(action.data(), GUI_SIZE
        #    if action.data() == GUI_SIZE
        #        action.setChecked(True)

        lang_menu = QMenu(_("Langue"), self)
        self.lang_group = QActionGroup(self)
        self.lang_group.setExclusionPolicy(
            QActionGroup.ExclusionPolicy.ExclusiveOptional
        )

        for lang in [_('locale')] + LANG_LIST:
            lang_act = QAction(lang, checkable=True)
            lang_act.setData(lang)
            lang_menu.addAction(self.lang_group.addAction(lang_act))

        # for action in self.lang_group.actions():
        #    if action.data() == GUI_LANG
        #        action.setChecked(True)

        view_menu.addMenu(mode_menu)
        view_menu.addMenu(size_menu)
        view_menu.addMenu(lang_menu)

        ### tools ###
        tool_menu = self.addMenu(_("Outils"))

        self.debug_action = QAction("Debug", self, checkable=True)
        tool_menu.addAction(self.debug_action)
        self.debug_action.setToolTip(
            _("Affiche les étapes du programme dans le terminal")
        )

        self.mode_group.triggered.connect(self.set_interface_mode)
        self.size_group.triggered.connect(self.set_interface_size)
        self.lang_group.triggered.connect(self.set_language)

        # About menu
        about_menu = self.addMenu(_("A propos"))
        about_action = QAction(_("A propos"), self)
        about_menu.addAction(about_action)
        about_action.triggered.connect(self.show_about)

        license_action = QAction(_("License"), self)
        about_menu.addAction(license_action)
        license_action.triggered.connect(self.show_license)

        ack_action = QAction(_("Credits"), self)
        about_menu.addAction(ack_action)
        ack_action.triggered.connect(self.load_acknowledgments)

        help_action = QAction(_("Aide"), self)
        about_menu.addAction(help_action)
        help_action.triggered.connect(self.show_help)

    def load(self):
        pass

    def save(self):
        pass

    def set_language(self, lang):
        QTimer.singleShot(0, self.show_message_box)

    def set_interface_mode(self, mode):
        msg = ""
        if mode.data() == GUI_SIMPLIFIED:
            msg = WARNING_SWITCH_SIMPLIFY_MODE
            QTimer.singleShot(0, lambda msg=msg: self.show_message_box_2(msg))
        else:
            QTimer.singleShot(0, lambda msg=msg: self.show_message_box(msg))

    def set_interface_size(self, size):
        print('change size triggered')
        QTimer.singleShot(0, self.show_message_box)

    def show_message_box(self, msg=""):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Icon.Warning)
        msgBox.setWindowTitle(_("Configuration de l'interface"))
        msg = (
            msg
            + "\n\n" * bool(msg)
            + _(
                "Les changements prendrons effet au prochain lancement.\nQuitter l'interface ?"
            )
        )
        msgBox.setText(msg)
        msgBox.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        msgBox.setDefaultButton(QMessageBox.StandardButton.Cancel)
        button_clicked = msgBox.exec()
        if button_clicked == QMessageBox.StandardButton.Ok:
            self.parent.quit()
        # elif button_clicked == QMessageBox.Cancel:

    def show_message_box_2(self, msg=""):
        msg = (
            msg
            + "\n\n" * bool(msg)
            + _(
                "Les changements prendrons effet au prochain lancement.\nQuitter l'interface ?"
            )
        )
        msg_box = QMessageBox()
        msg_box.setText(msg)
        apply_n_continue_button = msg_box.addButton("Apply and continue", QMessageBox.ButtonRole.RejectRole)
        quit_n_keep_button = msg_box.addButton("Quit and keep config", QMessageBox.ButtonRole.AcceptRole)
        quit_n_reset_button = msg_box.addButton("Quit and reset config", QMessageBox.ButtonRole.DestructiveRole)
        #apply_button = msg_box.addButton("Apply and Continue", QMessageBox.ActionRole)

        msg_box.exec()

        if msg_box.clickedButton() == quit_n_reset_button:
            # Perform the reset action
            self.parent.quit_n_reset()
        elif msg_box.clickedButton() == quit_n_keep_button:
            # Perform the quit action
            self.parent.quit()
        elif msg_box.clickedButton() == apply_n_continue_button:
            # Continue running the application
            pass  # Replace 'pass' with any other code to run when the user clicks "Don't Quit"

    def show_license(self):
        license_text = open(LICENSE_PATH).read()
        QMessageBox.about(self, _("License"), license_text)

    def show_about(self):
        text = open(str(ABOUT_PATH).format(LANG)).read()
        msgBox = QMessageBox()
        msgBox.setWindowTitle(_("A propos"))
        msgBox.setTextFormat(Qt.TextFormat.MarkdownText)
        msgBox.setText(text)
        msgBox.exec()

    def load_acknowledgments(self):
        text = open(str(AKNOLEG_PATH).format(LANG)).read()
        msgBox = QMessageBox()
        msgBox.setWindowTitle(_("README"))
        msgBox.setTextFormat(Qt.TextFormat.MarkdownText)
        msgBox.setText(text)
        msgBox.exec()

    def show_help(self):
        readme_text = open(str(HELP_PATH).format(LANG)).read()
        msgBox = QMessageBox()
        msgBox.setWindowTitle(_("README"))
        msgBox.setTextFormat(Qt.TextFormat.MarkdownText)
        msgBox.setText(readme_text)
        msgBox.exec()

    def open_file_browser(self):
        import subprocess
        import platform

        if platform.system() == "Windows":
            subprocess.run(("explorer", str(CONFIG_PATH)))
        elif platform.system() == "Linux":
            subprocess.run(("xdg-open", str(CONFIG_PATH)))

    def debug_toggle(self, value):
        pass

class SettingFilePopup(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Configuration générale")

        # Create the layouts and widgets
        layout = QVBoxLayout()

        sublayout = QHBoxLayout()
        self.ckb_max_hash = QCheckBox()
        label = QLabel(_("Empreinte partielles maximum"))
        self.spin_max_hash = QSpinBox()
        self.spin_max_hash.setRange(0, 10000)
        unit = QLabel("MB")
        sublayout.addWidget(self.ckb_max_hash)
        sublayout.addWidget(label)
        sublayout.addWidget(self.spin_max_hash)
        sublayout.addWidget(unit)
        layout.addLayout(sublayout)

        sublayout = QHBoxLayout()
        self.ckb_min_size = QCheckBox()
        label = QLabel(_("Ignorer fichiers plus petit que"))
        self.spin_min_size = QSpinBox()
        self.spin_min_size.setRange(0, 1000 * 1000)
        unit = QLabel("KB")
        sublayout.addWidget(self.ckb_min_size)
        sublayout.addWidget(label)
        sublayout.addWidget(self.spin_min_size)
        sublayout.addWidget(unit)
        layout.addLayout(sublayout)

        sublayout = QHBoxLayout()
        self.ckb_max_size = QCheckBox()
        label = QLabel(_("Ignorer les fichiers plus grand que"))
        unit = QLabel("MB")
        self.spin_max_size = QSpinBox()
        self.spin_max_size.setRange(1, 100000)
        sublayout.addWidget(self.ckb_max_size)
        sublayout.addWidget(label)
        sublayout.addWidget(self.spin_max_size)
        sublayout.addWidget(unit)
        layout.addLayout(sublayout)

        button = QPushButton("OK")
        button.clicked.connect(self.accept)
        layout.addWidget(button)

        self.setLayout(layout)

    def get_values(self):
        # Return the entered values as a tuple of integers
        dct = {
            "max_hash": (self.ckb_max_hash.checkState(), self.spin_max_hash.value()),
            "max_size": (self.ckb_max_size.checkState(), self.spin_max_size.value()),
            "min_size": (self.ckb_min_size.checkState(), self.spin_min_size.value()),
        }
        return dct

