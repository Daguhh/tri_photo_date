#!/usr/bin/env python1

from configparser import ConfigParser
import sys, os
from pathlib import Path
import logging
import re
import time
from collections import deque

from tomlkit import parse

#from PyQt5.QtWidgets import QApplication, QWidget, QProgressBar
from PyQt5.QtGui import QPainter, QBrush, QColor, QPen
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QPieSlice, QValueAxis

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QThread, QTimer, QEventLoop, QSize, pyqtSignal, QPoint, QRect
from PyQt5.QtGui import (
    QKeySequence,
    QIcon,
    QPixmap,
    QClipboard,
    QStandardItem,
    QPixmap,
    QPainter,
    QFontMetrics,
    QBrush,
    QColor,
    QPen,
)
from PyQt5.QtChart import QChart, QChartView, QPieSeries, QPieSlice, QValueAxis
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
    QFileDialog,
    QStyle,
    QTabWidget,
    QAction,
    QListView,
    QSizePolicy,
    QMainWindow,
    QActionGroup,
    QDialog,
    QMenu,
    QAction,
    QComboBox,
    QTextEdit,
    QButtonGroup,
    QRadioButton,
    QSplitter,
    QToolBox,
    QSpinBox,
    QScrollArea,
)

# Local PyQt widgets
from tri_photo_date.gui import collapsible_frame
from tri_photo_date.gui.collapsible_frame import (
    CollapsibleFrame,
    PreviewCollapsibleFrame,
)
from tri_photo_date.gui import small_widgets
from tri_photo_date.gui.small_widgets import (
    simpleCheckBox,
    simpleLabelBox,
    simplePushButton,
    simpleStopButton,
    MyRadioButton,
    ItemWidget,
    OptionBool,
    ComboBox
)
from tri_photo_date.gui import menu as windowmenu
from tri_photo_date.gui import sqlite_view

# Constants
from tri_photo_date.exif import (
    TAG_DESCRIPTION,
    USEFULL_TAG_DESCRIPTION,
    EXIF_LOCATION_FIELD,
)
from tri_photo_date.utils.constants import (
    FILE_SIMULATE,
    FILE_COPY,
    FILE_MOVE,
    GUI_SIMPLIFIED,
    GUI_NORMAL,
    GUI_ADVANCED,
    DUP_MD5_FILE,
    DUP_MD5_DATA,
    DUP_DATETIME,
)
#from tri_photo_date.gui.strftime_help import DATE_STRFTIME_FORMAT
from tri_photo_date.gui.human_text import (
    GPS_HELP_TEXT,
    MEDIA_FORMATS,
    REL_PATH_FORMATS,
)
from tri_photo_date.config.config_paths import (
    STRFTIME_HELP_PATH,
    ICON_PATH,
    LOCALES_DIR,
    IMAGE_DATABASE_PATH,
)

# Texts
from tri_photo_date.gui.human_text import HUMAN_TEXT as HT
from tri_photo_date.gui.progressbar import MyProgressBar

from tri_photo_date.utils.small_tools import get_lang


def set_global_config(lang='en', size=1, mode=GUI_ADVANCED):

    lang = get_lang(lang)
    windowmenu.set_global_config(lang, size, mode)
    collapsible_frame.set_global_config(lang, size, mode)
    sqlite_view.set_global_config(lang, size, mode)
    small_widgets.set_global_config(lang, size, mode)

    import gettext

    trad = gettext.translation("base", localedir=LOCALES_DIR, languages=[lang])
    trad.install()

    global _
    _ = trad.gettext  # Greek

    os.environ["QT_SCALE_FACTOR"] = size

    global GUI_MODE
    GUI_MODE = mode


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

class MainWindow_ui(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("TriPhotoDate")
        self.setWindowIcon(QIcon(str(ICON_PATH)))

        self.menubar = windowmenu.WindowMenu(self)
        self.setMenuBar(self.menubar)

        main_windows_wdg = QWidget()
        main_windows_lyt = QHBoxLayout()
        splitter = QSplitter()
        splitter.setHandleWidth(3)

        self.conf_panel = MainTab(self)

        self.tool_panel = QWidget()
        toolboxLyt = QVBoxLayout()

        self.tool_panel.exts = ListExtsTab()
        self.tool_panel.meta = ListMetaTab()
        self.tool_panel.cam = ListCameraTab()
        self.tool_panel.date = DateTab()
        self.tool_panel.gps = GPSTab()

        toolboxLyt.addWidget(self.tool_panel.exts)
        toolboxLyt.addWidget(self.tool_panel.meta)
        toolboxLyt.addWidget(self.tool_panel.cam)
        toolboxLyt.addWidget(self.tool_panel.date)
        toolboxLyt.addWidget(self.tool_panel.gps)
        toolboxLyt.addStretch()

        self.tool_panel.setLayout(toolboxLyt)

        toolscroll_area = QScrollArea()
        toolscroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        toolscroll_area.setWidgetResizable(True)
        conf_panel_content = QWidget()
        conf_panel_content.setLayout(QVBoxLayout())
        conf_panel_content.layout().addWidget(self.tool_panel)
        toolscroll_area.setWidget(conf_panel_content)

        preview_frame = PreviewCollapsibleFrame(_(" Afficher un aperçu"), "green")
        self.preview_wdg = sqlite_view.DatabaseViewer(str(IMAGE_DATABASE_PATH))
        preview_frame.setWidget(self.preview_wdg)

        tabs = QTabWidget()
        tabs.setMinimumWidth(450)
        tabs.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        tabs.setMaximumWidth(700)
        tabs.setTabPosition(QTabWidget.West)

        scroll_area = QScrollArea()
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setWidgetResizable(True)
        conf_panel_content = QWidget()
        conf_panel_content.setLayout(QVBoxLayout())
        conf_panel_content.layout().addWidget(self.conf_panel)
        scroll_area.setWidget(conf_panel_content)

        if GUI_MODE == GUI_SIMPLIFIED:
            splitter.addWidget(self.conf_panel)
            tabs.setHidden(True)

        elif GUI_MODE == GUI_ADVANCED:
            tabs.addTab(scroll_area, _("Main"))

        tabs.addTab(toolscroll_area, _("Outils"))
        splitter.addWidget(tabs)

        splitter.addWidget(preview_frame)

        main_windows_lyt.addWidget(splitter)

        main_windows_wdg.setLayout(main_windows_lyt)
        self.setCentralWidget(main_windows_wdg)

        size = self.sizeHint()
        self.resize(400, 500)
        preview_frame.collapse(True)

        self.setup_interconnections()

    def setup_interconnections(self):
        self.tool_panel.exts.listext_wdg.itemChanged.connect(
            lambda: self.conf_panel.src_frame.ext_wdg.textBox.setText(
                self.tool_panel.exts.user_choice_extentions
            )
        )
        self.tool_panel.cam.listapp_wdg.itemChanged.connect(
            lambda: self.conf_panel.src_frame.cam_wdg.textBox.setText(
                self.tool_panel.cam.user_choice_cameras
            )
        )
        # self.preview_wdg.filter_edit.textChanged.connect(self.update_preview)

        # Link scan lineedit to source and destination sections
        self.conf_panel.src_frame.dir_wdg.textBox.textChanged.connect(
            self.conf_panel.scan_frame.srcdir_wdg.textBox.setText
        )
        self.conf_panel.dest_frame.dir_wdg.textBox.textChanged.connect(
            self.conf_panel.scan_frame.destdir_wdg.textBox.setText
        )


class MainTab(QWidget):
    def __init__(self, parent):
        super().__init__()

        self.parent = parent

        main_layout = QVBoxLayout()

        ########## Scan ##########
        scan_frame = CollapsibleFrame(_("Scan"), color="darkGreen")
        layout = QVBoxLayout()

        scan_frame.srcdir_wdg = LabelNLineEdit(self, **HT['scan']["src_dir"])
        layout.addLayout(scan_frame.srcdir_wdg)
        scan_frame.destdir_wdg = LabelNLineEdit(self, **HT['scan']["dest_dir"])
        layout.addLayout(scan_frame.destdir_wdg)
        scan_frame.exts_wdg = LabelNLineEdit(self, **HT['scan']["extentions"])
        layout.addLayout(scan_frame.exts_wdg)
        sub_layout = QHBoxLayout()
        scan_frame.is_use_cache = simpleCheckBox(
            sub_layout, **HT['scan']["is_use_cached_datas"]
        )
        layout.addLayout(sub_layout)

        scan_frame.setLayout(layout)
        scan_frame.collapse(True)
        main_layout.addWidget(scan_frame)

        self.populateBtn = simplePushButton(main_layout, **HT['action']["populate"])
        #self.populateBtn.clicked.connect(self.populate_event)
        self.stopBtn = simpleStopButton(main_layout, self.stop)

        scan_frame.progbar_layout = QVBoxLayout()

        main_layout.addLayout(scan_frame.progbar_layout)

        # Disable "coming soon"
        scan_frame.srcdir_wdg.textBox.setReadOnly(True)
        scan_frame.destdir_wdg.textBox.setReadOnly(True)
        # scan_frame.dir_wdg.btn_selector.setDisabled(True)
        # scan_frame.dir_wdg.recursiveBtn.setDisabled(True)
        # scan_frame.is_metaBtn.setDisabled(True)
        # scan_frame.is_md5_file.setDisabled(True)
        # scan_frame.is_md5_data.setDisabled(True)

        self.scan_frame = scan_frame

        self.run_populate = self.gen_run_function(
            self.populateBtn,
            self.stopBtn,
            self.scan_frame.progbar_layout
        )

        ########## Source ##########
        src_frame = CollapsibleFrame(_("Source"))
        layout = QVBoxLayout()

        src_frame.dir_wdg = LabelNLineEdit(self, **HT['source']["dir"])
        src_frame.dir_wdg.recursiveBtn = simpleCheckBox(
            src_frame.dir_wdg, **HT['source']["is_recursive"]
        )
        src_frame.ext_wdg = LabelNLineEdit(self, **HT['source']["extentions"])
        src_frame.cam_wdg = LabelNLineEdit(self, **HT['source']["cameras"])
        src_frame.exclude_wdg = LabelNLineEdit(self, **HT['source']["excluded_dirs"])
        src_frame.exclude_wdg.is_regex = simpleCheckBox(
            src_frame.exclude_wdg, **HT['source']["is_exclude_dir_regex"]
        )

        layout.addLayout(src_frame.dir_wdg)
        layout.addLayout(src_frame.ext_wdg)
        if not GUI_MODE == GUI_SIMPLIFIED:
            layout.addLayout(src_frame.cam_wdg)
            layout.addLayout(src_frame.exclude_wdg)
        src_frame.setLayout(layout)
        main_layout.addWidget(src_frame)

        self.src_frame = src_frame

        ########## Destination ##########
        dest_frame = CollapsibleFrame(_("Destination"), color="blue")
        layout = QVBoxLayout()

        dest_frame.dir_wdg = LabelNLineEdit(self, **HT['destination']["out_dir"])
        dest_frame.rel_dir_wdg = LabelNLineEdit(self, **HT['destination']["out_path_str"])
        dest_frame.filename_wdg = LabelNLineEdit(self, **HT['destination']["filename"])

        layout.addLayout(dest_frame.dir_wdg)
        layout.addLayout(dest_frame.rel_dir_wdg)
        layout.addLayout(dest_frame.filename_wdg)

        dest_frame.setLayout(layout)
        main_layout.addWidget(dest_frame)

        self.dest_frame = dest_frame

        ########## Duplicates ##########
        dup_frame = CollapsibleFrame(_("Dupliqués"), color="blue")
        layout = QVBoxLayout()
        dup_frame.dupBtns = DuplicateWdg(self)
        layout.addLayout(dup_frame.dupBtns)
        dup_frame.procedureBox = simpleLabelBox(layout, **HT['duplicates']['procedure'])
        dup_frame.dupBtns.duplicateBtn.stateChanged.connect(lambda val : dup_frame.procedureBox.setEnabled(val))
        dup_frame.dupBtns.duplicateBtn.stateChanged.emit(False)
        dup_frame.setLayout(layout)
        main_layout.addWidget(dup_frame)

        self.dup_frame = dup_frame

        ########## Options ##########
        opt_frame = CollapsibleFrame(_("Options"), color="blue")

        layout = QVBoxLayout()
        sub_layout = QHBoxLayout()

        opt_frame.guess_date_from_name = LabelNLineEdit(
            self, **HT["options"]['name']["guess_date_from_name"]
        )
        opt_frame.group_by_floating_days = LabelNLineEdit(
            self, **HT['options']['group']["group_by_floating_days"]
        )

        layout.addLayout(opt_frame.guess_date_from_name)
        layout.addLayout(opt_frame.group_by_floating_days)

        sub_layout = QHBoxLayout()
        opt_frame.gps = simpleCheckBox(sub_layout, **HT['gps']["gps"])
        layout.addLayout(sub_layout)

        sub_layout = QHBoxLayout()

        opt_frame.is_delete_metadatas = simpleCheckBox(
            sub_layout, **HT['options']['general']["is_delete_metadatas"]
        )
        layout.addLayout(sub_layout)

        sub_layout = QHBoxLayout()
        opt_frame.is_date_from_filesystem = simpleCheckBox(
            sub_layout, **HT['options']['general']["is_date_from_filesystem"]
        )
        opt_frame.is_force_date_from_filesystem = simpleCheckBox(
            sub_layout, **HT['options']['general']["is_force_date_from_filesystem"]
        )
        opt_frame.is_date_from_filesystem.stateChanged.connect(
            lambda e: opt_frame.is_force_date_from_filesystem.setEnabled(bool(e))
        )
        opt_frame.is_date_from_filesystem.stateChanged.emit(False)

        layout.addLayout(sub_layout)

        opt_frame.setLayout(layout)
        opt_frame.collapse()
        main_layout.addWidget(opt_frame)

        self.opt_frame = opt_frame

        self.previewBtn = simplePushButton(main_layout, **HT['action']["calculate"])
        #self.previewBtn.clicked.connect(self.preview_event)
        self.stopBtn1 = simpleStopButton(main_layout, self.stop)

        if GUI_MODE == GUI_SIMPLIFIED:
            self.opt_frame.setHidden(True)

        self.compute_act_prog_holder = QVBoxLayout()
        main_layout.addLayout(self.compute_act_prog_holder)

        self.run_preview = self.gen_run_function(
            self.previewBtn,
            self.stopBtn1,
            self.compute_act_prog_holder
        )

        ########## Save & Run ##########
        exec_frame = CollapsibleFrame("Executer", color="red")
        layout = QVBoxLayout()
        exec_frame.file_action_wdg = fileActionWdg(self)
        layout.addLayout(exec_frame.file_action_wdg)
        exec_frame.setLayout(layout)
        main_layout.addWidget(exec_frame)

        self.exec_frame = exec_frame

        self.executeBtn = simplePushButton(main_layout, **HT['action']["execute"])
        #self.executeBtn.clicked.connect(self.execute_event)
        self.stopBtn2 = simpleStopButton(main_layout, self.stop)

        self.execute_act_prog_holder = QVBoxLayout()
        main_layout.addLayout(self.execute_act_prog_holder)

        # Progress bar
        self.progress_bar = MyProgressBar(self)

        self.run_execute = self.gen_run_function(
            self.executeBtn,
            self.stopBtn2,
            self.execute_act_prog_holder
        )
        # Counters


        main_layout.addStretch()

        # size = self.sizeHint()
        # self.setMinimumHeight(size.height())

        # Create run functions

        self.setLayout(main_layout)

    def gen_run_function(self, runBtn, stopBtn, progbarLyt):

        def _function(func, after=lambda:None):
            logging.info("Starting processing files...")

            self.progress_bar.move_to_layout(progbarLyt)

            runBtn.setHidden(True)
            stopBtn.setHidden(False)

            LoopCallBack.stopped = False
            self.timer = QTimer()

            self.timer.timeout.connect(
                lambda: self.run_function(
                    func, self.progress_bar, LoopCallBack
                )
            )
            self.timer.timeout.connect(after)
            self.timer.start(1000)  # waits for 1 second

        return _function

    def run_function(self, func, *args, **kwargs):
        if not LoopCallBack.stopped:
            func(*args, **kwargs)
        if LoopCallBack.stopped:
            self.stop()

    def stop(self):
        self.timer.stop()
        LoopCallBack.stopped = True
        self.populateBtn.setHidden(False)
        self.executeBtn.setHidden(False)
        self.previewBtn.setHidden(False)
        self.stopBtn.setHidden(True)
        self.stopBtn1.setHidden(True)
        self.stopBtn2.setHidden(True)
        #self.progress_bar.setValue(100)


class LabelNLineEdit(QHBoxLayout):
    def __init__(
        self,
        parent,
        label,
        tooltip,
        placeholder="",
        fileselector=False,
        combobox_options="",
        checkbox=False,
        spinbox=False,
    ):
        super().__init__()

        self.parent = parent
        self.widget_list = []

        if checkbox:
            self.add_checkbox()

        if isinstance(label, list):
            self.add_labelbox(label)
        else:
            label_wdg = QLabel(label)
            self.addWidget(label_wdg)
        # self.widget_list += [labelWdg]

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
        self.spinBox.setRange(1, 100)
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
        combo.setToolTip(tooltip)
        self.addWidget(combo)
        self.combo = combo

        if GUI_MODE == GUI_SIMPLIFIED:
            combo.addItems(options)
            combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            #self.textBox = QLineEdit()
            self.textBox = CustomQLineEdit(combo=combo)
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
            for k, v in MEDIA_FORMATS.items():
                text = re.sub(k, v, text)
            for k, v in REL_PATH_FORMATS.items():
                text = re.sub(k, v, text)
            self.textBox.setText(text)
            self.textBox.textChanged.emit(text)
            self.combo.clearFocus()  # prevent combo to capture all signals

        combo.activated.connect(callback)

        # Set default values (need to load values from textBox intead of config at MainTab.__init__)
        #if GUI_MODE == GUI_SIMPLIFIED:
        #    combo.setCurrentIndex(0)
        #    combo.currentIndexChanged.emit(0)

        return self.textBox

    def select_directory(self):
        options = QFileDialog.Options()
        options |= QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        directory = QFileDialog.getExistingDirectory(
            self.parent.parent, _("Selectionner le dossier"), options=options
        )

        if directory:
            self.textBox.setText(directory)

class CustomQLineEdit(QLineEdit):
    def __init__(self, combo):
        super().__init__()
        self.combo = combo

    def setText(self, lineedit_txt):

        # If called manually (at startup to load config)
        # Set combobox element that match hidden QLineEdit
        if self.sender() is None:
            match = False
            for i in range(self.combo.count()):
                combo_txt = self.combo.itemText(i)

                #import ipdb; ipdb.set_trace()
                dcts = MEDIA_FORMATS | REL_PATH_FORMATS
                combo_txt = re.sub(combo_txt, dcts.get(combo_txt, combo_txt), combo_txt)

                if lineedit_txt == combo_txt:
                    self.combo.setCurrentIndex(i)
                    #super().setText(combo_txt)
                    self.combo.activated.emit(0)
                    match = True
                    break

            # If no match set the first element
            if not match:
                self.combo.setCurrentIndex(0)
                self.combo.activated.emit(0)
                #super().setText(self.combo.currentText())

        # If call by another widget : continue as normal
        else:
            super().setText(lineedit_txt)

        #self.combo.activated.emit()

class DuplicateWdg(QHBoxLayout):
    def __init__(self, parent):
        super().__init__()

        self.duplicateBtn = simpleCheckBox(
            self, **HT['duplicates']["is_duplicate"]
        )  # QCheckBox('Dupliqués : ')

        self.duplicateBtn.stateChanged.connect(self.set_dup_toggle)

        self.dup_grp = QButtonGroup(parent)
        mode_Btns = {}
        mode_Btns[DUP_MD5_FILE] = MyRadioButton(
            parent, **HT['duplicates']["file"]
        )  # QRadioButton(_('Fichier'), parent)
        mode_Btns[DUP_MD5_DATA] = MyRadioButton(
            parent, **HT['duplicates']["data"]
        )  # QRadioButton(_('Données'), parent)
        mode_Btns[DUP_DATETIME] = MyRadioButton(
            parent, **HT['duplicates']["date"]
        )  # QRadioButton(_('Date'), parent)

        self.dup_grp.addButton(mode_Btns[DUP_MD5_FILE], DUP_MD5_FILE)
        self.dup_grp.addButton(mode_Btns[DUP_MD5_DATA], DUP_MD5_DATA)
        self.dup_grp.addButton(mode_Btns[DUP_DATETIME], DUP_DATETIME)

        self.addWidget(mode_Btns[DUP_MD5_FILE])
        self.addWidget(mode_Btns[DUP_MD5_DATA])
        self.addWidget(mode_Btns[DUP_DATETIME])
        self.scandestBtn = simpleCheckBox(self, **HT['duplicates']["is_scan_dest"])

        self.duplicateBtn.stateChanged.emit(False)

    def set_dup_toggle(self, val):
        self.scandestBtn.setDisabled(not val)
        for btn in self.dup_grp.buttons():
            btn.setDisabled(not val)

class fileActionWdg(QHBoxLayout):
    def __init__(self, parent):
        super().__init__()

        ckb_grp = QButtonGroup(parent)
        # ckb_grp.buttonClicked[int].connect(self.set_file_action)
        file_action_Btns = {}
        file_action_Btns[FILE_SIMULATE] = QRadioButton(_("Simuler"), parent)
        file_action_Btns[FILE_COPY] = QRadioButton(_("Copier"), parent)
        file_action_Btns[FILE_MOVE] = QRadioButton(_("Déplacer"), parent)

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
        self.list_wdg = list_widget
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
        #btn.clicked.connect(self.run_gps_act)

        self.runBtn = btn

        layout.addLayout(btn_layout)
        # frame.setLayout(layout)
        main_layout.addLayout(layout)
        self.setLayout(main_layout)
        self.collapse(True)

    def populate_list(self):
        tags = EXIF_LOCATION_FIELD.values()

        for tag in tags:
            item = ItemWidget(tag)
            self.list_wdg.addItem(item)
        self.list_wdg.repaint()

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
        text = "<" + item.text().split("\t")[0].strip() + ">"
        QApplication.clipboard().setText(text)

class ListExtsTab(CollapsibleFrame):
    def __init__(self):
        super().__init__(_("Extensions"), color="blue")
        list_layout = QVBoxLayout()
        list_widget = QListWidget()
        self.listext_wdg = list_widget
        self.listext_wdg.setViewMode(QListView.IconMode)
        self.listext_wdg.setSpacing(10)
        self.listext_wdg.setResizeMode(QListWidget.Adjust)
        self.listext_wdg.itemChanged.connect(self.validate_ext)

        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.listext_wdg.setSizePolicy(size_policy)

        list_layout.addWidget(list_widget)

        self.setLayout(list_layout)
        self.collapse(True)

    def validate_ext(self):
        self.user_choice_extentions = []
        for i in range(self.listext_wdg.count()):
            item = self.listext_wdg.item(i)
            if item.checkState():
                self.user_choice_extentions.append(item.text().strip("."))

        self.user_choice_extentions = ",".join(self.user_choice_extentions)
        logging.info(f"User extention selection : {self.user_choice_extentions}")

    def set_ext_list(self, exts=[]):
        self.listext_wdg.clear()

        for ext in exts:
            # item = QListWidgetItem(ext)
            item = ItemWidget(ext)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setTextAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
            item.setCheckState(Qt.Unchecked)
            self.listext_wdg.addItem(item)
        self.listext_wdg.repaint()

class ListCameraTab(CollapsibleFrame):
    def __init__(self):
        super().__init__(_("Appareil"), color="blue")
        list_layout = QVBoxLayout()
        list_widget = QListWidget()
        self.listapp_wdg = list_widget
        self.listapp_wdg.setViewMode(QListView.IconMode)
        self.listapp_wdg.setSpacing(10)
        self.listapp_wdg.setResizeMode(QListWidget.Adjust)
        self.listapp_wdg.itemChanged.connect(self.validate_cam)

        size_policy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.listapp_wdg.setSizePolicy(size_policy)

        list_layout.addWidget(list_widget)
        self.setLayout(list_layout)
        self.collapse(True)

    def validate_cam(self):
        user_choice_cameras = []
        for i in range(self.listapp_wdg.count()):
            item = self.listapp_wdg.item(i)
            if item.checkState():
                text = item.text().strip()
                user_choice_cameras.append(text)

        self.user_choice_cameras = ",".join(user_choice_cameras)
        logging.info(f"User extention selection : {self.user_choice_cameras}")

    def set_camera_list(self, cameras):
        self.listapp_wdg.clear()
        for camera in cameras:
            # item = QListWidgetItem(ext)
            item = ItemWidget(camera)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setTextAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignLeft)
            item.setCheckState(Qt.Unchecked)
            self.listapp_wdg.addItem(item)
        self.listapp_wdg.repaint()

class ListMetaTab(CollapsibleFrame):
    def __init__(self):
        super().__init__(_("Métadonnées"), color="blue")
        list_layout = QVBoxLayout()
        list_widget = CopyableListWidget()
        self.listmeta_wdg = list_widget
        self.listmeta_wdg.setAlternatingRowColors(True)

        btn_layout = QHBoxLayout()
        self.choose_box = ComboBox(self.show_tag_list)
        btn_layout.addWidget(self.choose_box)
        list_layout.addLayout(btn_layout)

        list_layout.addWidget(list_widget)
        self.setLayout(list_layout)
        self.collapse(True)

        self.exifs_lists = ([],[])

    def set_tag_list(self, tags_list):
        self.exifs_lists = tags_list

        option = self.choose_box.currentText()
        self.show_tag_list(option)

    def show_tag_list(self, option=_("utiles")):
        self.listmeta_wdg.clear()

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
            self.listmeta_wdg.addItem(item)

class DateTab(CollapsibleFrame):
    def __init__(self):
        super().__init__(_("Codes de formatage des dates"))

        self.collapse(True)

        layout = QHBoxLayout()
        strftime_help = open(STRFTIME_HELP_PATH).read()
        text_widget = QTextEdit()
        text_widget.setHtml(strftime_help)
        layout.addWidget(text_widget)
        self.setLayout(layout)

    def link_clicked(self, url):
        QDesktopServices.openUrl(url)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
