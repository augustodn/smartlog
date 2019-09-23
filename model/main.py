# To find the class proper library look for qmake = gui in this case
from PyQt5.QtGui import QStandardItemModel
import sqlite3

DB_PATH = './data/'

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

    def write_toDB(self):
        cols = tuple(self.well.keys())
        data = tuple(self.well.values())
        # TODO: Warn if database exists, although a new entry in well
        # table will be inserted.

        # Create Database, based on well name
        ff = open('{}{}.db'.format(DB_PATH, self.well['name']), 'w+')
        ff.close()

        try:
            con = sqlite3.connect('{}{}.db'.format(DB_PATH,
                                                        self.well['name']))
        except:
            return "Error: Couldn't initialize DB"

        try:
            con.execute("INSERT INTO well{} VALUES {}".format(cols, data))
            con.commit()
            con.close()
            return ""
        except:
            pass

        # Empty DB, create well table before returning
        try:
            con.execute("""CREATE TABLE well(name text, field text,"""
                        """area text, province text, country text,"""
                        """company text, driller text, operator text,"""
                        """witness text, date numeric, service text,"""
                        """comments text, footNote text,"""
                        """inDate numeric)""")
            con.execute("INSERT INTO well{} VALUES {}".format(cols, data))
            con.commit()
            con.close()
            return ""
        except:
            return "Warning: Couldn't store data into DB"
