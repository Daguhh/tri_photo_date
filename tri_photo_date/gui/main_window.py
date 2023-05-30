#!/usr/bin/env python3

from configparser import ConfigParser
import sys, os
from pathlib import Path
import logging
import re


from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QThread, QTimer, QEventLoop, QSize
from PyQt5.QtGui import QKeySequence, QIcon, QPixmap, QClipboard, QStandardItem, QPixmap, QPainter, QFontMetrics
from PyQt5.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
    QCheckBox,
    QFrame,
    QProgressBar,
    QFileDialog,
    QStyle,
    QTabWidget,
    QAction,
    QListView,
    QSizePolicy,
    QMainWindow,
    QMenu,
    QAction,
    QComboBox,
    QTextEdit,
    QButtonGroup,
    QRadioButton,
    QSplitter,
    QToolBox,
    QSpinBox,
)

# Modules
from tri_photo_date.gui.sqlite_view import DatabaseViewer
from tri_photo_date import ordonate_photos
from tri_photo_date.ordonate_photos import CFG
from tri_photo_date.gui.menu import WindowMenu

# Constants
from tri_photo_date.exif import TAG_DESCRIPTION, USEFULL_TAG_DESCRIPTION, EXIF_LOCATION_FIELD
from tri_photo_date.utils.config_loader import FILE_SIMULATE, FILE_COPY, FILE_MOVE, GUI_SIMPLIFIED, GUI_NORMAL, GUI_ADVANCED
from tri_photo_date.gui.strftime_help import DATE_STRFTIME_FORMAT
from tri_photo_date.gui.human_text import MAIN_TAB_WIDGETS, MAIN_TAB_BUTTONS, GPS_HELP_TEXT, MEDIA_FORMATS, REL_PATH_FORMATS
from tri_photo_date.utils.config_paths import STRFTIME_HELP_PATH, ICON_PATH, LOCALES_DIR, IMAGE_DATABASE_PATH


lang = CFG['lang']
import gettext
trad = gettext.translation('base', localedir=LOCALES_DIR, languages=[lang])
trad.install()
_ = trad.gettext # Greek

os.environ['QT_SCALE_FACTOR'] = CFG['gui_size']

class InterupHolder():
    stop_signal = False

from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QRect
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtWidgets import QSplitterHandle, QPushButton


class CustomSplitterHandle(QSplitterHandle):
    clicked = pyqtSignal()

    def __init__(self, orientation=Qt.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.setContentsMargins(0, 0, 0, 0)

        # Create a QPushButton to collapse/show the panel
        self.button = QPushButton(self)
        self.button.setIconSize(QSize(16, 16))
        self.button.setFixedSize(16, 16)
        self.button.setToolTip('Hide Panel')
        self.button.setCheckable(True)

        # Connect the clicked signal of the button to emit the custom clicked signal
        self.button.clicked.connect(self.clicked.emit)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            event.accept()
            return

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.button.setChecked(not self.button.isChecked())
            self.clicked.emit()
            event.accept()
            return

        super().mouseReleaseEvent(event)

    def sizeHint(self):
        return QSize(16, 16)

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.button.isChecked():
            pixmap = QPixmap('arrow-left.png')
        else:
            pixmap = QPixmap('arrow-right.png')
        pixmap = pixmap.scaled(QSize(16, 16), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        painter.drawPixmap(QRect(0, 0, 16, 16), pixmap)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Tri photo")
        self.setWindowIcon(QIcon(str(ICON_PATH)))

        self.setMenuBar(WindowMenu(self))

        main_windows_wdg = QWidget()
        main_windows_lyt = QHBoxLayout()
        splitter = QSplitter()
        splitter.setHandleWidth(3)

        self.tab1 = MainTab(self)
        self.tab2 = ListExtsTab()
        self.tab3 = ListMetaTab()
        self.tab4 = ListAppsTab()
        self.tab5 = DateTab()
        self.tab6 = GPSTab()

        toolBox = QToolBox()
        toolBox.setStyleSheet("QToolBox::tab { padding: 5px; }")

        toolBox.addItem(self.tab2, _("Extensions"))
        toolBox.addItem(self.tab3, _("Metadatas"))
        toolBox.addItem(self.tab4, _("Appareil"))
        toolBox.addItem(self.tab5, _("Date"))
        toolBox.addItem(self.tab6, _("GPS"))

        self.tab2.listextWdg.itemChanged.connect(self.update_extensions)
        self.tab4.listappWdg.itemChanged.connect(self.update_cameras)
        self.tab1.populateBtn.clicked.connect(self.update_selection_tabs)

        previewBtn = QPushButton("\n".join(list(_("> Afficher un aperçu >"))))
        previewBtn.setFixedWidth(15)

        self.preview_wdg = DatabaseViewer(str(IMAGE_DATABASE_PATH))
        self.preview_wdg.filter_edit.textChanged.connect(self.update_preview)
        self.preview_wdg.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.preview_wdg.setHidden(True)
        self.preview_wdg.setHiddenCallback(lambda : previewBtn.setHidden(False))
        previewBtn.clicked.connect(lambda : self.preview_wdg.setHidden(False))
        previewBtn.clicked.connect(lambda : previewBtn.setHidden(True))

        tabs = QTabWidget()
        tabs.setMinimumWidth(300)
        tabs.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        tabs.setMaximumWidth(600)
        tabs.setTabPosition(QTabWidget.West)

        if CFG['gui_mode'] == GUI_SIMPLIFIED or CFG['gui_mode'] == GUI_NORMAL :

            splitter.addWidget(self.tab1)
            tabs.setHidden(True)

        elif CFG['gui_mode'] == GUI_ADVANCED :

            tabs.addTab(self.tab1, "Main")

        tabs.addTab(toolBox, _("Outils"))
        splitter.addWidget(tabs)

        splitter.addWidget(previewBtn)
        splitter.addWidget(self.preview_wdg)

        main_windows_lyt.addWidget(splitter)
        #self.tab1.previewBtn.clicked.connect(self.update_preview)

        main_windows_wdg.setLayout(main_windows_lyt)
        self.setCentralWidget(main_windows_wdg)

        size = self.sizeHint()
        self.setMinimumHeight(size.height())

    def update_cameras(self):
        txt = self.tab4.user_choice_cameras
        self.tab1.textWdg["cameras"].setText(txt)

    def update_extensions(self):
        txt = self.tab2.user_choice_extentions
        self.tab1.textWdg["extentions"].setText(txt)

    def update_preview(self):

        timer = QTimer()

        if not timer.isActive():

            filter_text = self.preview_wdg.filter_edit.text()
            tup = (CFG['in_dir'], CFG['extentions'], CFG['cameras'], CFG['is_recursive'], 0, CFG['control_hash'], filter_text)
            self.preview_wdg.update_table(*tup)

    def update_selection_tabs(self):

        self.tab2.get_ext_list()
        self.tab3.get_tag_list()
        self.tab4.get_app_list()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Escape:
            self.quit()
        elif e.key() == Qt.Key_Q:
            self.quit()

    def quit(self):
        self.tab1.save_act()
        QApplication.quit()

    def closeEvent(self, event):
        self.tab1.save_act()
        super().closeEvent(event)

class LabelNLineEdit(QHBoxLayout):
    def __init__(self, parent, label, tooltip, placeholder='', fileselector=False, combobox_options='', checkbox=False, spinbox=False):
        super().__init__()

        self.parent = parent
        self.widget_list = []

        if checkbox:
            self.add_checkbox()

        labelWdg = QLabel(label)
        self.addWidget(labelWdg)
        self.widget_list += [labelWdg]

        if not combobox_options:
            self.textBox = self.add_lineedit(tooltip, placeholder)
        else:
            self.textBox = self.add_combobox(tooltip, placeholder, combobox_options)
            self.widget_list += [self.combo]
        self.widget_list += [self.textBox]

        self.textBox.textChanged.connect(self.parent.get_config)

        if spinbox:
            roll_box = self.add_spinbox(spinbox)
            self.widget_list += [roll_box]

        if fileselector:
            btn_selector = self.add_fileselector_btn()
            self.widget_list += [btn_selector]

        if checkbox:
            self.toggle_widgets(self.checkBox.checkState())

    def toggle_widgets(self, e):
        for wdg in self.widget_list:
            wdg.setEnabled(bool(e))

    def add_checkbox(self):

        self.checkBox = QCheckBox()
        self.addWidget(self.checkBox)
        self.checkBox.setCheckState(CFG['is_guess_date_from_name'])
        self.checkBox.toggled.connect(self.toggle_widgets)

    def add_spinbox(self, spin_label=False):

        self.spinBox = QSpinBox()
        self.spinBox.setRange(0,100)
        if spin_label:
            self.addWidget(QLabel(spin_label))
        self.addWidget(self.spinBox)
        #self.checkBox = spin
        def callback(val):
            CFG['group_floating_days_nb'] = str(val)
        self.spinBox.valueChanged.connect(callback)

        return self.spinBox

    def add_lineedit(self, tooltip, placeholder):

        textBox = QLineEdit()
        textBox.setToolTip(tooltip)
        textBox.setPlaceholderText(placeholder)
        self.addWidget(textBox)

        return textBox

    def add_fileselector_btn(self):

        btn = QPushButton()
        pixmapi = QStyle.StandardPixmap.SP_DirOpenIcon
        icon = self.parent.style().standardIcon(pixmapi)
        btn.setIcon(icon)
        btn.clicked.connect(self.select_directory)

        self.addWidget(btn)
        return btn

    def add_combobox(self, tooltip, placeholder, options):

        combo = QComboBox()
        self.addWidget(combo)
        self.combo = combo

        if CFG['gui_mode'] == GUI_SIMPLIFIED:
            combo.addItems(options)
            combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            #combo.view().setMinimumWidth(self.combo_box.width())
            self.textBox = QLineEdit()
            self.textBox.setHidden(True)

        else:
            combo.setEditable(True)
            combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            combo.setToolTip(tooltip)
            combo.lineEdit().setPlaceholderText(placeholder)
            model = combo.model()
            for option in options:
                model.appendRow(QStandardItem(option))
            self.textBox = combo.lineEdit()

        def callback():
            text = combo.currentText()
            for k,v in MEDIA_FORMATS.items():
                text = re.sub(k, v, text)
            for k,v in REL_PATH_FORMATS.items():
                text = re.sub(k, v, text)
            self.textBox.setText(text)
            self.combo.clearFocus() # prevent combo to capture all signals

        #callback = lambda e:self.textBox.setText(combo.currentText())
        combo.currentIndexChanged.connect(callback)

        # Set default values (need to load values from textBox intead of config at MainTab.__init__)
        if CFG['gui_mode'] == GUI_SIMPLIFIED:
            combo.setCurrentIndex(0)
            combo.currentIndexChanged.emit(0)

        return self.textBox


            #return combo.lineEdit()

    def select_directory(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        directory = QFileDialog.getExistingDirectory(
            self.parent.parent, _("Selectionner le dossier"), options=options
        )

        if directory:
            self.textBox.setText(directory)
            logging.info(f"{self.parentWidget().children()[0].text()} directory changed to {directory}")

class MainTab(QWidget):
    def __init__(self, parent):
        super().__init__()

        self.parent = parent
        self.textWdg = {}

        main_layout = QVBoxLayout()

        ########## Source ##########
        frame = MyFrame(_("Source"), "blue")
        layout = QVBoxLayout()

        srcWdg = LabelNLineEdit(self, **MAIN_TAB_WIDGETS['in_dir'])
        extWdg = LabelNLineEdit(self, **MAIN_TAB_WIDGETS['extentions'])

        self.textWdg["in_dir"] = srcWdg.textBox
        self.textWdg["extentions"] = extWdg.textBox

        layout.addLayout(srcWdg)
        layout.addLayout(extWdg)

        if not CFG['gui_mode'] == GUI_SIMPLIFIED:
            camWdg = LabelNLineEdit(self, **MAIN_TAB_WIDGETS['cameras'])
            self.textWdg["cameras"] = camWdg.textBox
            layout.addLayout(camWdg)

        frame.setLayout(layout)
        main_layout.addWidget(frame)

        ########## Destination ##########
        frame = MyFrame(_("Destination"), "blue")
        layout = QVBoxLayout()

        destWdg = LabelNLineEdit(self, **MAIN_TAB_WIDGETS['out_dir'])
        rel_destWdg = LabelNLineEdit(self, **MAIN_TAB_WIDGETS['out_path_str'])
        name_destWdg = LabelNLineEdit(self, **MAIN_TAB_WIDGETS['filename'])

        self.textWdg["out_dir"] = destWdg.textBox
        self.textWdg["out_path_str"] = rel_destWdg.textBox
        self.textWdg["filename"] = name_destWdg.textBox

        layout.addLayout(destWdg)
        layout.addLayout(rel_destWdg)
        layout.addLayout(name_destWdg)

        frame.setLayout(layout)
        main_layout.addWidget(frame)

        ########## Options ##########
        frame = MyFrame(_("Options"), "blue")

        layout = QVBoxLayout()
        sub_layout = QHBoxLayout()

        self.boxWdg = {}
        self.spinWdg = {}

        guess_date_from_name_Wdg = LabelNLineEdit(self, **MAIN_TAB_WIDGETS['guess_date_from_name'])
        self.textWdg['guess_date_from_name'] = guess_date_from_name_Wdg.textBox
        self.boxWdg['is_guess_date_from_name'] = guess_date_from_name_Wdg.checkBox
        layout.addLayout(guess_date_from_name_Wdg)

        group_by_floating_days_Wdg = LabelNLineEdit(self, **MAIN_TAB_WIDGETS['group_by_floating_days'])
        self.textWdg['group_floating_days_fmt'] = group_by_floating_days_Wdg.textBox
        self.boxWdg['is_group_floating_days'] = group_by_floating_days_Wdg.checkBox
        self.spinWdg['group_floating_days_nb'] = group_by_floating_days_Wdg.spinBox
        layout.addLayout(group_by_floating_days_Wdg)

        for prop, label, tooltip in MAIN_TAB_BUTTONS:
            if prop == "NEW_LINE":
                layout.addLayout(sub_layout)
                sub_layout = QHBoxLayout()
            elif isinstance(prop, str):
                ckb = QCheckBox()
                ckb.setText(label)
                ckb.setToolTip(tooltip)
                sub_layout.addWidget(ckb)
                self.boxWdg[prop] = ckb

                # callback
        for prop, ckb in self.boxWdg.items():
            ckb.setCheckState(CFG[prop])
            ckb.stateChanged.connect(self.get_config)

        self.boxWdg["control_hash"].clicked.connect(self.toogle_hash)

        layout.addLayout(sub_layout)
        frame.setLayout(layout)
        main_layout.addWidget(frame)
        if CFG['gui_mode'] == GUI_SIMPLIFIED:
            frame.setHidden(True)

        ########## Save & Run ##########
        frame = MyFrame("", "red")

        layout = QVBoxLayout()

        sub_layout = QHBoxLayout()

        ckb_grp = QButtonGroup(self)
        ckb_grp.buttonClicked[int].connect(self.set_file_action)
        file_action_Btns = {}
        file_action_Btns[FILE_SIMULATE] = QRadioButton(_('Simuler'), self)
        file_action_Btns[FILE_COPY] = QRadioButton(_('Copier'), self)
        file_action_Btns[FILE_MOVE] = QRadioButton(_('Déplacer'), self)

        ckb_grp.addButton(file_action_Btns[FILE_SIMULATE], FILE_SIMULATE)
        ckb_grp.addButton(file_action_Btns[FILE_COPY], FILE_COPY)
        ckb_grp.addButton(file_action_Btns[FILE_MOVE], FILE_MOVE)

        file_action_Btns[CFG['file_action']].setChecked(True)

        sub_layout.addWidget(file_action_Btns[FILE_SIMULATE])
        sub_layout.addWidget(file_action_Btns[FILE_COPY])
        sub_layout.addWidget(file_action_Btns[FILE_MOVE])
        layout.addLayout(sub_layout)

        # Buttons
        btn_layout = QHBoxLayout()

        #btn = QPushButton(_("Sauvegarder la configuration"))
        #btn_layout.addWidget(btn)
        #btn.clicked.connect(self.save_act)

        #self.previewBtn = QPushButton(_("update preview"))
        #btn_layout.addWidget(self.previewBtn)

        self.populateBtn = QPushButton(_("1. Scanner"))
        self.populateBtn.setToolTip(_("Scanne les repertoires <b>source</b> et <b>destination</b><br>et met à jour l'onglet <b>outils</b>"))
        btn_layout.addWidget(self.populateBtn)
        self.populateBtn.clicked.connect(self.populate_act)

        self.stopBtn0 = QPushButton(_("Interrompre"))
        btn_layout.addWidget(self.stopBtn0)
        self.stopBtn0.clicked.connect(self.stop)
        self.stopBtn0.setHidden(True)

        self.previewBtn = QPushButton(_("2. Pré-calculer"))
        self.previewBtn.setToolTip(_("A partir des fichiers trouvés pendant le scan, \nGenere les nouveaux chemins pour les images et affiche un aperçu"))
        btn_layout.addWidget(self.previewBtn)
        self.previewBtn.clicked.connect(self.preview_act)

        self.stopBtn1 = QPushButton(_("Interrompre"))
        btn_layout.addWidget(self.stopBtn1)
        self.stopBtn1.clicked.connect(self.stop)
        self.stopBtn1.setHidden(True)

        self.executeBtn = QPushButton(_("3. Executer"))
        self.executeBtn.setToolTip(_("A partir des chemins pré-calculés, déplace les fichiers,\ninscrit les nouvelles métadonnées si besoin"))
        btn_layout.addWidget(self.executeBtn)
        self.executeBtn.clicked.connect(self.run_act)

        self.stopBtn2 = QPushButton(_("Interrompre"))
        btn_layout.addWidget(self.stopBtn2)
        self.stopBtn2.clicked.connect(self.stop)
        self.stopBtn2.setHidden(True)

        # Progress bar
        self.progress_bar = MyProgressBar()
        progress_bar_label = self.progress_bar.add_label()

        # Counters
        self.couterWdg = CounterWdg()

        layout.addLayout(btn_layout)
        layout.addWidget(progress_bar_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.couterWdg)
        layout.setContentsMargins(0, 0, 0, 0)
        frame.setLayout(layout)

        size = frame.sizeHint()
        frame.setMinimumHeight(size.height())

        main_layout.addWidget(frame)

        size = self.sizeHint()
        self.setMinimumHeight(size.height())

        self.setLayout(main_layout)

        ########## Get config & init interface ##########
        if CFG['gui_mode'] == GUI_SIMPLIFIED: # use default values
            self.get_config()
        else:
            self.set_config()
        self.toogle_hash(self.boxWdg["control_hash"].checkState())

    def set_file_action(self, id):
        CFG['file_action'] = id

    def toogle_hash(self, is_checked):
        self.boxWdg["hash_populate"].setDisabled(not is_checked)
        self.boxWdg["hash_reset"].setDisabled(not is_checked)

    def populate_act(self):
        logging.info("Starting processing files...")

        self.save_act()
        self.populateBtn.setHidden(True)
        self.stopBtn0.setHidden(False)

        InterupHolder.stop_signal = False
        self.timer = QTimer()

        import itertools

        def waiting_animation():
            animation = itertools.cycle(['|', '/', '-', '\\'])
            while True:
                yield 'Interrompre ' + next(animation)
        loop_text = waiting_animation()

        self.timer.timeout.connect(lambda : self.run_function(
            ordonate_photos.populate_db, InterupHolder, self.couterWdg, lambda : self.stopBtn0.setText(loop_text.__next__())
        ))
        self.timer.timeout.connect(self.parent.update_preview)
        self.timer.start(1000)  # waits for 1 second

        #ordonate_photos.populate_db()

    def preview_act(self):
        logging.info("Starting processing files...")

        self.save_act()
        self.previewBtn.setHidden(True)
        self.stopBtn1.setHidden(False)

        InterupHolder.stop_signal = False
        self.timer = QTimer()
        self.timer.timeout.connect(lambda : self.run_function(
            ordonate_photos.compute, self.progress_bar, self.couterWdg, InterupHolder
        ))
        self.timer.timeout.connect(self.parent.update_preview)
        self.timer.start(1000)  # waits for 1 second

    def run_act(self):
        logging.info("Starting processing files...")

        self.save_act()
        self.executeBtn.setHidden(True)
        self.stopBtn2.setHidden(False)

        InterupHolder.stop_signal = False
        self.timer = QTimer()
        self.timer.timeout.connect(lambda : self.run_function(
            ordonate_photos.execute, self.progress_bar, self.couterWdg, InterupHolder
        ))
        self.timer.start(1000)  # waits for 1 second

        #self.start(ordonate_photos.main, self.progress_bar, self.couterWdg, InterupHolder)

    def run_function(self, func, *args, **kwargs):
        if not InterupHolder.stop_signal:
            func(*args, **kwargs)
        if InterupHolder.stop_signal:
            self.timer.stop()
            self.populateBtn.setHidden(False)
            self.executeBtn.setHidden(False)
            self.previewBtn.setHidden(False)
            self.stopBtn0.setHidden(True)
            self.stopBtn1.setHidden(True)
            self.stopBtn2.setHidden(True)
            self.progress_bar.setValue(100)

    def stop(self):
        self.timer.stop()
        InterupHolder.stop_signal = True
        self.populateBtn.setHidden(False)
        self.executeBtn.setHidden(False)
        self.previewBtn.setHidden(False)
        self.stopBtn0.setHidden(True)
        self.stopBtn1.setHidden(True)
        self.stopBtn2.setHidden(True)
        self.progress_bar.setValue(100)

    def save_act(self):
        print("SAVING")
        logging.info(f"Saving config to {CFG.configfile} ...")
        self.get_config()
        CFG.save_config()

    def set_config(self):
        logging.info("load config")
        for cfg_name, wdg in self.textWdg.items():
            wdg.setText(str(CFG.get_repr(cfg_name)))

        for cfg_name, wdg in self.spinWdg.items():
            wdg.setValue(int(CFG.get_repr(cfg_name)))

        for cfg_name, wdg in self.boxWdg.items():
            wdg.setCheckState(2 * int(CFG[cfg_name]))

    def get_config(self):
        for cfg_name, wdg in self.textWdg.items():
            CFG[cfg_name] = wdg.text()

        for cfg_name, wdg in self.spinWdg.items():
            CFG[cfg_name] = wdg.value()

        for cfg_name, wdg in self.boxWdg.items():
            CFG[cfg_name] = 2 * int(wdg.isChecked())

class GPSTab(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout()
        frame = MyFrame(_("tags GPS"), "blue")

        list_layout = QVBoxLayout()
        list_widget = CopyableListWidget()
        self.listWdg = list_widget
        list_layout.addWidget(list_widget)

        self.populate_list()
        list_widget.setMaximumHeight(170)
        frame.setMaximumHeight(200)

        frame.setLayout(list_layout)
        main_layout.addWidget(frame)

        frame = MyFrame("", "red")
        layout = QVBoxLayout()

        label = QLabel(GPS_HELP_TEXT)
        layout.addWidget(label)
        res_layout = QHBoxLayout()
        self.label_gps_info = QLabel()
        self.label_image = QLabel()
        res_layout.addWidget(self.label_image)
        res_layout.addWidget(self.label_gps_info)
        layout.addLayout(res_layout)

        btn_layout = QHBoxLayout()
        btn = QPushButton(_("Executer"))
        btn_layout.addWidget(btn)
        self.progress_bar = MyProgressBar()
        btn_layout.addWidget(self.progress_bar)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn.clicked.connect(self.run_act)

        layout.addLayout(btn_layout)
        frame.setLayout(layout)
        main_layout.addWidget(frame)
        self.setLayout(main_layout)

    def run_act(self):
        logging.info("Starting processing files...")

        ordonate_photos.add_tags_to_folder(
            self.progress_bar,
            self.label_gps_info,
            self.label_image
        )
        self.progress_bar.setValue(100)

    def populate_list(self):
        tags = EXIF_LOCATION_FIELD.values()

        for tag in tags:
            item = ItemWidget(tag)
            self.listWdg.addItem(item)
        self.listWdg.repaint()

class DateTab(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)

        frame = QFrame(self, frameShape=QFrame.StyledPanel)
        label_frame = QLabel(_("Codes de formatage des dates"), frame)
        frame.setObjectName("myFrame")
        label_frame.setObjectName("myLabel")
        frame.setStyleSheet("#myFrame { padding: 15px; border: 2px solid blue}")
        label_frame.setStyleSheet("padding: 10px; color:blue")
        list_layout = QVBoxLayout()
        #list_widget = QListWidget()

        strftime_help = open(STRFTIME_HELP_PATH).read()
        text_widget = QTextEdit()
        #text_widget.setTextFormat(Qt.MarkdownText)
        text_widget.setHtml(strftime_help)
        #self.listWdg = list_widget
        list_layout.addWidget(text_widget)
        #self.get_tag_list()
        frame.setLayout(list_layout)
        main_layout.addWidget(frame)

        self.setLayout(main_layout)

    def link_clicked(self, url):
        QDesktopServices.openUrl(url)

#    def get_tag_list(self):
#
#        for tag in DATE_STRFTIME_FORMAT:
#            item = QListWidgetItem(tag)
#            self.listWdg.addItem(item)


class CopyableListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

    def show_context_menu(self, pos):
        item = self.itemAt(pos)
        if item:
            menu = QMenu(self)
            copy_action = QAction(_("Copier la propriété"), self)
            copy_action.triggered.connect(lambda: self.copy_to_clipboard(item))
            menu.addAction(copy_action)
            menu.exec_(self.mapToGlobal(pos))

    def keyPressEvent(self, event):
        if event.matches(QKeySequence.Copy):
            select_item = self.selectedItems()[0]
            self.copy_to_clipboard(select_item)
        else:
            super().keyPressEvent(event)

    def copy_to_clipboard(self, item):
        text = '<' + item.text().split('\t')[0].strip() + '>'
        QApplication.clipboard().setText(text)

class ComboBox(QComboBox):

    def __init__(self, callback):
        super().__init__()

        def combo_changed():
            callback(self.currentText())

        model = self.model()

        # Add items to the QComboBox and set the foreground color
        options = (_('toutes'), _('en commun'), _('utiles'))
        for option in options:
            entry = QStandardItem(option)
            model.appendRow(entry)

        self.setCurrentIndex(2)

        # Connect QComboBox signal to combo_changed() slot
        self.currentIndexChanged.connect(combo_changed)

class MyFrame(QFrame):
    def __init__(self, label, color, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setFrameShape(QFrame.StyledPanel)
        label_frame = QLabel(label, self)
        self.setObjectName(f"myFrame_{color}")
        label_frame.setObjectName(f"myLabel_{color}")
        self.setStyleSheet(
            f"#myFrame_{color}" + " { padding: 15px; border: 2px solid " + color + "}"
        )
        label_frame.setStyleSheet(f"padding: 10px; color:{color}")
        self.adjustSize()
        self.setContentsMargins(6, 14, 6, 1)

def OptionBool(QHBoxLayout):
    def __init__(self, label, tooltip):
        super().__init__()

        self.addWidget(QLabel(f"{label}:"))

        self.checkbox = QCheckBox()
        self.checkbox.setToolTip(tooltip)
        self.addWidget(self.checkbox)

class ItemWidget(QListWidgetItem):
    def __init__(self, text, parent=None):
        super().__init__(parent)
        self.setText(text)
        # self.setSizeHint(QtCore.QSize(100, 48))

class ListExtsTab(MyFrame):
    def __init__(self):

        super().__init__(_("Extensions"), 'blue')
        #self.setTabPosition(QTabWidget.West)
        #main_layout = QVBoxLayout(self)
        #tab = QTabWidget()

        ###### Extentions ########
        # add the list with toggable buttons to list extentions
        #frame = MyFrame(_("Extensions"), 'blue')
        list_layout = QVBoxLayout()
        list_widget = QListWidget()
        self.listextWdg = list_widget
        self.listextWdg.setViewMode(QListView.IconMode)
        self.listextWdg.setSpacing(10)
        self.listextWdg.setResizeMode(QListWidget.Adjust)
        self.listextWdg.itemChanged.connect(self.validate_ext)

        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.listextWdg.setSizePolicy(size_policy)

        #list_btn = QPushButton(_("Charger depuis les Fichiers"))
        #list_btn.clicked.connect(self.get_ext_list)

        #list_layout.addWidget(list_btn)
        list_layout.addWidget(list_widget)

        self.setLayout(list_layout)
        #self.addTab(frame, 'Extensions')
        #main_layout.addWidget(frame)

    def validate_ext(self):
        self.user_choice_extentions = []
        for i in range(self.listextWdg.count()):
            item = self.listextWdg.item(i)
            #item.setSizeHint(QtCore.QSize(100, 48))
            if item.checkState():
                self.user_choice_extentions.append(item.text().strip("."))

        self.user_choice_extentions = ",".join(self.user_choice_extentions)
        logging.info(f"User extention selection : {self.user_choice_extentions}")

    def get_ext_list(self):
        self.listextWdg.clear()
        exts = ordonate_photos.list_available_exts(CFG["in_dir"], recursive=CFG["is_recursive"])
        for ext in exts:
            # item = QListWidgetItem(ext)
            item = ItemWidget(ext)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setTextAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
            item.setCheckState(Qt.Unchecked)
            self.listextWdg.addItem(item)
        self.listextWdg.repaint()

class ListAppsTab(MyFrame):
    def __init__(self):
        super().__init__(_("Appareil"), 'blue')
        ######## Appareil ##############
        # add the list with toggable buttons to list extentions
        list_layout = QVBoxLayout()
        list_widget = QListWidget()
        self.listappWdg = list_widget
        self.listappWdg.setViewMode(QListView.IconMode)
        self.listappWdg.setSpacing(10)
        self.listappWdg.setResizeMode(QListWidget.Adjust)
        self.listappWdg.itemChanged.connect(self.validate_cam)

        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.listappWdg.setSizePolicy(size_policy)

        #list_btn = QPushButton(_("Charger depuis les Fichiers"))
        #list_btn.clicked.connect(self.get_app_list)
        #list_layout.addWidget(list_btn)
        list_layout.addWidget(list_widget)
        self.setLayout(list_layout)
        #self.addTab(frame, 'Appareil')
        #main_layout.addWidget(frame)

    def validate_cam(self):
        ## APPAREIL PHOTO ###
        user_choice_cameras = []
        for i in range(self.listappWdg.count()):
            item = self.listappWdg.item(i)
            #item.setSizeHint(QtCore.QSize(100, 48))
            if item.checkState():
                text = item.text().strip()
                user_choice_cameras.append(text)

        self.user_choice_cameras = ",".join(user_choice_cameras)
        logging.info(f"User extention selection : {self.user_choice_cameras}")

    def get_app_list(self):

        self.listappWdg.clear()
        cameras = ordonate_photos.list_available_camera_model(CFG["in_dir"], CFG['extentions'], recursive=CFG['is_recursive'])
        for camera in cameras:
            # item = QListWidgetItem(ext)
            item = ItemWidget(camera)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setTextAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
            item.setCheckState(Qt.Unchecked)
            self.listappWdg.addItem(item)
        self.listappWdg.repaint()


class ListMetaTab(MyFrame):
    def __init__(self):
        super().__init__(_("Métadonnées"), 'blue')
        ################ Metadatas #######################
        #frame = MyFrame(_("Métadonnées"), 'blue')
        list_layout = QVBoxLayout()
        list_widget = CopyableListWidget()
        self.listmetaWdg = list_widget
        self.listmetaWdg.setAlternatingRowColors(True)

        btn_layout = QHBoxLayout()
        #list_btn = QPushButton(_("Charger depuis les Fichiers"))
        self.choose_box = ComboBox(self.show_tag_list)
        #btn_layout.addWidget(list_btn)
        btn_layout.addWidget(self.choose_box)
        list_layout.addLayout(btn_layout)

        list_layout.addWidget(list_widget)
        #list_btn.clicked.connect(self.get_tag_list)
        self.setLayout(list_layout)
        #self.addTab(frame, 'Métadonnées')
        #main_layout.addWidget(frame)

        #self.validate_btn = QPushButton("Valider")
        #self.validate_btn.clicked.connect(self.validate_act)
        #main_layout.addWidget(self.validate_btn)

        #self.setLayout(main_layout)

    def get_tag_list(self):

        self.exifs_lists = ordonate_photos.list_available_tags(
            CFG["in_dir"], CFG["extentions"], recursive=CFG['is_recursive']
        )

        option = self.choose_box.currentText()
        self.show_tag_list(option)

    def show_tag_list(self, option=_("utiles")):

        self.listmetaWdg.clear()

        exifs_all, exifs_common = self.exifs_lists
        if option == _("toutes"):
            exifs = exifs_all
        elif option == _("en commun"):
            exifs = exifs_common
        elif option == _("utiles"):
            exifs = [x for x in exifs_all if x in USEFULL_TAG_DESCRIPTION]

        for tag in sorted(exifs):
            text = f"{tag:38} \t{TAG_DESCRIPTION.get(tag,'')}"
            item = QListWidgetItem(text)
            self.listmetaWdg.addItem(item)

class ListMetaDataTab_old(QWidget):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)

        frame = QFrame(self, frameShape=QFrame.StyledPanel)
        label_frame = QLabel(_("Métadonnées"), frame)
        frame.setObjectName("myFrame")
        label_frame.setObjectName("myLabel")
        frame.setStyleSheet("#myFrame { padding: 15px; border: 2px solid blue}")
        label_frame.setStyleSheet("padding: 10px; color:blue")
        list_layout = QVBoxLayout()
        list_widget = CopyableListWidget()
        self.listWdg = list_widget
        self.listWdg.setAlternatingRowColors(True)

        btn_layout = QHBoxLayout()
        list_btn = QPushButton(_("Charger depuis les Fichiers"))
        self.choose_box = ComboBox(self.show_tag_list)
        btn_layout.addWidget(list_btn)
        btn_layout.addWidget(self.choose_box)
        list_layout.addLayout(btn_layout)

        list_layout.addWidget(list_widget)
        list_btn.clicked.connect(self.get_tag_list)
        frame.setLayout(list_layout)
        main_layout.addWidget(frame)

        self.setLayout(main_layout)

    def get_tag_list(self):

        self.exifs_lists = ordonate_photos.list_available_tags(
            CFG["in_dir"], CFG["extentions"], recursive=CFG['is_recursive']
        )

        option = self.choose_box.currentText()
        self.show_tag_list(option)

    def show_tag_list(self, option=_("utiles")):

        self.listWdg.clear()

        exifs_all, exifs_common = self.exifs_lists
        if option == _("toutes"):
            exifs = exifs_all
        elif option == _("en commun"):
            exifs = exifs_common
        elif option == _("utiles"):
            exifs = [x for x in exifs_all if x in USEFULL_TAG_DESCRIPTION]

        for tag in sorted(exifs):
            text = f"{tag:38} \t{TAG_DESCRIPTION.get(tag,'')}"
            item = QListWidgetItem(text)
            self.listWdg.addItem(item)

class MyProgressBar(QProgressBar):
    def __init__(self):
        super().__init__()
        self.setGeometry(50, 50, 200, 20)
        self.setContentsMargins(0, 0, 0, 0)

    def add_label(self):
        self.text_label = QLabel("")
        return self.text_label

    def init(self, n):
        self._progbar_nb_val = n

    def update(self, v, text='', text2=''):
        self.setValue(int(100 * v / self._progbar_nb_val))
        QApplication.processEvents()  # keep the GUI responsive
        self.text_label.setText(text)

class CounterWdg(QWidget):
    def __init__(self):
        super().__init__()

        sublayout = QHBoxLayout()

        label = QLabel(_("Nombre de fichiers :"))
        text = QLabel("")
        sublayout.addWidget(label)
        sublayout.addWidget(text)
        self.nb_files = text

        label = QLabel(_("Dupliqués :"))
        text = QLabel("")
        sublayout.addWidget(label)
        sublayout.addWidget(text)
        self.duplicates = text

        self.setLayout(sublayout)

        size = self.sizeHint()
        self.setMinimumHeight(size.height())

    def update(self, counter):
        self.nb_files.setText(str(counter.nb_files))
        self.duplicates.setText(str(counter.duplicates))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
