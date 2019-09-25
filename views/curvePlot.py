from PyQt5 import uic, QtCore
from PyQt5.QtWidgets import QVBoxLayout, QSizePolicy, QDialog, QMenuBar, QMenu
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as ticker
import numpy as np
import sqlite3
import model.main as model

DEPTH_SCALE = 98.0
TENSION_SCALE = 19.53125
CCL_FACTOR = 51.1
CCL_OFFSET = 0   # -511
Ui_CurvePlot, QtBaseClass = uic.loadUiType("./resources/curvePlot.ui")

class CurvePlot(QDialog, Ui_CurvePlot):
    def __init__(self, parent=None):
        super(CurvePlot, self).__init__(parent)
        Ui_CurvePlot.__init__(self)
        self.setupUi(self)
        self.session = model.Session()
        # DEBUG: print (self.__dict__) # To check widget attributes
        layout = QVBoxLayout(self.mainWidget)
        self.canvas = MyDynamicMplCanvas(
                            self.mainWidget,
                            width=11.50, height=6.80,
                            dpi=100, DB_PATH = self.session.active['DBpath'] ,
                            TABLE = self.session.active['pass'])
        layout.addWidget(self.canvas)
        self.mainWidget.setFocus()

        self.vScrollBar.valueChanged.connect(self.update_depth)

    def update_depth(self):
        self.canvas.DB_PATH = self.session.active['DBpath']
        self.canvas.TABLE = self.session.active['pass']
        self.canvas.iter = self.vScrollBar.value()
        self.canvas.update_figure()

    def wheelEvent(self, event):
        yWheelScroll = event.angleDelta().y() / (-120)
        newvScrollBarVal = self.vScrollBar.value() + yWheelScroll
        if newvScrollBarVal < 0:
            newvScrollBarVal = 0
        self.vScrollBar.setValue(newvScrollBarVal)


class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=4, height=5, dpi=100, DB_PATH="",
                 TABLE= ""):
        self.fig, self.axis = plt.subplots(
                                1, 2, # 1 row, 2 cols
                                gridspec_kw={'width_ratios':[1, 2]},
                                sharey=True,
                                figsize=(width, height)
                              )
        self.DB_PATH = DB_PATH
        self.TABLE = TABLE
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)


class MyDynamicMplCanvas(MyMplCanvas):
    """A canvas that updates itself every 300 msecs with a new plot."""

    def __init__(self, *args, **kwargs):
        MyMplCanvas.__init__(self, *args, **kwargs)
        self.iter = 0
        # TODO: Implement real time plotting, try with a session variable
        """
        # Use this for realtime plotting
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_figure)
        timer.start(100)
        """
    def update_figure(self):
        self.conn = sqlite3.connect(self.DB_PATH)
        self.cur = self.conn.cursor()
        result = self.cur.execute("SELECT * FROM {} where id_seq > {} and \
                                  id_seq < {}".format(self.TABLE,
                                                      self.iter*100,
                                                      (self.iter+1)*100)).fetchall()
        self.conn.close()
        """
        # Use something like this for realtime plotting
        result = cur.execute("SELECT * FROM acq_20190917_134352 \
                             order by id_seq desc limit 100"
                             .format(i*100, (i+1)*100)).fetchall()
        """
        y = np.array([var[1] for var in result]) / DEPTH_SCALE
        x1 = (np.array([var[2] for var in result]) + CCL_OFFSET) \
                / CCL_FACTOR
        x2 = np.array([var[3] for var in result]) * TENSION_SCALE

        [ax.clear() for ax in self.axis]
        self.load_subp_style()
        self.axis[0].plot(x1, y, label="CCL", linewidth=1.0)
        self.axis[1].plot(x2, y, label="Tension", linewidth=1.0)
        self.fig.gca().invert_yaxis() # To plot down
        self.fig.legend(ncol=2, loc='upper center',
                        mode="expand", borderaxespad=0.)

        self.draw()

    def load_subp_style(self):

        axis_major_step = []
        axis_minor_step = []
        # TODO: ranges hardcoded
        axis_xmin = [-10, 0]
        axis_xmax = [10, 20000]

        for i in range(len(axis_xmin)):
            axis_major_step.append(int((axis_xmax[i] - axis_xmin[i]) \
                                       / (2 * (1 + i)))
                                  )
            axis_minor_step.append(axis_major_step[i] / 5)
            self.axis[i].set_xlim(axis_xmin[i],axis_xmax[i])

        self.axis[0].tick_params(axis='y', which='major', pad=7)
        self.axis[0].yaxis.tick_right()


        for i, ax in zip(range(len(self.axis)), self.axis):

            ax.xaxis.tick_top()
            ax.xaxis.set_ticks_position('top')
            ax.spines['right'].set_color('none')
            ax.spines['left'].set_color('none')
            ax.spines['bottom'].set_color('none')
            ax.tick_params(which='major', width=1.00)
            ax.tick_params(which='major', length=10)
            ax.tick_params(which='minor', width=0.75)
            ax.tick_params(which='minor', length=5)
            ax.grid(b=True, which='minor', axis='both')
            ax.grid(which='major', axis='both', linewidth=2)
            ax.xaxis.set_major_locator(
                ticker.MultipleLocator(axis_major_step[i]))
            ax.xaxis.set_minor_locator(
                ticker.MultipleLocator(axis_minor_step[i]))
            ax.yaxis.set_major_locator(ticker.MultipleLocator(10))
            ax.yaxis.set_minor_locator(ticker.MultipleLocator(2))

