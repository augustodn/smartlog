from PyQt5.QtWidgets import QFileDialog, QWidget
from PyQt5 import uic
from PyQt5.QtCore import pyqtSignal, QThread
import sqlite3
import matplotlib
matplotlib.use('Agg')
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import jinja2
import pdfkit
import os
from PyPDF2 import PdfFileMerger
import src.model.main as model

Ui_ProgressBar, QtBaseClass = uic.loadUiType("./src/resources/progressBar.ui")

DEPTH_SCALE = 98.0
TENSION_SCALE = 19.53125
CCL_FACTOR = 51.1
CCL_OFFSET = 0   # -511


class SaveAs(QWidget, Ui_ProgressBar):

    updateProgressBar = pyqtSignal(int)

    def __init__(self, parent=None):
        super(SaveAs, self).__init__(parent)
        self.session = model.Session()
        Ui_ProgressBar.__init__(self)
        self.setupUi(self)
        self.buttonBox.rejected.connect(self.cancel)
        self.DEPTH_SCALE = DEPTH_SCALE
        self.TENSION_SCALE = []
        self.axis_xmin = [-10, 0]
        self.axis_xmax = [10, 20000]

    def pdf(self):
        # self.make_frontPage()
        self.path, _ = QFileDialog.getSaveFileName(
            self, "Save file", "", "PDF file (*.pdf)")

        if self.path and self.session.active['DBpath']\
        and self.session.active['pass']:
            con = sqlite3.connect(self.session.active['DBpath'])
            rows = con.execute("SELECT COUNT(*) FROM {} order by id_seq asc"\
                               .format(self.session.active['pass']))\
                               .fetchall()[0][0]
            totPages = int(rows / 100) - 1
            con.close()
            self.progressBar.setRange(0, totPages)
            self.show()
            self.thread = PDFThread(self.session, totPages)
            self.thread.DEPTH_SCALE = self.DEPTH_SCALE
            self.thread.TENSION_SCALE = self.TENSION_SCALE
            self.thread.axis_xmax = self.axis_xmax
            self.thread.axis_xmin = self.axis_xmin
            self.thread.change_value.connect(self.update_progress)
            self.thread.finished.connect(self.make_frontPage)
            self.thread.start()

    def update_progress(self, value):
        self.progressBar.setValue(value)
        """
        if value == self.progressBar.maximum():
            self.make_frontPage()
            self.close()
        """

    def make_frontPage(self):
        templateLoader = jinja2.FileSystemLoader(searchpath="./")
        templateEnv = jinja2.Environment(loader=templateLoader)
        TEMPLATE_FILE = "./resources/template.html"
        template = templateEnv.get_template(TEMPLATE_FILE)

        # fetch data from well in DB
        if self.session.active['DBpath'] and self.session.active['well']\
        and self.session.active['run']:
            well = self.session.active['well']
            run = self.session.active['run']
            con = sqlite3.connect(self.session.active['DBpath'])
            data = con.execute("select * from well where name = '{}'".
                               format(well)).fetchone()

            # Generate Front Page
            if data:
                well = {
                    'name': data[0], 'field': data[1],
                    'area': data[2], 'province': data[3],
                    'country': data[4], 'company': data[5],
                    'driller': data[6], 'operator': data[7],
                    'witness': data[8], 'date': data[9],
                    'service': data[10], 'casing': '7',
                    'comments': data[11], 'footNote': data[12],
                    'inDate': data[13],
                }
                # TODO: Implement missing variables on template.html
                outputText = template.render(well = well)
                html_file = open("temp.html", 'w')
                html_file.write(outputText)
                html_file.close()
                pdfkit.from_file('temp.html', 'frontpage.pdf')
                os.remove('temp.html')

            # merge it with pdfcurve
            pdfs = ['frontpage.pdf', 'plot.pdf']
            merger = PdfFileMerger()

            for pdf in pdfs:
                merger.append(pdf)

            merger.write(self.path) # Replace it by path
            merger.close()
            os.remove('frontpage.pdf')
            os.remove('plot.pdf')
            self.close()

    def cancel(self):
        self.thread.exit(-1)
        # Ends thread loop
        self.thread.totPages = self.progressBar.value()
        # Close progressBar
        self.close()

class PDFThread(QThread):
    change_value = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, session, totPages, parent=None):
        super(PDFThread, self).__init__(parent)
        self.session = session
        self.totPages = totPages
        self.TENSION_SCALE = TENSION_SCALE
        self.DEPTH_SCALE = DEPTH_SCALE
        self.axis_xmin = [-10, 0]
        self.axis_xmax = [10, 20000]

    def run(self):
        pdfFile = 'plot.pdf'
        with PdfPages(pdfFile) as pdf:
            page = 0
            fig, axis = plt.subplots(
                             1, 2, # 1 row, 2 cols
                             gridspec_kw={'width_ratios':[1, 2]},
                             sharey=True,
                             figsize=(8.27, 11.69))
            con = sqlite3.connect(self.session.active['DBpath'])
            cur = con.cursor()
            #Determine loggig direction
            for i in list(range(self.totPages+1)):
                data = cur.execute(
                            """SELECT * FROM {} where id_seq > {} and """
                            """id_seq < {}""".format(
                                self.session.active['pass'],
                                i*100,
                                (i+1)*100)).fetchall()
                data = np.array(data)
                depth = data.transpose()[1] # array containing depth values
                if (depth[0] < depth[-1]) and (abs(depth[-1] - depth[0]) > 2):
                    loggedUp = False
                    break
                if (depth[0] > depth[-1]) and (abs(depth[-1] - depth[0]) > 2):
                    loggedUp = True
                    break

            while (page < (self.totPages + 1)):
                if not loggedUp:
                    count = page
                else:
                    # Reverse plotting order
                    count = self.totPages + 1 - page
                self.change_value.emit(page)
                result = cur.execute(
                    """SELECT * FROM {} where id_seq > {} and id_seq < {}"""
                    .format(self.session.active['pass'], count*100, (count+1)*100))\
                    .fetchall()

                y = []
                x1 = []
                x2 = []
                for var in result:
                    y.append(var[1] / self.DEPTH_SCALE)
                    x1.append((var[2] + CCL_OFFSET)/CCL_FACTOR)
                    x2.append(self.TENSION_SCALE[var[3]])


                plt.rc('text', usetex=False)
                [ax.clear() for ax in axis] # takes ~ 47.0 ms!!
                axis[0].plot(x1, y, label="CCL", linewidth=1.0)
                axis[1].plot(x2, y, label="Tension", linewidth=1.0)
                # plt.title('Tension Plot')

                fig.legend(ncol=2, loc='upper center',
                                mode="expand",
                                borderaxespad=0.)

                # To plot/log down. TODO: Evaluate movement
                fig.gca().invert_yaxis()
                axis_major_step = []
                axis_minor_step = []

                for i, _ in enumerate(self.axis_xmin):
                    axis_major_step.append(
                        int((self.axis_xmax[i] - self.axis_xmin[i])/(2*(1+i))))
                    axis_minor_step.append(axis_major_step[i] / 5)
                    axis[i].set_xlim(self.axis_xmin[i],self.axis_xmax[i])

                axis[0].tick_params(axis='y', which='major', pad=7)
                axis[0].yaxis.tick_right()

                for i, ax in enumerate(axis):

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

                page += 1
                pdf.savefig(fig)
                plt.close()

            con.close()

        self.finished.emit()
