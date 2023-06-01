import sqlite3
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QWidget, QTableWidget, QHeaderView, QVBoxLayout, QLineEdit, QLabel, QApplication, QTableWidgetItem

from tri_photo_date.photo_database import ImageMetadataDB
from tri_photo_date.utils.config_paths import IMAGE_DATABASE_PATH

class DatabaseViewer(QWidget):
    def __init__(self, db_file):
        super().__init__()
        self.db_file = db_file

        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText('Entrez une chaine de caractères pour filtrer')
        #self.filter_edit.textChanged.connect(self.update_table)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["folder", "name", "new folder", "new_filename", "location", "group", "date"])
        #self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().sectionResized.connect(self.save_column_sizes)

        layout = QVBoxLayout()
        layout.addWidget(self.filter_edit)
        layout.addWidget(self.table)
        self.setLayout(layout)

        self.update_table()

    def update_table(self, src_dir='', extentions=[], cameras=[], recursive=True, filter_text='', dup_mode=False):

        #filter_text = self.filter_edit.text()
        #conn = sqlite3.connect(self.db_file)
        #cursor = conn.cursor()

        with ImageMetadataDB() as db:
            files_to_process = db.list_files(src_dir, extentions, cameras, recursive, filter_text, dup_mode)

            rows = db.get_preview(files_to_process)

        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, col in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(col)))
        #conn.close()

    def save_column_sizes(self, index, old_size, new_size):
        settings = QSettings('MyCompany', 'MyApp')
        settings.setValue(f'column_size_{index}', new_size)

    def load_column_sizes(self):
        settings = QSettings('MyCompany', 'MyApp')
        for i in range(self.table.columnCount()):
            size = settings.value(f'column_size_{i}', type=int, defaultValue=-1)
            if size != -1:
                self.table.setColumnWidth(i, size)

    def setHiddenCallback(self, callback):
        self.hidden_callback = callback

    def hideEvent(self, event):
        self.hidden_callback()
        #super().hideEvent(event)
        #self.hidden.emit()

if __name__ == "__main__":

    app = QApplication([])
    viewer = DatabaseViewer(str(IMAGE_DATABASE_PATH))
    viewer.show()
    app.exec_()

