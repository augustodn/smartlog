# To find the class proper library look for qmake = gui in this case
from PyQt5.QtGui import QStandardItemModel
import sqlite3

DB_PATH = '/home/augusto/dev/arduino/winchPanel/winchdata.sql'

class WellModel(QStandardItemModel):
    def __init__(self, well=None, *args, **kwargs):
        super(WellModel, self).__init__(*args, **kwargs)
        # TODO: Make sure well structure is correct (not used by the moment)
        self.well = well or {
            'name': '',
            'field': '',
            'area': '',
            'province': '',
            'country': '',
            'company': '',
            'driller': '',
            'operator': '',
            'witness': '',
            'date': '',
            'service': '',
            'comments': '',
            'footNote': '',
            'inDate': ''}

    def insert_inDB(self):
        try:
            con = sqlite3.connect(DB_PATH)
            # Shortcut method
            cols = tuple(self.well.keys())
            data = tuple(self.well.values())
            con.execute("INSERT INTO well{} VALUES {}".format(cols, data))
            con.commit()
            con.close()
            return ""
        except:
            return "Warning: Couldn't store data into DB"
