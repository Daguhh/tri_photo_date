#!/usr/bin/env python1

from configparser import ConfigParser
import sys, os
from pathlib import Path
import logging
import re

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QThread, QTimer, QEventLoop, QSize
from PyQt5.QtGui import QKeySequence, QIcon, QPixmap, QClipboard, QStandardItem, QPixmap, QPainter, QFontMetrics
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QListWidgetItem, QAbstractItemView, QCheckBox, QFrame, QProgressBar,
    QFileDialog, QStyle, QTabWidget, QAction, QListView, QSizePolicy, QMainWindow,
    QMenu, QAction, QComboBox, QTextEdit, QButtonGroup, QRadioButton, QSplitter,
    QToolBox, QSpinBox, QScrollArea,
)

# Modules
from tri_photo_date.gui.sqlite_view import DatabaseViewer
from tri_photo_date import ordonate_photos
from tri_photo_date.ordonate_photos import CFG
from tri_photo_date.gui.menu import WindowMenu
from tri_photo_date.explore_db import list_available_camera_model, list_available_exts, list_available_tags

# Local PyQt widgets
from tri_photo_date.gui.collapsible_frame import CollapsibleFrame, PreviewCollapsibleFrame
from tri_photo_date.gui.small_widgets import simpleCheckBox, simplePushButton, simpleStopButton, MyRadioButton

# Constants
from tri_photo_date.exif import TAG_DESCRIPTION, USEFULL_TAG_DESCRIPTION, EXIF_LOCATION_FIELD
from tri_photo_date.utils.config_loader import FILE_SIMULATE, FILE_COPY, FILE_MOVE, GUI_SIMPLIFIED, GUI_NORMAL, GUI_ADVANCED, DUP_MD5_FILE, DUP_MD5_DATA, DUP_DATETIME
from tri_photo_date.gui.strftime_help import DATE_STRFTIME_FORMAT
from tri_photo_date.gui.human_text import GPS_HELP_TEXT, MEDIA_FORMATS, REL_PATH_FORMATS, ACTION_BUTTONS, DUP_RADIO_BUTTONS
from tri_photo_date.gui.human_text import MAIN_TAB_WIDGETS as MTW
from tri_photo_date.gui.human_text import MAIN_TAB_BUTTONS as MTB
from tri_photo_date.utils.config_paths import STRFTIME_HELP_PATH, ICON_PATH, LOCALES_DIR, IMAGE_DATABASE_PATH


lang = CFG['interface.gui_lang']
import gettext
trad = gettext.translation('base', localedir=LOCALES_DIR, languages=[lang])
trad.install()
_ = trad.gettext # Greek

os.environ['QT_SCALE_FACTOR'] = CFG['interface.gui_size']

from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QRect
from PyQt5.QtGui import QPixmap, QPainter
from PyQt5.QtWidgets import QSplitterHandle, QPushButton

class LoopCallBack:
    stopped = False

    def __init__(self):
        pass

    @classmethod
    def run(cls):

        loop = QEventLoop()
        QTimer.singleShot(0, loop.quit)
        loop.exec_()
        if cls.stopped:
            return True
        return False

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
        self.tab4 = ListCameraTab()
        self.tab5 = DateTab()
        self.tab6 = GPSTab()

        toolBox = QWidget()
        toolboxLyt = QVBoxLayout()

        toolboxLyt.addWidget(self.tab2)
        toolboxLyt.addWidget(self.tab3)
        toolboxLyt.addWidget(self.tab4)
        toolboxLyt.addWidget(self.tab5)
        toolboxLyt.addWidget(self.tab6)
        toolboxLyt.addStretch()

        toolBox.setLayout(toolboxLyt)

        toolscroll_area = QScrollArea()
        toolscroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        toolscroll_area.setWidgetResizable(True)
        tab1_content = QWidget()
        tab1_content.setLayout(QVBoxLayout())
        tab1_content.layout().addWidget(toolBox)
        toolscroll_area.setWidget(tab1_content)

        self.tab2.listextWdg.itemChanged.connect(self.update_extensions)
        self.tab4.listappWdg.itemChanged.connect(self.update_cameras)
        self.tab1.scanWdg.runBtn.clicked.connect(self.update_selection_tabs)

        preview_frame = PreviewCollapsibleFrame(" Afficher un aperçu", 'green')
        self.preview_wdg = DatabaseViewer(str(IMAGE_DATABASE_PATH))
        self.preview_wdg.filter_edit.textChanged.connect(self.update_preview)
        preview_frame.setWidget(self.preview_wdg)

        tabs = QTabWidget()
        tabs.setMinimumWidth(450)
        tabs.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        tabs.setMaximumWidth(700)
        tabs.setTabPosition(QTabWidget.West)

        scroll_area = QScrollArea()
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setWidgetResizable(True)
        tab1_content = QWidget()
        tab1_content.setLayout(QVBoxLayout())
        tab1_content.layout().addWidget(self.tab1)
        scroll_area.setWidget(tab1_content)

        if CFG['interface.gui_mode'] == GUI_SIMPLIFIED or CFG['interface.gui_mode'] == GUI_NORMAL :

            splitter.addWidget(self.tab1)
            tabs.setHidden(True)

        elif CFG['interface.gui_mode'] == GUI_ADVANCED :

            tabs.addTab(scroll_area, "Main")

        tabs.addTab(toolscroll_area, _("Outils"))
        splitter.addWidget(tabs)

        splitter.addWidget(preview_frame)

        main_windows_lyt.addWidget(splitter)

        main_windows_wdg.setLayout(main_windows_lyt)
        self.setCentralWidget(main_windows_wdg)

        size = self.sizeHint()
        self.resize(400,500)
        preview_frame.collapse(True)

    def update_cameras(self):

        txt = self.tab4.user_choice_cameras
        self.tab1.srcFrame.camWdg.textBox.setText(txt)

    def update_extensions(self):

        txt = self.tab2.user_choice_extentions
        self.tab1.srcFrame.extWdg.textBox.setText(txt)

    def update_preview(self):

        timer = QTimer()

        if not timer.isActive():

            filter_text = self.preview_wdg.filter_edit.text()
            self.preview_wdg.update_table(filter_text)
            self.update_selection_tabs()

    def update_selection_tabs(self):

        self.tab2.get_ext_list()
        self.tab3.get_tag_list()
        self.tab4.get_camera_list()

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

class MainTab(QWidget):
    def __init__(self, parent):
        super().__init__()

        self.parent = parent
        self.Wdgs = {}

        main_layout = QVBoxLayout()

        ########## Scan ##########
        scanWdg = CollapsibleFrame(_("Scan"), color="darkGreen")
        layout = QVBoxLayout()

        scanWdg.dirWdg = LabelNLineEdit(self, **MTW['scan_dir'])
        scanWdg.dirWdg.recursiveBtn = simpleCheckBox(scanWdg.dirWdg, **MTB['is_recursive'])

        layout.addLayout(scanWdg.dirWdg)
        sub_layout = QHBoxLayout()
        scanWdg.is_metaBtn = simpleCheckBox(sub_layout, **MTB['scan_is_meta'])
        scanWdg.is_md5_file = simpleCheckBox(sub_layout, **MTB['scan_is_md5_file'])
        scanWdg.is_md5_data = simpleCheckBox(sub_layout, **MTB['scan_is_md5_data'])
        layout.addLayout(sub_layout)

        scanWdg.setLayout(layout)
        scanWdg.collapse(True)
        main_layout.addWidget(scanWdg)

        scanWdg.runBtn  = simplePushButton(main_layout, **ACTION_BUTTONS['populate'])
        scanWdg.runBtn.clicked.connect(self.populate_act)
        scanWdg.stopBtn = simpleStopButton(main_layout, self.stop)

        scanWdg.progbar_layout = QVBoxLayout()
        main_layout.addLayout(scanWdg.progbar_layout)

        # Disable "coming soon"
        scanWdg.dirWdg.textBox.setReadOnly(True)
        scanWdg.dirWdg.btn_selector.setDisabled(True)
        scanWdg.dirWdg.recursiveBtn.setDisabled(True)
        scanWdg.is_metaBtn.setDisabled(True)
        scanWdg.is_md5_file.setDisabled(True)
        scanWdg.is_md5_data.setDisabled(True)

        self.scanWdg = scanWdg

        ########## Source ##########
        srcWdg = CollapsibleFrame(_("Source"))
        layout = QVBoxLayout()

        srcWdg.dirWdg = LabelNLineEdit(self, **MTW['in_dir'])
        srcWdg.dirWdg.textBox.textChanged.connect(lambda x:scanWdg.dirWdg.textBox.setText(x))
        srcWdg.dirWdg.recursiveBtn = simpleCheckBox(srcWdg.dirWdg, **MTB['is_recursive'])
        srcWdg.extWdg = LabelNLineEdit(self, **MTW['extentions'])
        srcWdg.camWdg = LabelNLineEdit(self, **MTW['cameras'])
        srcWdg.excludeWdg = LabelNLineEdit(self, **MTW['excluded_dirs'])
        srcWdg.excludeWdg.is_regex = simpleCheckBox(srcWdg.excludeWdg, **MTB['is_exclude_dir_regex'])

        layout.addLayout(srcWdg.dirWdg)
        layout.addLayout(srcWdg.extWdg)
        layout.addLayout(srcWdg.camWdg)
        layout.addLayout(srcWdg.excludeWdg)
        srcWdg.setLayout(layout)
        main_layout.addWidget(srcWdg)

        self.srcFrame = srcWdg

        ########## Destination ##########
        destWdg = CollapsibleFrame(_("Destination"), color="blue")
        layout = QVBoxLayout()

        destWdg.dirWdg = LabelNLineEdit(self, **MTW['out_dir'])
        destWdg.rel_dirWdg = LabelNLineEdit(self, **MTW['out_path_str'])
        destWdg.filenameWdg = LabelNLineEdit(self, **MTW['filename'])

        layout.addLayout(destWdg.dirWdg)
        layout.addLayout(destWdg.rel_dirWdg)
        layout.addLayout(destWdg.filenameWdg)

        destWdg.setLayout(layout)
        main_layout.addWidget(destWdg)

        self.destFrame = destWdg

        ########## Duplicates ##########
        dupWdg = CollapsibleFrame(_("Dupliqués"), color="blue")
        layout = QVBoxLayout()
        dupWdg.dupBtns = DuplicateWdg(self)
        layout.addLayout(dupWdg.dupBtns)
        dupWdg.setLayout(layout)
        main_layout.addWidget(dupWdg)

        self.dupFrame = dupWdg

        ########## Options ##########
        optWdg = CollapsibleFrame(_("Options"), color="blue")

        layout = QVBoxLayout()
        sub_layout = QHBoxLayout()

        optWdg.guess_date_from_name = LabelNLineEdit(self, **MTW['guess_date_from_name'])
        optWdg.group_by_floating_days = LabelNLineEdit(self, **MTW['group_by_floating_days'])

        layout.addLayout(optWdg.guess_date_from_name)
        layout.addLayout(optWdg.group_by_floating_days)

        sub_layout = QHBoxLayout()
        optWdg.gps = simpleCheckBox(sub_layout, **MTB['gps'])

        optWdg.is_delete_metadatas = simpleCheckBox(sub_layout, **MTB['is_delete_metadatas'])
        optWdg.is_date_from_filesystem = simpleCheckBox(sub_layout, **MTB['is_date_from_filesystem'])

        layout.addLayout(sub_layout)

        optWdg.setLayout(layout)
        optWdg.collapse()
        main_layout.addWidget(optWdg)

        self.optFrame = optWdg

        self.previewBtn = simplePushButton(main_layout,**ACTION_BUTTONS['calculate'])
        self.previewBtn.clicked.connect(self.preview_act)
        self.stopBtn1 = simpleStopButton(main_layout, self.stop)

        if CFG['interface.gui_mode'] == GUI_SIMPLIFIED:
            frame.setHidden(True)

        self.compute_act_prog_holder = QVBoxLayout()
        main_layout.addLayout(self.compute_act_prog_holder)

        ########## Save & Run ##########
        execWdg = CollapsibleFrame("Executer", color="red")
        layout = QVBoxLayout()
        execWdg.file_actionWdg = fileActionWdg(self)
        layout.addLayout(execWdg.file_actionWdg)
        execWdg.setLayout(layout)
        main_layout.addWidget(execWdg)

        self.execFrame = execWdg

        self.executeBtn = simplePushButton(main_layout,**ACTION_BUTTONS['execute'])
        self.executeBtn.clicked.connect(self.run_act)
        self.stopBtn2 = simpleStopButton(main_layout, self.stop)

        self.execute_act_prog_holder = QVBoxLayout()
        main_layout.addLayout(self.execute_act_prog_holder)

        # Progress bar
        self.progress_bar = MyProgressBar()
        self.progress_bar_label = self.progress_bar.add_label()

        # Counters
        #self.couterWdg = CounterWdg()

        fake_layout = QVBoxLayout()
        fake_layout.addWidget(self.progress_bar_label)
        fake_layout.addWidget(self.progress_bar)
        self.prev_progbar_layout = fake_layout

        main_layout.addStretch()

        size = self.sizeHint()
        self.setMinimumHeight(size.height())

        self.setLayout(main_layout)

        # Set up connection to config object
        scanWdg.dirWdg.textBox.textChanged.connect(lambda x : CFG.__setitem__('scan.scan_dir',x))
        scanWdg.is_metaBtn.stateChanged.connect(lambda x : CFG.__setitem__('scan.scan_is_meta',x))
        scanWdg.is_md5_data.stateChanged.connect(lambda x : CFG.__setitem__('scan.scan_is_md5_data',x))
        scanWdg.is_md5_file.stateChanged.connect(lambda x : CFG.__setitem__('scan.scan_is_md5_file',x))
        scanWdg.dirWdg.recursiveBtn.stateChanged.connect(lambda x : CFG.__setitem__('scan.scan_is_recursive',x))

        srcWdg.dirWdg.textBox.textChanged.connect(lambda x : CFG.__setitem__('source.src_dir',x))
        srcWdg.extWdg.textBox.textChanged.connect(lambda x : CFG.__setitem__('source.src_extentions',x))
        srcWdg.camWdg.textBox.textChanged.connect(lambda x : CFG.__setitem__('source.src_cameras',x))
        srcWdg.dirWdg.recursiveBtn.stateChanged.connect(lambda x : CFG.__setitem__('source.src_is_recursive',x))
        srcWdg.excludeWdg.textBox.textChanged.connect(lambda x : CFG.__setitem__('source.src_excluded_dirs',x))
        srcWdg.excludeWdg.labelbox.currentIndexChanged.connect(lambda x : CFG.__setitem__('source.src_exclude_toggle',x))
        srcWdg.excludeWdg.is_regex.stateChanged.connect(lambda x : CFG.__setitem__('source.src_is_exclude_dir_regex',x))

        destWdg.dirWdg.textBox.textChanged.connect(lambda x : CFG.__setitem__('destination.dest_dir',x))
        destWdg.rel_dirWdg.textBox.textChanged.connect(lambda x : CFG.__setitem__('destination.dest_rel_dir',x))
        destWdg.filenameWdg.textBox.textChanged.connect(lambda x : CFG.__setitem__('destination.dest_filename',x))

        dupWdg.dupBtns.duplicateBtn.stateChanged.connect(lambda x : CFG.__setitem__('duplicates.dup_is_control',x))
        dupWdg.dupBtns.dup_grp.buttonClicked[int].connect(lambda x : CFG.__setitem__('duplicates.dup_mode',x))
        dupWdg.dupBtns.scandestBtn.stateChanged.connect(lambda x : CFG.__setitem__('duplicates.dup_is_scan_dest',x))

        optWdg.guess_date_from_name.textBox.textChanged.connect(lambda x : CFG.__setitem__('options.name.name_guess_fmt',x))
        optWdg.guess_date_from_name.checkBox.stateChanged.connect(lambda x : CFG.__setitem__('options.name.name_is_guess',x))
        optWdg.group_by_floating_days.checkBox.stateChanged.connect(lambda x : CFG.__setitem__('options.group.grp_is_group',x))
        optWdg.group_by_floating_days.textBox.textChanged.connect(lambda x : CFG.__setitem__('options.group.grp_display_fmt',x))
        optWdg.group_by_floating_days.spinBox.valueChanged.connect(lambda x : CFG.__setitem__('options.group.grp_floating_nb',x))
        optWdg.gps.stateChanged.connect(lambda x : CFG.__setitem__('options.gps.gps_is_gps',x))
        optWdg.is_delete_metadatas.stateChanged.connect(lambda x : CFG.__setitem__('options.general.opt_is_delete_metadatas',x))
        optWdg.is_date_from_filesystem.stateChanged.connect(lambda x : CFG.__setitem__('options.general.opt_is_date_from_filesystem',x))

        execWdg.file_actionWdg.btn_group.buttonClicked[int].connect(lambda x : CFG.__setitem__('action.action_mode',x))

        # set up setter for each widget
        scanWdgs = {}
        scanWdgs['scan_dir'] = scanWdg.dirWdg.textBox.setText
        scanWdgs['scan_is_recursive'] = scanWdg.dirWdg.recursiveBtn.setCheckState
        scanWdgs['scan_is_md5_file'] = scanWdg.is_md5_file.setCheckState
        scanWdgs['scan_is_md5_data'] = scanWdg.is_md5_data.setCheckState
        scanWdgs['scan_is_meta'] = scanWdg.is_metaBtn.setCheckState
        self.Wdgs['scan'] = scanWdgs

        srcWdgs = {}
        srcWdgs['src_dir'] = srcWdg.dirWdg.textBox.setText
        srcWdgs['src_extentions'] = srcWdg.extWdg.textBox.setText
        srcWdgs['src_cameras'] = srcWdg.camWdg.textBox.setText
        srcWdgs['src_is_recursive'] = srcWdg.dirWdg.recursiveBtn.setCheckState
        srcWdgs['src_excluded_dirs'] = srcWdg.excludeWdg.textBox.setText
        srcWdgs['src_exclude_toggle'] = srcWdg.excludeWdg.labelbox.setCurrentIndex
        srcWdgs['src_is_exclude_dir_regex'] = srcWdg.excludeWdg.is_regex.setCheckState
        self.Wdgs['source'] = srcWdgs

        destWdgs = {}
        destWdgs['dest_dir'] = destWdg.dirWdg.textBox.setText
        destWdgs['dest_rel_dir'] = destWdg.rel_dirWdg.textBox.setText
        destWdgs['dest_filename'] = destWdg.filenameWdg.textBox.setText
        self.Wdgs['destination'] = destWdgs

        dupWdgs = {}
        dupWdgs['dup_is_control'] = dupWdg.dupBtns.duplicateBtn.setCheckState
        dupWdgs['dup_mode'] = lambda x : dupWdg.dupBtns.dup_grp.button(x).setChecked(True)
        dupWdgs['dup_is_scan_dest'] = dupWdg.dupBtns.scandestBtn.setCheckState
        self.Wdgs['duplicates'] = dupWdgs

        optWdgs_name = {}
        optWdgs_name['name_is_guess'] = optWdg.guess_date_from_name.checkBox.setCheckState
        optWdgs_name['name_guess_fmt'] = optWdg.guess_date_from_name.textBox.setText
        self.Wdgs['options.name'] = optWdgs_name

        optWdgs_grp = {}
        optWdgs_grp['grp_is_group'] = optWdg.group_by_floating_days.checkBox.setCheckState
        optWdgs_grp['grp_display_fmt'] = optWdg.group_by_floating_days.textBox.setText
        optWdgs_grp['grp_floating_nb'] = optWdg.group_by_floating_days.spinBox.setValue
        self.Wdgs['options.group'] = optWdgs_grp

        self.Wdgs['options.gps'] = {'gps_is_gps':optWdg.gps.setCheckState}

        optWdgs_gen = {}
        optWdgs_gen['opt_is_delete_metadatas'] = optWdg.is_delete_metadatas.setCheckState
        optWdgs_gen['opt_is_date_from_filesystem'] = optWdg.is_date_from_filesystem.setCheckState
        self.Wdgs['options.general'] = optWdgs_gen

        self.Wdgs['action'] = {'action_mode' : lambda x : execWdg.file_actionWdg.btn_group.button(x).setChecked(True)}#[int]}

        self.load_conf()

    def load_conf(self):

        for section_name, section_dct in self.Wdgs.items():
            for param, wdg_setter in section_dct.items():
                wdg_setter(CFG.get_repr((section_name, param)))

    def move_progbar(self, new_layout):

        self.progress_bar.setParent(new_layout.parentWidget())
        self.progress_bar_label.setParent(new_layout.parentWidget())
        new_layout.addWidget(self.progress_bar_label)
        new_layout.addWidget(self.progress_bar)
        self.prev_progbar_layout.removeWidget(self.progress_bar)
        self.prev_progbar_layout.removeWidget(self.progress_bar_label)
        new_layout.update()
        self.prev_progbar_layout.update()
        self.prev_progbar_layout = new_layout

    def populate_act(self):

        logging.info("Starting processing files...")

        self.move_progbar(self.scanWdg.progbar_layout)

        self.save_act()
        self.scanWdg.runBtn.setHidden(True)
        self.scanWdg.stopBtn.setHidden(False)

        LoopCallBack.stopped = False
        self.timer = QTimer()

        self.timer.timeout.connect(lambda : self.run_function(
            ordonate_photos.populate_db, self.progress_bar, LoopCallBack
        ))
        self.timer.timeout.connect(self.parent.update_preview)
        self.timer.start(1000)  # waits for 1 second

    def preview_act(self):

        logging.info("Starting processing files...")

        self.move_progbar(self.compute_act_prog_holder)

        self.save_act()
        self.previewBtn.setHidden(True)
        self.stopBtn1.setHidden(False)

        LoopCallBack.stopped = False
        self.timer = QTimer()
        self.timer.timeout.connect(lambda : self.run_function(
            ordonate_photos.compute, self.progress_bar, LoopCallBack
        ))
        self.timer.timeout.connect(self.parent.update_preview)
        self.timer.start(1000)  # waits for 1 second

    def run_act(self):

        logging.info("Starting processing files...")

        self.move_progbar(self.execute_act_prog_holder)

        self.save_act()
        self.executeBtn.setHidden(True)
        self.stopBtn2.setHidden(False)

        LoopCallBack.stopped = False
        self.timer = QTimer()
        self.timer.timeout.connect(lambda : self.run_function(
            ordonate_photos.execute, self.progress_bar, LoopCallBack
        ))
        self.timer.start(1000)  # waits for 1 second

    def run_function(self, func, *args, **kwargs):

        if not LoopCallBack.stopped:
            func(*args, **kwargs)
        if LoopCallBack.stopped:
            self.timer.stop()
            self.scanWdg.runBtn.setHidden(False)
            self.executeBtn.setHidden(False)
            self.previewBtn.setHidden(False)
            self.scanWdg.stopBtn.setHidden(True)
            self.stopBtn1.setHidden(True)
            self.stopBtn2.setHidden(True)
            self.progress_bar.setValue(100)

    def stop(self):
        self.timer.stop()
        LoopCallBack.stopped = True
        self.scanWdg.runBtn.setHidden(False)
        self.executeBtn.setHidden(False)
        self.previewBtn.setHidden(False)
        self.scanWdg.stopBtn.setHidden(True)
        self.stopBtn1.setHidden(True)
        self.stopBtn2.setHidden(True)
        self.progress_bar.setValue(100)

    def save_act(self):
        logging.info(f"Saving config to {CFG.configfile} ...")
        #self.get_config()
        CFG.save_config()

class LabelNLineEdit(QHBoxLayout):
    def __init__(self, parent, label, tooltip, placeholder='', fileselector=False, combobox_options='', checkbox=False, spinbox=False):
        super().__init__()

        self.parent = parent
        self.widget_list = []

        if checkbox:
            self.add_checkbox()

        if isinstance(label, tuple):
            self.add_labelbox(label)
        else:
            labelWdg = QLabel(label)
            self.addWidget(labelWdg)
        #self.widget_list += [labelWdg]

        if not combobox_options:
            self.textBox = self.add_lineedit(tooltip, placeholder)
        else:
            self.textBox = self.add_combobox(tooltip, placeholder, combobox_options)
            self.widget_list += [self.combo]
        self.widget_list += [self.textBox]

        if spinbox:
            roll_box = self.add_spinbox(spinbox)
            self.widget_list += [roll_box]

        if fileselector:
            self.btn_selector = self.add_fileselector_btn()
            self.widget_list += [self.btn_selector]

        if checkbox:
            self.toggle_widgets(self.checkBox.checkState())

    def toggle_widgets(self, e):
        for wdg in self.widget_list:
            wdg.setEnabled(bool(e))

    def add_labelbox(self, labels):

        self.labelbox = QComboBox()
        self.addWidget(self.labelbox)
        self.labelbox.addItems(labels)

    def add_checkbox(self):

        self.checkBox = QCheckBox()
        self.addWidget(self.checkBox)
        self.checkBox.toggled.connect(self.toggle_widgets)

    def add_spinbox(self, spin_label=False):

        self.spinBox = QSpinBox()
        self.spinBox.setRange(1,100)
        if spin_label:
            self.addWidget(QLabel(spin_label))
        self.addWidget(self.spinBox)

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

        if CFG['interface.gui_mode'] == GUI_SIMPLIFIED:
            combo.addItems(options)
            combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
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

        combo.activated.connect(callback)

        # Set default values (need to load values from textBox intead of config at MainTab.__init__)
        if CFG['interface.gui_mode'] == GUI_SIMPLIFIED:
            combo.setCurrentIndex(0)
            combo.currentIndexChanged.emit(0)

        return self.textBox

    def select_directory(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        directory = QFileDialog.getExistingDirectory(
            self.parent.parent, _("Selectionner le dossier"), options=options
        )

        if directory:
            self.textBox.setText(directory)

class DuplicateWdg(QHBoxLayout):

    def __init__(self, parent):

        super().__init__()

        self.duplicateBtn = simpleCheckBox(self, **DUP_RADIO_BUTTONS['duplicate']) #QCheckBox('Dupliqués : ')

        self.dup_grp = QButtonGroup(parent)
        dup_mode_Btns = {}
        dup_mode_Btns[DUP_MD5_FILE] = MyRadioButton(parent, **DUP_RADIO_BUTTONS['file']) #QRadioButton(_('Fichier'), parent)
        dup_mode_Btns[DUP_MD5_DATA] = MyRadioButton(parent, **DUP_RADIO_BUTTONS['data'])#QRadioButton(_('Données'), parent)
        dup_mode_Btns[DUP_DATETIME] = MyRadioButton(parent, **DUP_RADIO_BUTTONS['date'])#QRadioButton(_('Date'), parent)

        self.dup_grp.addButton(dup_mode_Btns[DUP_MD5_FILE], DUP_MD5_FILE)
        self.dup_grp.addButton(dup_mode_Btns[DUP_MD5_DATA], DUP_MD5_DATA)
        self.dup_grp.addButton(dup_mode_Btns[DUP_DATETIME], DUP_DATETIME)

        self.addWidget(dup_mode_Btns[DUP_MD5_FILE])
        self.addWidget(dup_mode_Btns[DUP_MD5_DATA])
        self.addWidget(dup_mode_Btns[DUP_DATETIME])
        self.scandestBtn = simpleCheckBox(self, **MTB['dup_is_scan_dest'])

    def set_dup_toggle(self, val):
        #CFG['is_control_duplicates'] = val
        self.scandestBtn.setDisabled(not val)
        for btn in self.dup_grp.buttons():
            btn.setDisabled(not val)

class fileActionWdg(QHBoxLayout):

    def __init__(self, parent):
        super().__init__()

        ckb_grp = QButtonGroup(parent)
        #ckb_grp.buttonClicked[int].connect(self.set_file_action)
        file_action_Btns = {}
        file_action_Btns[FILE_SIMULATE] = QRadioButton(_('Simuler'), parent)
        file_action_Btns[FILE_COPY] = QRadioButton(_('Copier'), parent)
        file_action_Btns[FILE_MOVE] = QRadioButton(_('Déplacer'), parent)

        ckb_grp.addButton(file_action_Btns[FILE_SIMULATE], FILE_SIMULATE)
        ckb_grp.addButton(file_action_Btns[FILE_COPY], FILE_COPY)
        ckb_grp.addButton(file_action_Btns[FILE_MOVE], FILE_MOVE)

        self.addWidget(file_action_Btns[FILE_SIMULATE])
        self.addWidget(file_action_Btns[FILE_COPY])
        self.addWidget(file_action_Btns[FILE_MOVE])

        self.btn_group = ckb_grp

class GPSTab(CollapsibleFrame):

    def __init__(self):

        super().__init__(_("tags GPS"), color="blue")

        main_layout = QVBoxLayout()

        list_layout = QVBoxLayout()
        list_widget = CopyableListWidget()
        self.listWdg = list_widget
        list_layout.addWidget(list_widget)

        self.populate_list()
        list_widget.setMaximumHeight(170)
        self.setMaximumHeight(200)

        main_layout.addLayout(list_layout)
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
        #frame.setLayout(layout)
        main_layout.addLayout(layout)
        self.setLayout(main_layout)
        self.collapse(True)

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

class ListExtsTab(CollapsibleFrame):
    def __init__(self):

        super().__init__(_("Extensions"), color='blue')
        list_layout = QVBoxLayout()
        list_widget = QListWidget()
        self.listextWdg = list_widget
        self.listextWdg.setViewMode(QListView.IconMode)
        self.listextWdg.setSpacing(10)
        self.listextWdg.setResizeMode(QListWidget.Adjust)
        self.listextWdg.itemChanged.connect(self.validate_ext)

        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.listextWdg.setSizePolicy(size_policy)

        list_layout.addWidget(list_widget)

        self.setLayout(list_layout)
        self.collapse(True)

    def validate_ext(self):
        self.user_choice_extentions = []
        for i in range(self.listextWdg.count()):
            item = self.listextWdg.item(i)
            if item.checkState():
                self.user_choice_extentions.append(item.text().strip("."))

        self.user_choice_extentions = ",".join(self.user_choice_extentions)
        logging.info(f"User extention selection : {self.user_choice_extentions}")

    def get_ext_list(self):
        self.listextWdg.clear()
        exts = list_available_exts(CFG["source.src_dir"], recursive=CFG["source.src_is_recursive"])
        for ext in exts:
            # item = QListWidgetItem(ext)
            item = ItemWidget(ext)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setTextAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
            item.setCheckState(Qt.Unchecked)
            self.listextWdg.addItem(item)
        self.listextWdg.repaint()

class ListCameraTab(CollapsibleFrame):
    def __init__(self):
        super().__init__(_("Appareil"), color='blue')
        list_layout = QVBoxLayout()
        list_widget = QListWidget()
        self.listappWdg = list_widget
        self.listappWdg.setViewMode(QListView.IconMode)
        self.listappWdg.setSpacing(10)
        self.listappWdg.setResizeMode(QListWidget.Adjust)
        self.listappWdg.itemChanged.connect(self.validate_cam)

        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.listappWdg.setSizePolicy(size_policy)

        list_layout.addWidget(list_widget)
        self.setLayout(list_layout)
        self.collapse(True)

    def validate_cam(self):

        user_choice_cameras = []
        for i in range(self.listappWdg.count()):
            item = self.listappWdg.item(i)
            if item.checkState():
                text = item.text().strip()
                user_choice_cameras.append(text)

        self.user_choice_cameras = ",".join(user_choice_cameras)
        logging.info(f"User extention selection : {self.user_choice_cameras}")

    def get_camera_list(self):

        self.listappWdg.clear()
        cameras = list_available_camera_model(CFG["source.src_dir"], CFG['source.src_extentions'], recursive=CFG['source.src_is_recursive'])
        for camera in cameras:
            # item = QListWidgetItem(ext)
            item = ItemWidget(camera)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setTextAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
            item.setCheckState(Qt.Unchecked)
            self.listappWdg.addItem(item)
        self.listappWdg.repaint()

class ListMetaTab(CollapsibleFrame):
    def __init__(self):
        super().__init__(_("Métadonnées"), color='blue')
        list_layout = QVBoxLayout()
        list_widget = CopyableListWidget()
        self.listmetaWdg = list_widget
        self.listmetaWdg.setAlternatingRowColors(True)

        btn_layout = QHBoxLayout()
        self.choose_box = ComboBox(self.show_tag_list)
        btn_layout.addWidget(self.choose_box)
        list_layout.addLayout(btn_layout)

        list_layout.addWidget(list_widget)
        self.setLayout(list_layout)
        self.collapse(True)

    def get_tag_list(self):

        self.exifs_lists = list_available_tags(
            CFG["source.src_dir"], CFG["source.src_extentions"], recursive=CFG['source.src_is_recursive']
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

        self.exifs_lists = list_available_tags(
            CFG["source.src_dir"], CFG["source.src_extentions"], recursive=CFG['source.src_is_recursive']
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
        self._progbar_nb_val = 1

    def add_label(self):
        self.text_label = QLabel("")
        return self.text_label

    def init(self, n):
        n = n if n else 1 # prevent no files founded
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

class DateTab(CollapsibleFrame):
    def __init__(self):
        super().__init__(_("Codes de formatage des dates"))

        self.collapse(True)
        main_layout = QVBoxLayout(self)

        strftime_help = open(STRFTIME_HELP_PATH).read()
        text_widget = QTextEdit()
        text_widget.setHtml(strftime_help)
        main_layout.addWidget(text_widget)

        self.setLayout(main_layout)

    def link_clicked(self, url):
        QDesktopServices.openUrl(url)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

