import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QMainWindow, QApplication, QAction, QMenu, QRadioButton, QActionGroup, QMessageBox, QMenuBar
import logging
import pkg_resources

from pathlib import Path
import os

from tri_photo_date.utils.config_paths import LICENSE_PATH, AKNOLEG_PATH, README_PATH, CONFIG_PATH, ABOUT_PATH, LOCALES_DIR, HELP_PATH
from tri_photo_date.utils.config_loader import GUI_ADVANCED, GUI_NORMAL, GUI_SIMPLIFIED, LANG_LIST
from tri_photo_date.ordonate_photos import CFG
from tri_photo_date.gui.human_text import MENU_TOOL_BUTTON

lang = CFG['interface.gui_lang']
import gettext
trad = gettext.translation('base', localedir=LOCALES_DIR, languages=[lang])
trad.install()
_ = trad.gettext # Greek

class WindowMenu(QMenuBar):

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent

        # File menu
        file_menu = self.addMenu(_('Fichier'))

        load_action = QAction(_('Charger'), self)
        file_menu.addAction(load_action)
        load_action.triggered.connect(self.load)

        save_action = QAction(_('Sauvegarder'), self)
        file_menu.addAction(save_action)
        save_action.triggered.connect(self.save)

        file_menu.setDisabled(True)

        # Edit menu
        edit_menu = self.addMenu(_('Edition'))

        config_action = QAction(_('Ouvrir le fichier de configuration'), self)
        edit_menu.addAction(config_action)
        config_action.triggered.connect(self.open_file_browser)

        #option_2_action = QAction('Option 2', self)
        #edit_menu.addAction(option_2_action)

        ### Interface menu ###
        view_menu = self.addMenu(_('Interface'))

        # Interface mode
        mode_menu = QMenu(_('Apparence'), self)
        full_action = QAction(_("Avancée"), checkable=True)
        simplify_action = QAction(_("Simplifiée"), checkable=True)

        full_action.setData(GUI_ADVANCED)
        simplify_action.setData(GUI_SIMPLIFIED)

        mode_group = QActionGroup(self)
        mode_group.setExclusionPolicy(QActionGroup.ExclusionPolicy.ExclusiveOptional)
        mode_menu.addAction(mode_group.addAction(full_action))
        mode_menu.addAction(mode_group.addAction(simplify_action))
        mode_group.triggered.connect(self.set_interface_mode)

        for action in mode_group.actions():
            if action.data() == CFG['interface.gui_mode']:
                action.setChecked(True)
        #mode_menu.setDisabled(True)

        # Interface size
        size_menu = QMenu(_('Taille'), self)
        self.size_group = QActionGroup(self)
        self.size_group.setExclusionPolicy(QActionGroup.ExclusionPolicy.ExclusiveOptional)
        for s in ['0.8', '0.9', '1', '1.25', '1.5', '1.75', '2']:
            size_act = QAction(str(s), checkable=True)
            size_act.setData(s)
            size_menu.addAction(self.size_group.addAction(size_act))
            #size_act.triggered.connect(lambda x: self.set_interface_size(s))
        self.size_group.triggered.connect(self.set_interface_size)

        for action in self.size_group.actions():
            #print(action.data(), CFG['gui_size'], type(action.data()))
            if action.data() == CFG['interface.gui_size']:
                action.setChecked(True)

        lang_menu = QMenu(_('Langue'), self)
        lang_group = QActionGroup(self)
        self.size_group = QActionGroup(self)
        self.size_group.setExclusionPolicy(QActionGroup.ExclusionPolicy.ExclusiveOptional)
        for lang in LANG_LIST:
            lang_act = QAction(lang, checkable=True)
            lang_act.setData(lang)
            lang_menu.addAction(lang_group.addAction(lang_act))
        lang_group.triggered.connect(self.set_language)

        for action in lang_group.actions():
            if action.data() == CFG['interface.gui_lang']:
                action.setChecked(True)

        view_menu.addMenu(mode_menu)
        view_menu.addMenu(size_menu)
        view_menu.addMenu(lang_menu)

        ### tools ###
        tool_menu = self.addMenu(_('Outils'))

        debug_action = QAction("Debug", self, checkable=True)
        tool_menu.addAction(debug_action)
        debug_action.triggered.connect(self.debug_toggle)
        debug_action.setChecked(CFG['misc.verbose'])
        debug_action.setToolTip(_("Affiche les étapes du programme dans le terminal"))

        #simulate_action = QAction("Simuler", self, checkable=True)
        #tool_menu.addAction(simulate_action)
        #simulate_action.triggered.connect(self.simulate_toggle)
        #simulate_action.setChecked(CFG['simulate'])
        #simulate_action.setToolTip("Ne copie aucun fichier")

        # About menu
        about_menu = self.addMenu(_('A propos'))
        about_action = QAction(_('About'), self)
        about_menu.addAction(about_action)
        about_action.triggered.connect(self.show_about)

        license_action = QAction(_('License'), self)
        about_menu.addAction(license_action)
        license_action.triggered.connect(self.show_license)

        ack_action = QAction(_('Credits'), self)
        about_menu.addAction(ack_action)
        ack_action.triggered.connect(self.load_acknowledgments)

        help_action = QAction(_('Aide'), self)
        about_menu.addAction(help_action)
        help_action.triggered.connect(self.show_help)


    def load(self):
        pass

    def save(self):
        pass

    def show_message_box(self, msg=''):
        msgBox = QMessageBox()
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setWindowTitle(_("Configuration de l'interface"))
        msg = msg + '\n\n'*bool(msg) +_("Les changements prendrons effet au prochain lancement.\nQuitter l'interface ?")
        msgBox.setText(msg)
        msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        msgBox.setDefaultButton(QMessageBox.Cancel)
        button_clicked = msgBox.exec_()
        if button_clicked == QMessageBox.Ok:
            self.parent.quit()
        #elif button_clicked == QMessageBox.Cancel:

    def set_language(self, lang):

        if CFG['interface.gui_lang'] == lang.data():
            return

        CFG['interface.gui_lang'] = lang.data()

        self.show_message_box()

    def set_interface_mode(self, mode):

        if CFG['interface.gui_mode'] == mode.data():
            return

        CFG['interface.gui_mode'] = mode.data()
        msg=""
        if mode.data() == GUI_SIMPLIFIED:
            msg = "\n".join((
                _("Attention, les paramètres de la section 'options' seront conservés"),
                _("mais ne seront plus modifiables en mode 'simplifié'")
            ))
        self.show_message_box(msg)

    def set_interface_size(self, size):
        #selected_action = self.size_group.checkedAction()
        if CFG['interface.gui_size'] == size.data():
            return

        CFG['interface.gui_size'] = size.data()
        self.show_message_box()

    def show_license(self):
        license_text = open(LICENSE_PATH).read()
        QMessageBox.about(self, _("License"), license_text)

    def show_about(self):
        text = open(str(ABOUT_PATH).format(lang)).read()
        msgBox = QMessageBox()
        msgBox.setWindowTitle(_("A propos"))
        msgBox.setTextFormat(Qt.MarkdownText)
        msgBox.setText(text)
        msgBox.exec_()

    def load_acknowledgments(self):
        text = open(str(AKNOLEG_PATH).format(lang)).read()
        msgBox = QMessageBox()
        msgBox.setWindowTitle(_("README"))
        msgBox.setTextFormat(Qt.MarkdownText)
        msgBox.setText(text)
        msgBox.exec_()

    def show_help(self):
        readme_text = open(str(HELP_PATH).format(lang)).read()
        msgBox = QMessageBox()
        msgBox.setWindowTitle(_("README"))
        msgBox.setTextFormat(Qt.MarkdownText)
        msgBox.setText(readme_text)
        msgBox.exec_()

    def open_file_browser(self):

        import subprocess
        import platform

        if platform.system() == 'Windows':
            subprocess.run(('explorer', str(CONFIG_PATH)))
        elif platform.system() == 'Linux':
            subprocess.run(('xdg-open' , str(CONFIG_PATH)))

    def debug_toggle(self, value):

        CFG['misc.verbose'] = 2 * int(value)

    #def simulate_toggle(self, value):

    #    CFG['simulate'] = 2 * int(value)



