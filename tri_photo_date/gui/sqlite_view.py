import sqlite3
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import (
    QWidget,
    QTableWidget,
    QHeaderView,
    QVBoxLayout,
    QLineEdit,
    QLabel,
    QApplication,
    QTableWidgetItem,
    QSizePolicy,
    QTabWidget,
)

from tri_photo_date.photo_database import ImageMetadataDB
from tri_photo_date.config.config_paths import IMAGE_DATABASE_PATH

from tri_photo_date.config.config_paths import LOCALES_DIR

def set_global_config(lang='en', size=1, mode=None):

    import gettext

    trad = gettext.translation("base", localedir=LOCALES_DIR, languages=[lang])
    trad.install()

    global _
    _ = trad.gettext  # Greek

class DatabaseViewer(QTabWidget):

    def __init__(self, db_file):
        super().__init__()
        self.db_file = db_file

        #self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        #self.setTabPosition(QTabWidget.West)

        self.scan_view = ScanTableViewer(db_file)
        self.preview_view = PreviewTableViewer(db_file)

        self.addTab(self.scan_view, _("Scan"))
        self.addTab(self.preview_view, _("Preview"))

        self.setTabToolTip(0, _("Liste des fichiers scannés"))
        self.setTabToolTip(1, _("Aperçu des modifications à effectuer"))

class TableViewer(QWidget):
    def __init__(self, db_file):
        super().__init__()
        self.db_file = db_file

        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText(
            _("Entrez une chaine de caractères pour filtrer")
        )
        self.filter_edit.textChanged.connect(self.update_table_act)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        # self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().sectionResized.connect(self.save_column_sizes)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        self.table.setSortingEnabled(True)

        layout = QVBoxLayout()
        layout.addWidget(self.filter_edit)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.update_table("")

    def update_table_act(self, e):
        self.update_table(self.filter_edit.text())


    def save_column_sizes(self, index, old_size, new_size):
        settings = QSettings("MyCompany", "MyApp")
        settings.setValue(f"column_size_{index}", new_size)

    def load_column_sizes(self):
        settings = QSettings("MyCompany", "MyApp")
        for i in range(self.table.columnCount()):
            size = settings.value(f"column_size_{i}", type=int, defaultValue=-1)
            if size != -1:
                self.table.setColumnWidth(i, size)

    def setHiddenCallback(self, callback):
        self.hidden_callback = callback

    # def hideEvent(self, event):
    #    self.hidden_callback()
    # super().hideEvent(event)
    # self.hidden.emit()

class PreviewTableViewer(TableViewer):
    def __init__(self, db_file):
        super().__init__(db_file)

        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            [
                _("Dossier"),
                _("Nom"),
                _("Nouveau dossier"),
                _("Nouveau nom"),
                _("Lieu"),
                _("Groupe"),
                _("Date"),
            ]
        )

    def update_table(
        self, filter_text=""
    ):  # , dir='', extentions=[], cameras=[], recursive=True, filter_text='', mode=False, from_compute='update_table'):
        # filter_text = self.filter_edit.text()
        # conn = sqlite3.connect(self.db_file)
        # cursor = conn.cursor()

        with ImageMetadataDB() as db:
            # files_to_process = db.list__preview_files()

            rows = list(db.get_preview(filter_text))  # files_to_process)

        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, col in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(col)))
        # conn.close()


class ScanTableViewer(TableViewer):
    def __init__(self, db_file):
        super().__init__(db_file)

        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(
            [
                _("Dossier"),
                _("Nom"),
                _("Appareil"),
            ]
        )

    def update_table(
        self, filter_text=""
    ):  # , dir='', extentions=[], cameras=[], recursive=True, filter_text='', mode=False, from_compute='update_table'):
        # filter_text = self.filter_edit.text()
        # conn = sqlite3.connect(self.db_file)
        # cursor = conn.cursor()

        with ImageMetadataDB() as db:
            # files_to_process = db.list__preview_files()

            rows = list(db.get_images_to_process(filter_text))  # files_to_process)

        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, col in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(col)))
        # conn.close()


if __name__ == "__main__":
    app = QApplication([])
    viewer = DatabaseViewer(str(IMAGE_DATABASE_PATH))
    viewer.show()
    app.exec_()
