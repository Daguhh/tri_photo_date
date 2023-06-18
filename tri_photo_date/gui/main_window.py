#!/usr/bin/env python1

import logging

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QLineEdit,
    QCheckBox,
    QAction,
    QActionGroup,
    QDialog,
    QAction,
    QComboBox,
    QButtonGroup,
    QSpinBox,
)

# Modules
from tri_photo_date import ordonate_photos
from tri_photo_date.ordonate_photos import CFG

# database explorer functions
from tri_photo_date.explore_db import (
    list_available_camera_model,
    list_available_exts,
    list_available_tags,
)

# Load and init ui
from  tri_photo_date.gui import main_window_ui
main_window_ui.set_global_config(
    CFG['interface.lang'],
    CFG['interface.size'],
    CFG['interface.mode']
)
from tri_photo_date.gui.main_window_ui import MainWindow_ui, LoopCallBack

from tri_photo_date.gui.menu import SettingFilePopup


class MainWindow(MainWindow_ui):
    def __init__(self):
        super().__init__()

        self.create_widget_dct()

        self.setup_interconnections()
        self.setup_actions()

        self.connect_wdgs_2_config()

        self.load_conf()

    def create_widget_dct(self):
        wdgs = {}
        wdgs["scan.src_dir"] = self.conf_panel.scan_frame.srcdir_wdg.textBox
        wdgs["scan.dest_dir"] = self.conf_panel.scan_frame.destdir_wdg.textBox
        # wdgs['("scan.'] = self.conf_panel.scan_wdg.is_metaBtn.stateChanged
        # wdgs['("scan.'] = self.conf_panel.scan_frame.is_md5_data.stateChanged
        # wdgs['("scan.'] = self.conf_panel.scan_frame.is_md5_file.stateChanged
        wdgs["scan.is_use_cached_datas"] = self.conf_panel.scan_frame.is_use_cache
        # wdgs['("scan.'] = self.conf_panel.scan_frame.dir_wdg.recursiveBtn.stateChanged

        wdgs["source.dir"] = self.conf_panel.src_frame.dir_wdg.textBox
        wdgs["source.extentions"] = self.conf_panel.src_frame.ext_wdg.textBox
        wdgs["source.cameras"] = self.conf_panel.src_frame.cam_wdg.textBox
        wdgs["source.is_recursive"] = self.conf_panel.src_frame.dir_wdg.recursiveBtn
        wdgs["source.excluded_dirs"] = self.conf_panel.src_frame.exclude_wdg.textBox
        wdgs["source.exclude_toggle"] = self.conf_panel.src_frame.exclude_wdg.labelbox
        wdgs[
            "source.is_exclude_dir_regex"
        ] = self.conf_panel.src_frame.exclude_wdg.is_regex

        wdgs["destination.dir"] = self.conf_panel.dest_frame.dir_wdg.textBox
        wdgs["destination.rel_dir"] = self.conf_panel.dest_frame.rel_dir_wdg.textBox
        wdgs["destination.filename"] = self.conf_panel.dest_frame.filename_wdg.textBox

        wdgs["duplicates.is_control"] = self.conf_panel.dup_frame.dupBtns.duplicateBtn
        wdgs["duplicates.mode"] = self.conf_panel.dup_frame.dupBtns.dup_grp
        wdgs["duplicates.is_scan_dest"] = self.conf_panel.dup_frame.dupBtns.scandestBtn

        wdgs[
            "options.name.guess_fmt"
        ] = self.conf_panel.opt_frame.guess_date_from_name.textBox
        wdgs[
            "options.name.is_guess"
        ] = self.conf_panel.opt_frame.guess_date_from_name.checkBox
        wdgs[
            "options.group.is_group"
        ] = self.conf_panel.opt_frame.group_by_floating_days.checkBox
        wdgs[
            "options.group.display_fmt"
        ] = self.conf_panel.opt_frame.group_by_floating_days.textBox
        wdgs[
            "options.group.floating_nb"
        ] = self.conf_panel.opt_frame.group_by_floating_days.spinBox
        wdgs["options.gps.is_gps"] = self.conf_panel.opt_frame.gps
        wdgs[
            "options.general.is_delete_metadatas"
        ] = self.conf_panel.opt_frame.is_delete_metadatas
        wdgs[
            "options.general.is_date_from_filesystem"
        ] = self.conf_panel.opt_frame.is_date_from_filesystem
        wdgs[
            "options.general.is_force_date_from_filesystem"
        ] = self.conf_panel.opt_frame.is_force_date_from_filesystem

        wdgs[
            "action.action_mode"
        ] = self.conf_panel.exec_frame.file_action_wdg.btn_group

        wdgs["interface.mode"] = self.menubar.mode_group
        wdgs["interface.lang"] = self.menubar.lang_group
        wdgs["interface.size"] = self.menubar.size_group

        self.wdgs = wdgs

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

    def setup_actions(self):
        self.conf_panel.populateBtn.clicked.connect(self.act_populate)
        self.conf_panel.previewBtn.clicked.connect(self.act_preview)
        self.conf_panel.executeBtn.clicked.connect(self.act_execute)

        self.tool_panel.gps.runBtn.clicked.connect(self.act_run_gps)

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
                pass  # link manually to specific action
            elif isinstance(wdg, QActionGroup):
                wdg.triggered.connect(lambda s, prop=prop: callback(s.data(), prop))

        # self.menubar.load_action.triggered.connect(self.load)
        # self.menubar.save_action.triggered.connect(self.save)
        self.menubar.config_action.triggered.connect(self.menubar.open_file_browser)
        self.menubar.set_settings_action.triggered.connect(self.show_set_settings)
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

    # def update_cameras(self):
    #    txt = self.tool_panel.cam.user_choice_cameras
    #    self.conf_panel.src_frame.cam_wdg.textBox.setText(txt)

    # def update_extensions(self):
    #    txt = self.tool_panel.exts.user_choice_extentions
    #    self.conf_panel.src_frame.ext_wdg.textBox.setText(txt)

    def update_preview(self):
        timer = QTimer()

        if not timer.isActive():
            filter_text = self.preview_wdg.filter_edit.text()
            self.preview_wdg.update_table(filter_text)

    def update_selection_tabs(self):
        self.set_ext_list()
        self.set_tag_list()
        self.set_camera_list()

    def set_camera_list(self):
        cameras = list_available_camera_model(
            CFG["source.dir"],
            CFG["source.extentions"],
            recursive=CFG["source.is_recursive"],
        )
        self.tool_panel.cam.set_camera_list(cameras)

    def set_tag_list(self):
        tags_list = list_available_tags(
            CFG["source.dir"],
            CFG["source.extentions"],
            recursive=CFG["source.is_recursive"],
        )
        self.tool_panel.meta.set_tag_list(tags_list)

    def set_ext_list(self):
        exts = list_available_exts(
            CFG["source.dir"], recursive=CFG["source.is_recursive"]
        )
        self.tool_panel.exts.set_ext_list(exts)

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

    def act_populate(self):
        logging.info("Starting processing files...")

        self.conf_panel.move_progbar(self.conf_panel.scan_frame.progbar_layout)

        self.save_act()
        self.conf_panel.populateBtn.setHidden(True)
        self.conf_panel.stopBtn.setHidden(False)

        LoopCallBack.stopped = False
        self.conf_panel.timer = QTimer()

        self.conf_panel.timer.timeout.connect(
            lambda: self.conf_panel.run_function(
                ordonate_photos.populate_db, self.conf_panel.progress_bar, LoopCallBack
            )
        )
        self.conf_panel.timer.timeout.connect(self.update_selection_tabs)
        self.conf_panel.timer.start(1000)  # waits for 1 second

    def act_preview(self):
        logging.info("Starting processing files...")

        self.conf_panel.move_progbar(self.conf_panel.compute_act_prog_holder)

        self.save_act()
        self.conf_panel.previewBtn.setHidden(True)
        self.conf_panel.stopBtn1.setHidden(False)

        LoopCallBack.stopped = False
        self.conf_panel.timer = QTimer()
        self.conf_panel.timer.timeout.connect(
            lambda: self.conf_panel.run_function(
                ordonate_photos.compute, self.conf_panel.progress_bar, LoopCallBack
            )
        )
        self.conf_panel.timer.timeout.connect(self.update_preview)
        self.conf_panel.timer.start(1000)  # waits for 1 second

    def act_execute(self):
        logging.info("Starting processing files...")

        self.conf_panel.move_progbar(self.conf_panel.act_execute_prog_holder)

        self.save_act()
        self.conf_panel.executeBtn.setHidden(True)
        self.conf_panel.stopBtn2.setHidden(False)

        LoopCallBack.stopped = False
        self.conf_panel.timer = QTimer()
        self.conf_panel.timer.timeout.connect(
            lambda: self.conf_panel.run_function(
                ordonate_photos.execute, self.conf_panel.progress_bar, LoopCallBack
            )
        )
        self.conf_panel.timer.start(1000)  # waits for 1 second

    def save_act(self):
        logging.info(f"Saving config to {CFG.configfile} ...")
        # self.get_config()
        CFG.save_config()

    def show_set_settings(self):
        popup = SettingFilePopup()

        wdgs = {}
        wdgs["files.is_max_hash_size"] = popup.ckb_max_hash
        wdgs["files.max_hash_size"] = popup.spin_max_hash
        wdgs["files.is_min_size"] = popup.ckb_min_size
        wdgs["files.min_size"] = popup.spin_min_size
        wdgs["files.is_max_size"] = popup.ckb_max_size
        wdgs["files.max_size"] = popup.spin_max_size

        self.wdgs_settings = wdgs
        self.load_settings_conf()

        res = popup.exec_()
        if res == QDialog.Accepted:
            val = popup.get_values()

            CFG["files.is_max_hash_size"] = val["max_hash"][0]
            CFG["files.max_hash_size"] = val["max_hash"][1]
            CFG["files.is_min_size"] = val["min_size"][0]
            CFG["files.min_size"] = val["min_size"][1]
            CFG["files.is_max_size"] = val["max_size"][0]
            CFG["files.max_size"] = val["max_size"][1]

    def act_run_gps(self):
        logging.info("Starting processing files...")

        ordonate_photos.add_tags_to_folder(
            self.progress_bar, self.label_gps_info, self.label_image
        )
        self.progress_bar.setValue(100)

