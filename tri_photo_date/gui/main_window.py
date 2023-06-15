#!/usr/bin/env python1

from configparser import ConfigParser
import sys, os
from pathlib import Path
import logging
import re

from PyQt5 import QtCore
from PyQt5.QtCore import Qt, QThread, QTimer, QEventLoop, QSize
from PyQt5.QtGui import (
    QKeySequence,
    QIcon,
    QPixmap,
    QClipboard,
    QStandardItem,
    QPixmap,
    QPainter,
    QFontMetrics,
)
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

# Modules
from tri_photo_date.gui.sqlite_view import DatabaseViewer
from tri_photo_date import ordonate_photos
from tri_photo_date.ordonate_photos import CFG
from tri_photo_date.gui.menu import WindowMenu, SettingFilePopup
from tri_photo_date.explore_db import (
    list_available_camera_model,
    list_available_exts,
    list_available_tags,
)

# Local PyQt widgets
from tri_photo_date.gui.collapsible_frame import (
    CollapsibleFrame,
    PreviewCollapsibleFrame,
)
from tri_photo_date.gui.small_widgets import (
    simpleCheckBox,
    simplePushButton,
    simpleStopButton,
    MyRadioButton,
)

# Constants
from tri_photo_date.exif import (
    TAG_DESCRIPTION,
    USEFULL_TAG_DESCRIPTION,
    EXIF_LOCATION_FIELD,
)
from tri_photo_date.utils.config_loader import (
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
from tri_photo_date.gui.strftime_help import DATE_STRFTIME_FORMAT
from tri_photo_date.gui.human_text import (
    GPS_HELP_TEXT,
    MEDIA_FORMATS,
    REL_PATH_FORMATS,
    ACTION_BUTTONS,
    DUP_RADIO_BUTTONS,
)
from tri_photo_date.gui.human_text import MAIN_TAB_WIDGETS as MTW
from tri_photo_date.gui.human_text import MAIN_TAB_BUTTONS as MTB
from tri_photo_date.utils.config_paths import (
    STRFTIME_HELP_PATH,
    ICON_PATH,
    LOCALES_DIR,
    IMAGE_DATABASE_PATH,
)


lang = CFG["interface.lang"]
import gettext

trad = gettext.translation("base", localedir=LOCALES_DIR, languages=[lang])
trad.install()
_ = trad.gettext  # Greek

os.environ["QT_SCALE_FACTOR"] = CFG["interface.size"]

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

class MainWindow_ui(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Tri photo")
        self.setWindowIcon(QIcon(str(ICON_PATH)))

        self.menubar = WindowMenu(self)
        self.setMenuBar(self.menubar)

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


        preview_frame = PreviewCollapsibleFrame(" Afficher un aperçu", "green")
        self.preview_wdg = DatabaseViewer(str(IMAGE_DATABASE_PATH))
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

        if CFG["interface.mode"] == GUI_SIMPLIFIED:
            splitter.addWidget(self.tab1)
            tabs.setHidden(True)

        elif CFG["interface.mode"] == GUI_ADVANCED:
            tabs.addTab(scroll_area, "Main")

        tabs.addTab(toolscroll_area, _("Outils"))
        splitter.addWidget(tabs)

        splitter.addWidget(preview_frame)

        main_windows_lyt.addWidget(splitter)

        main_windows_wdg.setLayout(main_windows_lyt)
        self.setCentralWidget(main_windows_wdg)

        size = self.sizeHint()
        self.resize(400, 500)
        preview_frame.collapse(True)

class MainWindow(MainWindow_ui):
    def __init__(self):
        super().__init__()

        # Set up connection to config object
        wdgs = {}
        wdgs['scan.src_dir'] = self.tab1.scanFrame.srcdirWdg.textBox
        wdgs['scan.dest_dir'] = self.tab1.scanFrame.destdirWdg.textBox
        #wdgs['("scan.'] = self.tab1.scanWdg.is_metaBtn.stateChanged
        #wdgs['("scan.'] = self.tab1.scanFrame.is_md5_data.stateChanged
        #wdgs['("scan.'] = self.tab1.scanFrame.is_md5_file.stateChanged
        wdgs['scan.is_use_cached_datas'] = self.tab1.scanFrame.is_use_cache
        #wdgs['("scan.'] = self.tab1.scanFrame.dirWdg.recursiveBtn.stateChanged

        wdgs['source.dir'] = self.tab1.srcFrame.dirWdg.textBox
        wdgs['source.extentions'] = self.tab1.srcFrame.extWdg.textBox
        wdgs['source.cameras'] = self.tab1.srcFrame.camWdg.textBox
        wdgs['source.is_recursive'] = self.tab1.srcFrame.dirWdg.recursiveBtn
        wdgs['source.excluded_dirs'] = self.tab1.srcFrame.excludeWdg.textBox
        wdgs['source.exclude_toggle'] = self.tab1.srcFrame.excludeWdg.labelbox
        wdgs['source.is_exclude_dir_regex'] = self.tab1.srcFrame.excludeWdg.is_regex

        wdgs['destination.dir'] = self.tab1.destFrame.dirWdg.textBox
        wdgs['destination.rel_dir'] = self.tab1.destFrame.rel_dirWdg.textBox
        wdgs['destination.filename'] = self.tab1.destFrame.filenameWdg.textBox

        wdgs['duplicates.is_control'] = self.tab1.dupFrame.dupBtns.duplicateBtn
        wdgs['duplicates.mode'] = self.tab1.dupFrame.dupBtns.dup_grp
        wdgs['duplicates.is_scan_dest'] = self.tab1.dupFrame.dupBtns.scandestBtn

        wdgs['options.name.guess_fmt'] = self.tab1.optFrame.guess_date_from_name.textBox
        wdgs['options.name.is_guess'] = self.tab1.optFrame.guess_date_from_name.checkBox
        wdgs['options.group.is_group'] = self.tab1.optFrame.group_by_floating_days.checkBox
        wdgs['options.group.display_fmt'] = self.tab1.optFrame.group_by_floating_days.textBox
        wdgs['options.group.floating_nb'] = self.tab1.optFrame.group_by_floating_days.spinBox
        wdgs['options.gps.is_gps'] = self.tab1.optFrame.gps
        wdgs['options.general.is_delete_metadatas'] = self.tab1.optFrame.is_delete_metadatas
        wdgs['options.general.is_date_from_filesystem'] = self.tab1.optFrame.is_date_from_filesystem

        wdgs['action.action_mode'] = self.tab1.execFrame.file_actionWdg.btn_group
        wdgs['interface.mode'] = self.menubar.mode_group
        wdgs['interface.lang'] = self.menubar.lang_group
        wdgs['interface.size'] = self.menubar.size_group


        self.wdgs = wdgs

        self.setup_interconnections()
        self.setup_actions()

        self.connect_menubar_2_config()
        self.connect_wdgs_2_config()

        self.load_conf()

    def setup_interconnections(self):

        self.tab2.listextWdg.itemChanged.connect(
            lambda : self.tab1.srcFrame.extWdg.textBox.setText(self.tab2.user_choice_extentions)
        )
        self.tab4.listappWdg.itemChanged.connect(
            lambda : self.tab1.srcFrame.camWdg.textBox.setText(self.tab4.user_choice_cameras)
        )
        self.preview_wdg.filter_edit.textChanged.connect(self.update_preview)

        # Link scan lineedit to source and destination sections
        self.tab1.srcFrame.dirWdg.textBox.textChanged.connect(
            self.tab1.scanFrame.srcdirWdg.textBox.setText
        )
        self.tab1.destFrame.dirWdg.textBox.textChanged.connect(
            self.tab1.scanFrame.destdirWdg.textBox.setText
        )

    def setup_actions(self):
        self.tab1.runBtn.clicked.connect(self.populate_act)
        self.tab1.runBtn.clicked.connect(self.update_selection_tabs)
        self.tab1.previewBtn.clicked.connect(self.preview_act)
        self.tab1.executeBtn.clicked.connect(self.run_act)

    def connect_wdgs_2_config(self):

        for prop, wdg in self.wdgs.items():
            callback = lambda x, prop=prop: CFG.__setitem__(prop, x)
            if isinstance(wdg, QLineEdit):
                wdg.textChanged.connect(callback)
            elif isinstance(wdg, QCheckBox):
                wdg.stateChanged.connect(callback)
            elif isinstance(wdg, QSpinBox):
                wdg.valueChanged.connect(callback)
            elif isinstance(wdg, QComboBox):
                wdg.currentIndexChanged.connect(callback)
            elif isinstance(wdg, QButtonGroup):
                wdg.buttonClicked[int].connect(callback)
            elif isinstance(wdg, QAction):
                pass # link manually to specific action

    def connect_menubar_2_config(self):

        #self.menubar.load_action.triggered.connect(self.load)
        #self.menubar.save_action.triggered.connect(self.save)
        self.menubar.config_action.triggered.connect(self.menubar.open_file_browser)
        self.menubar.set_settings_action.triggered.connect(self.show_set_settings)
        self.menubar.mode_group.triggered.connect(self.set_interface_mode)
        self.menubar.size_group.triggered.connect(self.set_interface_size)
        self.menubar.lang_group.triggered.connect(self.set_language)
        self.menubar.debug_action.triggered.connect(self.menubar.debug_toggle)
        self.menubar.debug_action.setChecked(CFG["misc.verbose"])

    def load_conf(self):

        for prop, wdg in self.wdgs.items():
            if isinstance(wdg, QLineEdit):
                wdg.setText(CFG.get_repr(prop))
            elif isinstance(wdg, QCheckBox):
                wdg.setCheckState(CFG.get_repr(prop))
            elif isinstance(wdg, QSpinBox):
                wdg.setValue(CFG.get_repr(prop))
            elif isinstance(wdg, QComboBox):
                wdg.setCurrentIndex(CFG.get_repr(prop))
            elif isinstance(wdg, QButtonGroup):
                wdg.button(CFG.get_repr(prop)).setChecked(True)
            elif isinstance(wdg, QActionGroup):
                for act in wdg.actions():
                    if act.data() == CFG.get_repr(prop):
                        act.setChecked(True)

    def load_settings_conf(self):

        for prop, wdg in self.wdgs_settings.items():
            if isinstance(wdg, QCheckBox):
                wdg.setCheckState(CFG.get_repr(prop))
            elif isinstance(wdg, QSpinBox):
                wdg.setValue(CFG.get_repr(prop))

        #for section_name, section_dct in self.Wdgs.items():
        #    for param, wdg_setter in section_dct.items():
        #        wdg_setter(CFG.get_repr((section_name, param)))
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
        self.save_act()
        QApplication.quit()

    def closeEvent(self, event):
        self.save_act()
        super().closeEvent(event)

    def populate_act(self):
        logging.info("Starting processing files...")

        self.tab1.move_progbar(self.tab1.scanFrame.progbar_layout)

        self.save_act()
        self.tab1.runBtn.setHidden(True)
        self.tab1.stopBtn.setHidden(False)

        LoopCallBack.stopped = False
        self.tab1.timer = QTimer()

        self.tab1.timer.timeout.connect(
            lambda: self.tab1.run_function(
                ordonate_photos.populate_db, self.tab1.progress_bar, LoopCallBack
            )
        )
        self.tab1.timer.timeout.connect(self.update_preview)
        self.tab1.timer.start(1000)  # waits for 1 second

    def preview_act(self):
        logging.info("Starting processing files...")

        self.tab1.move_progbar(self.tab1.compute_act_prog_holder)

        self.save_act()
        self.tab1.previewBtn.setHidden(True)
        self.tab1.stopBtn1.setHidden(False)

        LoopCallBack.stopped = False
        self.tab1.timer = QTimer()
        self.tab1.timer.timeout.connect(
            lambda: self.tab1.run_function(
                ordonate_photos.compute, self.tab1.progress_bar, LoopCallBack
            )
        )
        self.tab1.timer.timeout.connect(self.update_preview)
        self.tab1.timer.start(1000)  # waits for 1 second

    def run_act(self):
        logging.info("Starting processing files...")

        self.tab1.move_progbar(self.tab1.execute_act_prog_holder)

        self.save_act()
        self.tab1.executeBtn.setHidden(True)
        self.tab1.stopBtn2.setHidden(False)

        LoopCallBack.stopped = False
        self.tab1.timer = QTimer()
        self.tab1.timer.timeout.connect(
            lambda: self.tab1.run_function(
                ordonate_photos.execute, self.tab1.progress_bar, LoopCallBack
            )
        )
        self.tab1.timer.start(1000)  # waits for 1 second

    def save_act(self):
        logging.info(f"Saving config to {CFG.configfile} ...")
        # self.get_config()
        CFG.save_config()

    def show_set_settings(self):

        popup = SettingFilePopup()

        wdgs = {}
        wdgs['files.is_max_hash_size'] = popup.ckb_max_hash
        wdgs['files.max_hash_size'] = popup.spin_max_hash
        wdgs['files.is_min_size'] = popup.ckb_min_size
        wdgs['files.min_size'] = popup.spin_min_size
        wdgs['files.is_max_size'] = popup.ckb_max_size
        wdgs['files.max_size'] = popup.spin_max_size

        self.wdgs_settings = wdgs
        self.load_settings_conf()

        res = popup.exec_()
        if res == QDialog.Accepted:
            val= popup.get_values()

            CFG['files.is_max_hash_size'] = val['max_hash'][0]
            CFG['files.max_hash_size'] = val['max_hash'][1]
            CFG['files.is_min_size'] = val['min_size'][0]
            CFG['files.min_size'] = val['min_size'][1]
            CFG['files.is_max_size'] = val['max_size'][0]
            CFG['files.max_size'] = val['max_size'][1]

    def set_language(self, lang):
        if CFG["interface.lang"] == lang.data():
            return

        CFG["interface.lang"] = lang.data()

        self.menubar.show_message_box()

    def set_interface_mode(self, mode):
        if CFG["interface.mode"] == mode.data():
            return

        CFG["interface.mode"] = mode.data()
        msg = ""
        if mode.data() == GUI_SIMPLIFIED:
            msg = "\n".join((
                _(
                    "Attention, les paramètres de la section 'options' seront conservés"
                ),
                _("mais ne seront plus modifiables en mode 'simplifié'"),
            ))
        self.menubar.show_message_box(msg)

    def set_interface_size(self, size):
        print('SIZE TRIGGERED')
        # selected_action = self.size_group.checkedAction()
        if CFG["interface.size"] == size.data():
            return

        CFG["interface.size"] = size.data()
        self.menubar.show_message_box()

class MainTab(QWidget):
    def __init__(self, parent):
        super().__init__()

        self.parent = parent
        self.Wdgs = {}

        main_layout = QVBoxLayout()

        ########## Scan ##########
        scanFrame = CollapsibleFrame(_("Scan"), color="darkGreen")
        layout = QVBoxLayout()

        scanFrame.srcdirWdg = LabelNLineEdit(self, **MTW["dir"])
        layout.addLayout(scanFrame.srcdirWdg)
        scanFrame.destdirWdg = LabelNLineEdit(self, **MTW["dir"])
        layout.addLayout(scanFrame.destdirWdg)
        sub_layout = QHBoxLayout()
        #scanFrame.is_metaBtn = simpleCheckBox(sub_layout, **MTB["is_meta"])
        #scanFrame.is_md5_file = simpleCheckBox(sub_layout, **MTB["is_md5_file"])
        #scanFrame.is_md5_data = simpleCheckBox(sub_layout, **MTB["is_md5_data"])
        scanFrame.is_use_cache = simpleCheckBox(sub_layout, **MTB["is_use_cached_datas"])
        layout.addLayout(sub_layout)

        scanFrame.setLayout(layout)
        scanFrame.collapse(True)
        main_layout.addWidget(scanFrame)

        self.runBtn = simplePushButton(main_layout, **ACTION_BUTTONS["populate"])
        self.stopBtn = simpleStopButton(main_layout, self.stop)

        scanFrame.progbar_layout = QVBoxLayout()
        main_layout.addLayout(scanFrame.progbar_layout)

        # Disable "coming soon"
        scanFrame.srcdirWdg.textBox.setReadOnly(True)
        scanFrame.destdirWdg.textBox.setReadOnly(True)
        #scanFrame.dirWdg.btn_selector.setDisabled(True)
        #scanFrame.dirWdg.recursiveBtn.setDisabled(True)
        #scanFrame.is_metaBtn.setDisabled(True)
        #scanFrame.is_md5_file.setDisabled(True)
        #scanFrame.is_md5_data.setDisabled(True)

        self.scanFrame = scanFrame

        ########## Source ##########
        srcFrame = CollapsibleFrame(_("Source"))
        layout = QVBoxLayout()

        srcFrame.dirWdg = LabelNLineEdit(self, **MTW["in_dir"])
        srcFrame.dirWdg.recursiveBtn = simpleCheckBox(
            srcFrame.dirWdg, **MTB["is_recursive"]
        )
        srcFrame.extWdg = LabelNLineEdit(self, **MTW["extentions"])
        srcFrame.camWdg = LabelNLineEdit(self, **MTW["cameras"])
        srcFrame.excludeWdg = LabelNLineEdit(self, **MTW["excluded_dirs"])
        srcFrame.excludeWdg.is_regex = simpleCheckBox(
            srcFrame.excludeWdg, **MTB["is_exclude_dir_regex"]
        )

        layout.addLayout(srcFrame.dirWdg)
        layout.addLayout(srcFrame.extWdg)
        if not CFG["interface.mode"] == GUI_SIMPLIFIED:
            layout.addLayout(srcFrame.camWdg)
            layout.addLayout(srcFrame.excludeWdg)
        srcFrame.setLayout(layout)
        main_layout.addWidget(srcFrame)

        self.srcFrame = srcFrame

        ########## Destination ##########
        destFrame = CollapsibleFrame(_("Destination"), color="blue")
        layout = QVBoxLayout()

        destFrame.dirWdg = LabelNLineEdit(self, **MTW["out_dir"])
        destFrame.rel_dirWdg = LabelNLineEdit(self, **MTW["out_path_str"])
        destFrame.filenameWdg = LabelNLineEdit(self, **MTW["filename"])

        layout.addLayout(destFrame.dirWdg)
        layout.addLayout(destFrame.rel_dirWdg)
        layout.addLayout(destFrame.filenameWdg)

        destFrame.setLayout(layout)
        main_layout.addWidget(destFrame)

        self.destFrame = destFrame

        ########## Duplicates ##########
        dupFrame = CollapsibleFrame(_("Dupliqués"), color="blue")
        layout = QVBoxLayout()
        dupFrame.dupBtns = DuplicateWdg(self)
        layout.addLayout(dupFrame.dupBtns)
        dupFrame.setLayout(layout)
        main_layout.addWidget(dupFrame)

        self.dupFrame = dupFrame

        ########## Options ##########
        optFrame = CollapsibleFrame(_("Options"), color="blue")

        layout = QVBoxLayout()
        sub_layout = QHBoxLayout()

        optFrame.guess_date_from_name = LabelNLineEdit(
            self, **MTW["guess_date_from_name"]
        )
        optFrame.group_by_floating_days = LabelNLineEdit(
            self, **MTW["group_by_floating_days"]
        )

        layout.addLayout(optFrame.guess_date_from_name)
        layout.addLayout(optFrame.group_by_floating_days)

        sub_layout = QHBoxLayout()
        optFrame.gps = simpleCheckBox(sub_layout, **MTB["gps"])

        optFrame.is_delete_metadatas = simpleCheckBox(
            sub_layout, **MTB["is_delete_metadatas"]
        )
        optFrame.is_date_from_filesystem = simpleCheckBox(
            sub_layout, **MTB["is_date_from_filesystem"]
        )

        layout.addLayout(sub_layout)

        optFrame.setLayout(layout)
        optFrame.collapse()
        main_layout.addWidget(optFrame)

        self.optFrame = optFrame

        self.previewBtn = simplePushButton(main_layout, **ACTION_BUTTONS["calculate"])
        self.stopBtn1 = simpleStopButton(main_layout, self.stop)

        if CFG["interface.mode"] == GUI_SIMPLIFIED:
            self.optFrame.setHidden(True)

        self.compute_act_prog_holder = QVBoxLayout()
        main_layout.addLayout(self.compute_act_prog_holder)

        ########## Save & Run ##########
        execFrame = CollapsibleFrame("Executer", color="red")
        layout = QVBoxLayout()
        execFrame.file_actionWdg = fileActionWdg(self)
        layout.addLayout(execFrame.file_actionWdg)
        execFrame.setLayout(layout)
        main_layout.addWidget(execFrame)

        self.execFrame = execFrame

        self.executeBtn = simplePushButton(main_layout, **ACTION_BUTTONS["execute"])
        self.stopBtn2 = simpleStopButton(main_layout, self.stop)

        self.execute_act_prog_holder = QVBoxLayout()
        main_layout.addLayout(self.execute_act_prog_holder)

        # Progress bar
        self.progress_bar = MyProgressBar()
        self.progress_bar_label = self.progress_bar.add_label()

        # Counters
        # self.couterWdg = CounterWdg()

        fake_layout = QVBoxLayout()
        fake_layout.addWidget(self.progress_bar_label)
        fake_layout.addWidget(self.progress_bar)
        self.prev_progbar_layout = fake_layout

        main_layout.addStretch()

        size = self.sizeHint()
        self.setMinimumHeight(size.height())

        self.setLayout(main_layout)

    def move_progbar(self, new_layout):
        self.prev_progbar_layout.removeWidget(self.progress_bar)
        self.prev_progbar_layout.removeWidget(self.progress_bar_label)

        self.progress_bar.setParent(new_layout.parentWidget())
        self.progress_bar_label.setParent(new_layout.parentWidget())

        new_layout.addWidget(self.progress_bar_label)
        new_layout.addWidget(self.progress_bar)

        new_layout.update()
        self.prev_progbar_layout.update()

        self.prev_progbar_layout = new_layout


    def run_function(self, func, *args, **kwargs):
        if not LoopCallBack.stopped:
            func(*args, **kwargs)
        if LoopCallBack.stopped:
            self.timer.stop()
            self.runBtn.setHidden(False)
            self.executeBtn.setHidden(False)
            self.previewBtn.setHidden(False)
            self.stopBtn.setHidden(True)
            self.stopBtn1.setHidden(True)
            self.stopBtn2.setHidden(True)
            self.progress_bar.setValue(100)

    def stop(self):
        self.timer.stop()
        LoopCallBack.stopped = True
        self.runBtn.setHidden(False)
        self.executeBtn.setHidden(False)
        self.previewBtn.setHidden(False)
        self.stopBtn.setHidden(True)
        self.stopBtn1.setHidden(True)
        self.stopBtn2.setHidden(True)
        self.progress_bar.setValue(100)


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

        if isinstance(label, tuple):
            self.add_labelbox(label)
        else:
            labelWdg = QLabel(label)
            self.addWidget(labelWdg)
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
        self.addWidget(combo)
        self.combo = combo

        if CFG["interface.mode"] == GUI_SIMPLIFIED:
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
            for k, v in MEDIA_FORMATS.items():
                text = re.sub(k, v, text)
            for k, v in REL_PATH_FORMATS.items():
                text = re.sub(k, v, text)
            self.textBox.setText(text)
            self.combo.clearFocus()  # prevent combo to capture all signals

        combo.activated.connect(callback)

        # Set default values (need to load values from textBox intead of config at MainTab.__init__)
        if CFG["interface.mode"] == GUI_SIMPLIFIED:
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

        self.duplicateBtn = simpleCheckBox(
            self, **DUP_RADIO_BUTTONS["duplicate"]
        )  # QCheckBox('Dupliqués : ')

        self.dup_grp = QButtonGroup(parent)
        mode_Btns = {}
        mode_Btns[DUP_MD5_FILE] = MyRadioButton(
            parent, **DUP_RADIO_BUTTONS["file"]
        )  # QRadioButton(_('Fichier'), parent)
        mode_Btns[DUP_MD5_DATA] = MyRadioButton(
            parent, **DUP_RADIO_BUTTONS["data"]
        )  # QRadioButton(_('Données'), parent)
        mode_Btns[DUP_DATETIME] = MyRadioButton(
            parent, **DUP_RADIO_BUTTONS["date"]
        )  # QRadioButton(_('Date'), parent)

        self.dup_grp.addButton(mode_Btns[DUP_MD5_FILE], DUP_MD5_FILE)
        self.dup_grp.addButton(mode_Btns[DUP_MD5_DATA], DUP_MD5_DATA)
        self.dup_grp.addButton(mode_Btns[DUP_DATETIME], DUP_DATETIME)

        self.addWidget(mode_Btns[DUP_MD5_FILE])
        self.addWidget(mode_Btns[DUP_MD5_DATA])
        self.addWidget(mode_Btns[DUP_DATETIME])
        self.scandestBtn = simpleCheckBox(self, **MTB["is_scan_dest"])

    def set_dup_toggle(self, val):
        # CFG['is_control_duplicates'] = val
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
        # frame.setLayout(layout)
        main_layout.addLayout(layout)
        self.setLayout(main_layout)
        self.collapse(True)

    def run_act(self):
        logging.info("Starting processing files...")

        ordonate_photos.add_tags_to_folder(
            self.progress_bar, self.label_gps_info, self.label_image
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
        text = "<" + item.text().split("\t")[0].strip() + ">"
        QApplication.clipboard().setText(text)


class ComboBox(QComboBox):
    def __init__(self, callback):
        super().__init__()

        def combo_changed():
            callback(self.currentText())

        model = self.model()

        # Add items to the QComboBox and set the foreground color
        options = (_("toutes"), _("en commun"), _("utiles"))
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
        super().__init__(_("Extensions"), color="blue")
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
        exts = list_available_exts(
            CFG["source.dir"], recursive=CFG["source.is_recursive"]
        )
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
        super().__init__(_("Appareil"), color="blue")
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
        cameras = list_available_camera_model(
            CFG["source.dir"],
            CFG["source.extentions"],
            recursive=CFG["source.is_recursive"],
        )
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
        super().__init__(_("Métadonnées"), color="blue")
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
            CFG["source.dir"],
            CFG["source.extentions"],
            recursive=CFG["source.is_recursive"],
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
            CFG["source.dir"],
            CFG["source.extentions"],
            recursive=CFG["source.is_recursive"],
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
        n = n if n else 1  # prevent no files founded
        self._progbar_nb_val = n

    def update(self, v, text="", text2=""):
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
