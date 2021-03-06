from PyQt5 import uic
from PyQt5.QtWidgets import (QVBoxLayout, QSizePolicy, QDialog, QMenuBar, QMenu,
                             QMessageBox)
from PyQt5.QtCore import pyqtSignal
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.ticker as ticker
import numpy as np
import sqlite3
import model.main as model
import time

DEPTH_SCALE = 98.0
TENSION_SCALE = 19.53125
CCL_FACTOR = 55.1
CCL_OFFSET = 0 # -511
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
                            dpi=100,
                            DB_PATH = self.session.active['DBpath'] ,
                            TABLE = self.session.active['pass'],
                            mode = self.session.active['mode'])
        layout.addWidget(self.canvas)
        self.mainWidget.setFocus()
        self.cableUp = False

        # Connections
        self.vScrollBar.valueChanged.connect(self.update_depth)

    def update_depth(self):
        self.canvas.DB_PATH = self.session.active['DBpath']
        self.canvas.TABLE = self.session.active['pass']
        self.canvas.mode = self.session.active['mode']
        # If cable movement is up, whe have to invert the scroll position
        # id_seq = 0 starts at the bottom and not at the beggining
        if self.cableUp:
            self.canvas.iter = self.vScrollBar.maximum() - self.vScrollBar.value()
        else:
            self.canvas.iter = self.vScrollBar.value()
        self.canvas.update_figure()

    def wheelEvent(self, event):
        yWheelScroll = event.angleDelta().y() / (-120)
        newvScrollBarVal = self.vScrollBar.value() + yWheelScroll
        if newvScrollBarVal < 0:
            newvScrollBarVal = 0
        self.vScrollBar.setValue(newvScrollBarVal)

    def check_movement(self, totPages):
        for i in list(range(totPages)):
            con = sqlite3.connect(self.session.active['DBpath'])
            data = con.execute(
                        """SELECT * FROM {} where id_seq > {} and """
                        """id_seq < {}""".format(
                            self.session.active['pass'],
                            i*100,
                            (i+1)*100)).fetchall()
            data = np.array(data)
            depth = data.transpose()[1] # array containing depth values
            if (depth[0] < depth[-1]) and (abs(depth[-1] - depth[0]) > 2):
                # Cable Down
                return False
            if (depth[0] > depth[-1]) and (abs(depth[-1] - depth[0]) > 2):
                # Cable Up
                return True


    def set_scroll_interval(self, lastItem=None):
        pageStep = 1
        wasAtMax = (self.vScrollBar.value() == \
                   (self.vScrollBar.maximum() - 2*pageStep))
        if not lastItem:  # database mode
            con = sqlite3.connect(self.session.active['DBpath'])
            lastItem = con.execute("SELECT COUNT(*) FROM {}"\
                       .format(self.session.active['pass'])).fetchall()[0][0]
            con.close()
            self.cableUp = self.check_movement(int(lastItem/100))

        lastItem = lastItem - pageStep
        self.vScrollBar.setMinimum(0)
        # Division by 100 depends on the DB query interval. Related to zoom
        self.vScrollBar.setMaximum(int(lastItem/100))
        self.vScrollBar.setPageStep(pageStep)
        if self.session.active['mode'] == 'realtime':
            # While logging down the slider is set to the bottom 
            if wasAtMax and not self.cableUp:
                self.vScrollBar.setValue(int(lastItem/100) - 2*pageStep)
            # While logging up, slider always on top (probably redundant)
            elif self.vScrollBar.value() < 2 and self.cableUp:
                # Trigger a plot refresh
                self.update_depth()
                # self.vScrollBar.setValue(1)


class MyMplCanvas(FigureCanvas):
    """Ultimately, this is a QWidget (as well as a FigureCanvasAgg, etc.)."""

    def __init__(self, parent=None, width=4, height=5, dpi=100, DB_PATH='',
                 TABLE= '', mode='', DEPTH_SCALE=0, TENSION_SCALE=[]):
        self.fig, self.axis = plt.subplots(
                                1, 2, # 1 row, 2 cols
                                gridspec_kw={'width_ratios':[1, 2]},
                                sharey=True,
                                figsize=(width, height)
                              )
        self.DB_PATH = DB_PATH
        self.TABLE = TABLE
        self.mode = mode
        self.DEPTH_SCALE = 0
        self.TENSION_SCALE = []
        FigureCanvas.__init__(self, self.fig)
        self.setParent(parent)
        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)


class MyDynamicMplCanvas(MyMplCanvas):
    """A canvas that updates itself every 300 msecs with a new plot."""
    speednDepthChanged = pyqtSignal(list)

    def __init__(self, *args, **kwargs):
        MyMplCanvas.__init__(self, *args, **kwargs)
        self.iter = 0
        self.axis_xmin = [-10, 0]
        self.axis_xmax = [10, 20000]
        self.top = 0
        self.bottom =  0


    def update_figure(self):
        try:
            con = sqlite3.connect(self.DB_PATH)
            cur = con.cursor()
            self.result = cur.execute(
                          "SELECT * FROM {} where id_seq > {} and id_seq < {}"\
                          .format(self.TABLE, self.iter*100, (self.iter+1)*100)
                          ).fetchall()

        except Exception as e:
            self.dialog_critical(str(e))
            return -1

        else:
            con.close()
        y = []
        x1 = []
        x2 = []
        if (len(self.TENSION_SCALE) != 1024):
            print("[ERROR] Tension scale array has not the proper lenght")
            return -1

        for var in self.result:
            y.append(var[1] / self.DEPTH_SCALE)
            x1.append((var[2] + CCL_OFFSET)/CCL_FACTOR)
            x2.append(self.TENSION_SCALE[var[3]])

        # Calculate speed
        self.set_depthnSpeed(y[-10:])
        y_arr = np.array(y)
        # print(y_arr.max(), y_arr.min())
        if y_arr.any() and self.bottom < y_arr.max():
            self.top = int(y_arr.min())
            self.bottom = int(y_arr.min()) + 50
            [ax.clear() for ax in self.axis] # takes ~ 47.0 ms!!
            self.load_subp_style()

        elif y_arr.any() and self.top > y_arr.min():
            self.top = int(y_arr.max()) - 50
            self.bottom = int(y_arr.max())
            [ax.clear() for ax in self.axis] # takes ~ 47.0 ms!!
            self.load_subp_style()

        # Plot data ~ 48.0 ms TODO: Maybe multithread this
        #[ax.clear() for ax in self.axis] # takes ~ 47.0 ms!!
        self.axis[0].set_ylim(self.top, self.bottom)
        self.axis[0].plot(x1, y, color='b', label="CCL", linewidth=1.0)
        self.axis[1].plot(x2, y, color='b', label="Tension", linewidth=1.0)
        self.fig.gca().invert_yaxis()
        # This two below takes ~ 15.0 ms
        # self.load_subp_style()
        self.draw_idle() #  increase performance x10 vs draw() method


    def load_subp_style(self):
        self.fig.legend(ncol=2, loc='upper center',
                        mode="expand",
                        borderaxespad=0.)

        # self.fig.gca().invert_yaxis()
        axis_major_step = []
        axis_minor_step = []
        for i in range(len(self.axis_xmin)):
            axis_major_step.append(int((self.axis_xmax[i] - self.axis_xmin[i]) \
                                       / (2 * (1 + i)))
                                  )
            axis_minor_step.append(axis_major_step[i] / 5)
            self.axis[i].set_xlim(self.axis_xmin[i],self.axis_xmax[i])

        self.axis[0].tick_params(axis='y', which='major', pad=7)
        self.axis[0].yaxis.tick_right()


        for i, ax in enumerate(self.axis):

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

    def set_depthnSpeed(self, y):
        if y:
            depth = y[-1]
            speed = 0
            if len(y) > 9:
                speedLst = []
                while y:
                    speedLst.append((y.pop() - y.pop())/0.01)

                speed = np.average(speedLst)

            self.speednDepthChanged.emit([depth, speed])

    def dialog_critical(self, s):
        dlg = QMessageBox(self)
        dlg.setText(s)
        dlg.setIcon(QMessageBox.Critical)
        dlg.show()
