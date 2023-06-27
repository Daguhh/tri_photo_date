from collections import deque
import pyqtgraph as pg
import time

class SpeedProgressBar(pg.PlotWidget):
    """A ProgressBar that show both progress and speed:
        - abscissa : progress [unit], with unit, the unit of data given by user
        - ordonnate : speed [unit/time]
    """

    def __init__(self, parent=None, nb_sections=500, smooth_window=4):
        """Initialize the plot : Hide axis, prevent mouse interactions
        initialize values

        Parameters
        ----------
        nb_sections : int
            Number of vertical bar in the graph
        smooth_window : int
            Use average of last speed bars value to smooth datas (prettier?)
        """

        super().__init__(parent, background='w')

        # Number of bar in the graph
        self.nb_sections = nb_sections

        # Hide axis
        self.plotItem.showAxes(False)
        self.plotItem.showGrid(False)

        # Store last speed values to smooth_window the graph
        self.speeds = deque([0], maxlen=smooth_window)

        # Disable mouse interactions
        self.setMouseEnabled(False)
        self.plotItem.setMenuEnabled(False)
        self.plotItem.setMouseEnabled(False)
        self.wheelEvent = lambda *args, **kwargs: None
        self.mouseDragEvent = lambda *args, **kwargs: None
        self.mousePressEvent = lambda *args, **kwargs: None
        self.mouseReleaseEvent = lambda *args, **kwargs: None

        # Store the graph object
        self.bargraph = None

    def init(self, max_value):
        """Initialise a bar graph at zero for each x

        Parameters
        ----------
        max_value : int, float
            value at which progressbar reach 100%, could be number of items, sum of files size to process...
            Set to 100 to work in percentage
        """

        if max_value == 0: # no bar
            return

        self.bar_width = max_value / self.nb_sections # "width" of bar
        self.bar_index = -1 # count bar index
        self._bar_previous_index = -1 # hold previous bar index

        # remove last bar and clean plot
        del(self.bargraph)
        self.clear()

        # Init bar at 0
        x = range(self.nb_sections)
        y = [0 for _ in x]
        self.bargraph = pg.BarGraphItem(x = x, height = y, width = 1, brush ='c', pen=pg.mkPen(None))
        self.addItem(self.bargraph)

        # start a timer to update the plot
        self.timer = pg.QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(100)  # 50ms

        # Start to mesure time
        self.tic = time.time_ns() - 6*1000*1000*1000 # remove 1 sec # init in s #time.time()

        # Store bargraph values
        self.new_ys = self.bargraph.opts['height']

    def update_plot(self):
        """Update bar graph given new Y values when called by timer"""

        self.bargraph.setOpts(**{'heigth':self.new_ys})

    def update(self, progress_value):
        """update bar Y values

        Parameters
        ----------
        progress_value : int, float
            progress_value / max_value = percentage
        """

        # Create a new bar on graph
        bar_index = int(progress_value // self.bar_width)

        # Pass the 100%
        if bar_index >= self.nb_sections:
            bar_index = self.nb_sections - 1

        # while bar is not complete skip
        elif bar_index == self._bar_previous_index:
            return

        # get last elapsed time
        toc = time.time_ns() - self.tic + 1000 # add 1 micro second (if loop time is under computer precision)
        self.tic = time.time_ns()

        # (let's say we loop over 1 Go (max_value) of files, and all are 1Ko
        # except 1 that is 500Mo (progress_value),
        # the last will progress of multiples row (nb_bars) in one time)
        nb_bars = bar_index -self._bar_previous_index

        # compute speed
        new_speed = nb_bars * self.bar_width / toc # speed of bar

        # if new progress_value is larger than bar width
        ys = self.bargraph.opts['height']
        for index in range(self._bar_previous_index + 1, bar_index + 1):

            self.speeds.append(new_speed)

            # Set mean speed at bar_index
            ys[index] = sum(self.speeds) / len(self.speeds)

        self.new_ys = ys

        self.speeds.append(new_speed)
        self._bar_previous_index = bar_index


