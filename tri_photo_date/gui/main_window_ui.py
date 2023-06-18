#!/usr/bin/env python1

from configparser import ConfigParser
import sys, os
from pathlib import Path
import logging
import re

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
from tri_photo_date.gui import menu as windowmenu
from tri_photo_date.gui.sqlite_view import DatabaseViewer

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
from tri_photo_date.utils.config_paths import (
    STRFTIME_HELP_PATH,
    ICON_PATH,
    LOCALES_DIR,
    IMAGE_DATABASE_PATH,
)

# Texts
from tri_photo_date.gui.human_text import MAIN_TAB_WIDGETS as MTW
from tri_photo_date.gui.human_text import MAIN_TAB_BUTTONS as MTB


def set_global_config(lang='en', size=1, mode=GUI_ADVANCED):

    windowmenu.set_global_config(lang, size, mode)

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

        self.setWindowTitle("Tri photo")
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
        conf_panel_content = QWidget()
        conf_panel_content.setLayout(QVBoxLayout())
        conf_panel_content.layout().addWidget(self.conf_panel)
        scroll_area.setWidget(conf_panel_content)

        if GUI_MODE == GUI_SIMPLIFIED:
            splitter.addWidget(self.conf_panel)
            tabs.setHidden(True)

        elif GUI_MODE == GUI_ADVANCED:
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

        scan_frame.srcdir_wdg = LabelNLineEdit(self, **MTW["dir"])
        layout.addLayout(scan_frame.srcdir_wdg)
        scan_frame.destdir_wdg = LabelNLineEdit(self, **MTW["dir"])
        layout.addLayout(scan_frame.destdir_wdg)
        sub_layout = QHBoxLayout()
        # scan_frame.is_metaBtn = simpleCheckBox(sub_layout, **MTB["is_meta"])
        # scan_frame.is_md5_file = simpleCheckBox(sub_layout, **MTB["is_md5_file"])
        # scan_frame.is_md5_data = simpleCheckBox(sub_layout, **MTB["is_md5_data"])
        scan_frame.is_use_cache = simpleCheckBox(
            sub_layout, **MTB["is_use_cached_datas"]
        )
        layout.addLayout(sub_layout)

        scan_frame.setLayout(layout)
        scan_frame.collapse(True)
        main_layout.addWidget(scan_frame)

        self.populateBtn = simplePushButton(main_layout, **ACTION_BUTTONS["populate"])
        self.populateBtn.clicked.connect(self.populate_event)
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

        ########## Source ##########
        src_frame = CollapsibleFrame(_("Source"))
        layout = QVBoxLayout()

        src_frame.dir_wdg = LabelNLineEdit(self, **MTW["in_dir"])
        src_frame.dir_wdg.recursiveBtn = simpleCheckBox(
            src_frame.dir_wdg, **MTB["is_recursive"]
        )
        src_frame.ext_wdg = LabelNLineEdit(self, **MTW["extentions"])
        src_frame.cam_wdg = LabelNLineEdit(self, **MTW["cameras"])
        src_frame.exclude_wdg = LabelNLineEdit(self, **MTW["excluded_dirs"])
        src_frame.exclude_wdg.is_regex = simpleCheckBox(
            src_frame.exclude_wdg, **MTB["is_exclude_dir_regex"]
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

        dest_frame.dir_wdg = LabelNLineEdit(self, **MTW["out_dir"])
        dest_frame.rel_dir_wdg = LabelNLineEdit(self, **MTW["out_path_str"])
        dest_frame.filename_wdg = LabelNLineEdit(self, **MTW["filename"])

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
        dup_frame.setLayout(layout)
        main_layout.addWidget(dup_frame)

        self.dup_frame = dup_frame

        ########## Options ##########
        opt_frame = CollapsibleFrame(_("Options"), color="blue")

        layout = QVBoxLayout()
        sub_layout = QHBoxLayout()

        opt_frame.guess_date_from_name = LabelNLineEdit(
            self, **MTW["guess_date_from_name"]
        )
        opt_frame.group_by_floating_days = LabelNLineEdit(
            self, **MTW["group_by_floating_days"]
        )

        layout.addLayout(opt_frame.guess_date_from_name)
        layout.addLayout(opt_frame.group_by_floating_days)

        sub_layout = QHBoxLayout()
        opt_frame.gps = simpleCheckBox(sub_layout, **MTB["gps"])
        layout.addLayout(sub_layout)

        sub_layout = QHBoxLayout()

        opt_frame.is_delete_metadatas = simpleCheckBox(
            sub_layout, **MTB["is_delete_metadatas"]
        )
        layout.addLayout(sub_layout)

        sub_layout = QHBoxLayout()
        opt_frame.is_date_from_filesystem = simpleCheckBox(
            sub_layout, **MTB["is_date_from_filesystem"]
        )
        opt_frame.is_force_date_from_filesystem = simpleCheckBox(
            sub_layout, **MTB["is_force_date_from_filesystem"]
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

        self.previewBtn = simplePushButton(main_layout, **ACTION_BUTTONS["calculate"])
        self.previewBtn.clicked.connect(self.preview_event)
        self.stopBtn1 = simpleStopButton(main_layout, self.stop)

        if GUI_MODE == GUI_SIMPLIFIED:
            self.opt_frame.setHidden(True)

        self.compute_act_prog_holder = QVBoxLayout()
        main_layout.addLayout(self.compute_act_prog_holder)

        ########## Save & Run ##########
        exec_frame = CollapsibleFrame("Executer", color="red")
        layout = QVBoxLayout()
        exec_frame.file_action_wdg = fileActionWdg(self)
        layout.addLayout(exec_frame.file_action_wdg)
        exec_frame.setLayout(layout)
        main_layout.addWidget(exec_frame)

        self.exec_frame = exec_frame

        self.executeBtn = simplePushButton(main_layout, **ACTION_BUTTONS["execute"])
        self.executeBtn.clicked.connect(self.execute_event)
        self.stopBtn2 = simpleStopButton(main_layout, self.stop)

        self.execute_act_prog_holder = QVBoxLayout()
        main_layout.addLayout(self.execute_act_prog_holder)

        # Progress bar
        self.progress_bar = MyProgressBar()
        self.progress_bar_label = self.progress_bar.add_label()

        # Counters
        # self.couter_wdg = CounterWdg()

        fake_layout = QVBoxLayout()
        fake_layout.addWidget(self.progress_bar_label)
        fake_layout.addWidget(self.progress_bar)
        self.prev_progbar_layout = fake_layout

        main_layout.addStretch()

        # size = self.sizeHint()
        # self.setMinimumHeight(size.height())

        self.setLayout(main_layout)

    def populate_event(self):
        logging.info("Starting processing files...")

        self.move_progbar(self.scan_frame.progbar_layout)

        self.populateBtn.setHidden(True)
        self.stopBtn.setHidden(False)

    def preview_event(self):
        logging.info("Starting processing files...")

        self.move_progbar(self.compute_act_prog_holder)

        self.previewBtn.setHidden(True)
        self.stopBtn1.setHidden(False)

    def execute_event(self):
        logging.info("Starting processing files...")

        self.move_progbar(self.execute_act_prog_holder)

        self.executeBtn.setHidden(True)
        self.stopBtn2.setHidden(False)

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
            self.populateBtn.setHidden(False)
            self.executeBtn.setHidden(False)
            self.previewBtn.setHidden(False)
            self.stopBtn.setHidden(True)
            self.stopBtn1.setHidden(True)
            self.stopBtn2.setHidden(True)
            self.progress_bar.setValue(100)

    def stop(self):
        self.timer.stop()
        LoopCallBack.stopped = True
        self.populateBtn.setHidden(False)
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
        self.addWidget(combo)
        self.combo = combo

        if GUI_MODE == GUI_SIMPLIFIED:
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
        if GUI_MODE == GUI_SIMPLIFIED:
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

        self.duplicateBtn.stateChanged.connect(self.set_dup_toggle)

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

        strftime_help = open(STRFTIME_HELP_PATH).read()
        text_widget = QTextEdit()
        text_widget.setHtml(strftime_help)
        self.layout.addWidget(text_widget)

    def link_clicked(self, url):
        QDesktopServices.openUrl(url)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
