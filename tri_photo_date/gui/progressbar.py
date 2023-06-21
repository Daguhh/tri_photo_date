
import time

from PyQt5.QtWidgets import QVBoxLayout, QLabel, QApplication, QProgressBar

PROG_SPEED_BAR = 0
PROG_NORMAL = 1

try:
    import pyqtgraph as pg
    progress_bar_mode = PROG_SPEED_BAR
except ModuleNotFoundError:
    progress_bar_mode = PROG_NORMAL

if progress_bar_mode == PROG_SPEED_BAR:

    class MyProgressBar(pg.PlotWidget):

        def __init__(self, parent=None):

            super().__init__(parent, background='w')

            self.parent = parent

            self.label = self.add_label()

            fake_layout = QVBoxLayout()
            fake_layout.addWidget(self.label)
            fake_layout.addWidget(self)
            self.prev_layout = fake_layout

            self.plotItem.showAxes(False)
            self.plotItem.showGrid(False)

            self.bargraph = None

        def add_label(self):

            self.text_label = QLabel("")
            return self.text_label

        def init(self, n):

            n = n + 1

            self.chunk_nb = min(500, n) # max bar number
            self.chunk_width = n // self.chunk_nb # "width" of bar
            self.chunk_index = 0 # count bar index
            self.chunk_last_index = 0 # hold previous bar index

            del(self.bargraph)
            self.clear()

            x = range(n // self.chunk_width + 1)
            y = [0 for _ in x]

            self.bargraph = pg.BarGraphItem(x = x, height = y, width = 1, brush ='c')
            self.addItem(self.bargraph)

            # start a timer to update the plot
            self.timer = pg.QtCore.QTimer()
            self.timer.timeout.connect(self.update_plot)
            self.timer.start(100)  # 50ms

            self.tic = time.time()

            self.new_ys = self.bargraph.opts['height']

        def update_plot(self):

            self.bargraph.setOpts(**{'heigth':self.new_ys})

        def update(self, x, text="", text2=""):

            self.text_label.setText(text)
            QApplication.processEvents()  # keep the GUI responsive

            # Create a new bar on graph
            self.chunk_index = x // self.chunk_width
            if self.chunk_index != self.chunk_last_index:
                self.chunk_last_index = self.chunk_index

                # get last elapsed time
                toc = time.time() - self.tic
                self.tic = time.time()

                # Set speed at chunk_index
                speed = (self.chunk_width) / toc # speed of chunk
                ys = self.bargraph.opts['height']
                ys[self.chunk_index] = speed
                self.new_ys = ys

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
            self.text_label.setText(text)

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



