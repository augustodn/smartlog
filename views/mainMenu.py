from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, qApp, QMessageBox, QStatusBar
from PyQt5.QtCore import QTimer
from . import (digitalDisplay as dsp, curvePlot as cplt,
               newWell as nw, loadPass as lp, settings, saveAs,
               tensionCal, depthCal, setDepth)
import model.main as model
import lib.arducom as arducom
import time

qt_creator_file = "./resources/mainMenu.ui"
Ui_MainWindow, QtBaseClass = uic.loadUiType(qt_creator_file)

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        self.setupUi(self)

        self.session = model.Session()
        self.newWell = nw.NewWell()
        self.loadPass = lp.LoadPass()
        self.curvePlot = cplt.CurvePlot()
        self.saveAs = saveAs.SaveAs()
        self.serial = arducom.Serial()
        self.serial.opened = False
        self.ardu2DB = arducom.DB()
        self.settings = settings.Settings()
        self.speedWdgt = dsp.DigitalDisplay(title='Speed', decPnt=True)
        self.depthWdgt = dsp.DigitalDisplay(title='Depth', decPnt=True)
        self.setDepth = setDepth.SetDepth(None)

        # Connections
        self.actionWell.triggered.connect(self.new_well)
        self.actionRun.triggered.connect(self.new_run)
        self.actionPass.triggered.connect(self.new_pass)
        self.actionLoad.triggered.connect(self.load_pass)
        self.actionSaveAs.triggered.connect(self.save_as)

        self.actionStart.triggered.connect(self.start_dataAcq)
        self.actionStop.triggered.connect(self.stop_dataPolling)
        self.actionTension.triggered.connect(self.cal_tension)
        self.actionDepthCal.triggered.connect(self.cal_depth)
        self.actionDepthCorrect.triggered.connect(self.set_depth)
        self.actionSettings.triggered.connect(self.new_settings)

        self.actionPlot.triggered.connect(self.curve_plot)
        self.actionDepth.triggered.connect(self.depth_window)
        self.actionSpeed.triggered.connect(self.speed_window)
        self.actionExit.triggered.connect(qApp.quit)

        # Signals
        self.loadPass.sessionChanged.connect(self.update_session)
        self.newWell.sessionChanged.connect(self.update_session)
        self.settings.prefsChanged.connect(self.update_settings)
        self.curvePlot.canvas.speednDepthChanged.connect(self.update_displays)
        self.setDepth.sendDepth2panel.connect(self.send_depth_panel)

        # Misc
        self.actionExit.setStatusTip('Exit the application')
        self.actionDepth.setStatusTip('Open depth window')
        self.dbStatus = QStatusBar()
        self.statusbar = self.statusBar()
        self.statusbar.addWidget(self.dbStatus, stretch=1)

    def depth_window(self):
        self.depthWdgt.show()
    def speed_window(self):
        self.speedWdgt.show()

    def curve_plot(self):
        if self.session.active['mode'] == 'database':
            self.curvePlot.set_scroll_interval()
        self.curvePlot.update_depth()
        self.curvePlot.show()

    def new_well(self):
        self.newWell.show()

    def load_pass(self):
        self.loadPass.show()

    def save_as(self):
        self.saveAs.pdf()

    def new_run(self):
        run = self.session.active['run']
        self.session.active['run'] = run + 1
        self.session.active['mode'] = 'realtime'
        error = model.WellRunTable().write(self.session)
        self.update_session(self.session)
        if error:
            self.dialog_critical(error)

    def new_pass(self):
        self.session.active['pass'] = model.Pass().\
                create_table(self.session.active['DBpath'])
        self.session.active['mode'] = 'realtime'
        error = model.WellRunTable().write(self.session)
        self.update_session(self.session)
        if error:
            self.dialog_critical(error)

    def update_session(self, session):
        """ Read session object as argument coming from emit signal.
        Update session on Main Window """

        self.session = session
        self.curvePlot.session = session
        self.saveAs.session = session
        print(self.session.active)
        self.actionPlot.setEnabled(True)
        self.actionSpeed.setEnabled(True)
        self.actionDepth.setEnabled(True)
        self.actionSaveAs.setEnabled(True)
        self.menuConnect.setEnabled(True)
        msg = "Well: {} Run: {} Pass: {}".format(
            session.active['well'],
            str(session.active['run']),
            session.active['pass'][5:])
        self.dbStatus.showMessage(msg)

    def start_dataAcq(self):
        if not self.serial.opened:
            self.open_serialCon()
        self.start_dataPolling()

    def open_serialCon(self):
        """ Open microcontroller connection using the API """
        msg = ("""Failed to open serial port, check if """
               """winch panel is connected and retry""")

        try:
            if not self.serial.opened and self.port and self.brate:
                if not self.serial.open(self.port, self.brate, 1):
                    raise Exception

                self.serial.opened = True
        except:
            self.dialog_critical(msg)
            return -1

    def start_dataPolling(self):
        # serial.start() resets id_seq counter
        if not self.serial.start():
            self.dialog_critical("""Communication not established, check if """
                                 """winch panel is connected and retry""")
            return -1

        self.serSeq = 0
        self.lastItem = 0
        self.session.active['mode'] = 'realtime'
        self.update_session(self.session)
        self.curvePlot.update_depth()

        self.ardu2DB.open_db(self.session.active['DBpath'])
        # TODO: Probably better to put this in a thread
        self.serTimer = QTimer(self)
        self.serTimer.timeout.connect(self.read_data)
        self.serTimer.start(500)
        return 0

    def stop_dataPolling(self):
        """ Stop polling from microncontroller """
        self.serSeq = 0
        self.session.active['mode'] = 'database'
        self.update_session(self.session)
        self.curvePlot.update_depth()

        try:
            self.serTimer.stop()
            self.ardu2DB.close()
        except Exception as e:
            self.dialog_critical(str(e))
            return -1

    def read_data (self):
        # start = time.clock()
        data, self.serSeq = self.serial.get_data(self.serSeq) # ~ 0.5ms
        table = self.session.active['pass']
        get_data_t = time.clock()
        if data and self.session.active['mode'] == 'realtime':
            # ~ 68.5 ms mostly plotting data
            self.lastItem += len(data)
            self.curvePlot.set_scroll_interval(self.lastItem)
            update_plot_t = time.clock()
            while(not self.ardu2DB.write(data, table)): # ~ 1ms
                # retry insertion to DB
                time.sleep(.1)
                print("[INFO] Failed to write, retrying")

    def new_settings(self):
        self.settings.refresh_comboBoxes()
        self.settings.show()

    def update_settings(self, preferences):
        self.port = preferences['port']
        self.brate = preferences['brate']
        self.curvePlot.canvas.axis_xmin = preferences['axis_xmin']
        self.curvePlot.canvas.axis_xmax = preferences['axis_xmax']
        self.depthCal = preferences['depth_cal']
        self.tensionCal = preferences['tension_cal']
        self.curvePlot.canvas.DEPTH_SCALE = self.depthCal
        self.curvePlot.canvas.TENSION_SCALE = self.tensionCal
        self.saveAs.DEPTH_SCALE = self.depthCal
        self.saveAs.TENSION_SCALE = self.tensionCal
        self.menuCorrect.setEnabled(True)
        self.menuCalibrate.setEnabled(True)

    def update_displays(self, value):
        self.depthWdgt.lcdNumber.display(str(value[0]))
        speed = value[1] * 60
        self.speedWdgt.lcdNumber.display(str(speed))

    def cal_tension(self):
        self.tensionCal = tensionCal.TensionCal(self.port, self.brate)
        self.tensionCal.show()

    def cal_depth(self):
        self.depthCal = depthCal.DepthCal(self.port, self.brate)
        self.depthCal.show()

    def set_depth(self):
        self.setDepth.show()

    def send_depth_panel(self, depth):
        if not self.serial.opened:
            self.open_serialCon()
            time.sleep(2)

        answer = self.serial.set_depth(depth['val'], depth['cal'])
        if answer < 0:
            self.dialog_critical("New depth value not verified")
            return -1
        self.dialog_critical("Depth value set")
        return 0

    def dialog_critical(self, s):
        dlg = QMessageBox(self)
        dlg.setText(s)
        dlg.setIcon(QMessageBox.Critical)
        dlg.show()
