
import time

from PyQt5.QtWidgets import QVBoxLayout, QLabel, QApplication, QProgressBar

from tri_photo_date.utils.small_tools import limited_string
from tri_photo_date.config.config_loader import CONFIG
IS_SPEEDBAR = CONFIG['interface']['is_speedbar']

PROG_SPEED_BAR = 0
PROG_NORMAL = 1

try:
    import pyqtgraph as pg
    from tri_photo_date.gui.speedprogressbar import SpeedProgressBar
    progress_bar_mode = PROG_SPEED_BAR
except ModuleNotFoundError:
    progress_bar_mode = PROG_NORMAL

if progress_bar_mode == PROG_SPEED_BAR and IS_SPEEDBAR:

    class MyProgressBar(SpeedProgressBar):

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

            self.label = self.add_label()

            fake_layout = QVBoxLayout()
            fake_layout.addWidget(self.label)
            fake_layout.addWidget(self)
            self.prev_layout = fake_layout

        def update(self, v, text="", text2=""):
            super().update(v)
            QApplication.processEvents()  # keep the GUI responsive
            self.text_label.setText(limited_string(text,limit=40) + '-' + text2)

        def add_label(self):

            self.text_label = QLabel("")
            return self.text_label

        def move_to_layout(self, new_layout):

            self.prev_layout.removeWidget(self)
            self.prev_layout.removeWidget(self.label)

            self.setParent(new_layout.parentWidget())
            self.label.setParent(new_layout.parentWidget())

            new_layout.addWidget(self.label)
            new_layout.addWidget(self)

            new_layout.update()
            self.prev_layout.update()

            self.prev_layout = new_layout

else:

    class MyProgressBar(QProgressBar):
        def __init__(self, *args, **kwargs):
            super().__init__()
            self.setGeometry(50, 50, 200, 20)
            self.setContentsMargins(0, 0, 0, 0)
            self._progbar_nb_val = 1

            self.label = self.add_label()

            fake_layout = QVBoxLayout()
            fake_layout.addWidget(self.label)
            fake_layout.addWidget(self)
            self.prev_layout = fake_layout

        def add_label(self):
            self.text_label = QLabel("")
            return self.text_label

        def init(self, n):
            n = n if n else 1  # prevent no files founded
            self._progbar_nb_val = n

        def update(self, v, text="", text2=""):
            self.setValue(int(100 * v / self._progbar_nb_val))
            QApplication.processEvents()  # keep the GUI responsive
            self.text_label.setText(' '.join((limited_string(text, limit=40), '-', text2)))

        def move_to_layout(self, new_layout):

            self.prev_layout.removeWidget(self)
            self.prev_layout.removeWidget(self.label)

            self.setParent(new_layout.parentWidget())
            self.label.setParent(new_layout.parentWidget())

            new_layout.addWidget(self.label)
            new_layout.addWidget(self)

            new_layout.update()
            self.prev_layout.update()

            self.prev_layout = new_layout



