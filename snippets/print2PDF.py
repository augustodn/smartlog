"""
=============
Multipage PDF
=============

This is a demo of creating a pdf file with several pages,
as well as adding metadata and annotations to pdf files.

If you want to use a multipage pdf file using LaTeX, you need
to use `from matplotlib.backends.backend_pgf import PdfPages`.
This version however does not support `attach_note`.
"""

import datetime
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.pyplot as plt
import sqlite3
import matplotlib.ticker as ticker

DEPTH_SCALE = 98.0
TENSION_SCALE = 19.53125
CCL_FACTOR = 51.1
CCL_OFFSET = 0   # -511

# Create the PdfPages object to which we will save the pages:
# The with statement makes sure that the PdfPages object is closed properly at
# the end of the block, even if an Exception occurs.


with PdfPages('logPlot.pdf') as pdf:
    page = 0
    fig, axis = plt.subplots(
                             1, 2, # 1 row, 2 cols
                             gridspec_kw={'width_ratios':[1, 2]},
                             sharey=True,
                             figsize=(8.27, 11.69)
                             )

    con = sqlite3.connect('../data/LLan-123.db')
    rows = con.execute("SELECT COUNT(*) FROM 'acq_20190917_134352' \
                order by id_seq asc").fetchall()[0][0]
    totPages = int(rows / 100) - 1
    while (page < totPages):
        cur = con.cursor()
        result = cur.execute(
            """SELECT * FROM {} where id_seq > {} and id_seq < {}"""
            .format('acq_20190917_134352', page*100,
                    (page+1)*100)
            ).fetchall()

        y = []
        x1 = []
        x2 = []
        for var in result:
            y.append(var[1] / DEPTH_SCALE)
            x1.append(var[2] + CCL_OFFSET)
            x2.append(var[3] * TENSION_SCALE)


        plt.rc('text', usetex=False)
        [ax.clear() for ax in axis] # takes ~ 47.0 ms!!
        axis[0].plot(x1, y, label="CCL", linewidth=1.0)
        axis[1].plot(x2, y, label="Tension", linewidth=1.0)
        # plt.title('Tension Plot')

        axis_xmin = [-10, 0]
        axis_xmax = [10, 20000]
        fig.legend(ncol=2, loc='upper center',
                        mode="expand",
                        borderaxespad=0.)

        # To plot/log down. TODO: Evaluate movement
        fig.gca().invert_yaxis()
        axis_major_step = []
        axis_minor_step = []

        for i, _ in enumerate(axis_xmin):
            axis_major_step.append(int((axis_xmax[i] - axis_xmin[i]) \
                                       / (2 * (1 + i)))
                                  )
            axis_minor_step.append(axis_major_step[i] / 5)
            axis[i].set_xlim(axis_xmin[i],axis_xmax[i])

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

        print("Printed page :", page)
        page += 1
        # or you can pass a Figure object to pdf.savefig
        pdf.savefig(fig)
        plt.close()

    con.close()
