# To find the class proper library look for qmake = gui in this case
from PyQt5.QtGui import QStandardItemModel
import sqlite3
from datetime import datetime

DB_PATH = './data/'

class Well(QStandardItemModel):
    def __init__(self, well=None, *args, **kwargs):
        super(Well, self).__init__(*args, **kwargs)
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

    def write(self):
        cols = tuple(self.well.keys())
        data = tuple(self.well.values())
        # TODO: Warn if database exists, although a new entry in well
        # table will be inserted.

        # Create Database, based on well name, append if exists
        ff = open('{}{}.db'.format(DB_PATH, self.well['field']), 'a+')
        ff.close()

        try:
            con = sqlite3.connect('{}{}.db'.format(DB_PATH,
                                                        self.well['field']))
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
                        """ area text, province text, country text,"""
                        """ company text, driller text, operator text,"""
                        """ witness text, date numeric, service text,"""
                        """ comments text, footNote text,"""
                        """ inDate numeric)""")
            con.execute("INSERT INTO well {} VALUES {}".format(cols, data))
            con.commit()
            con.close()
            return ""
        except:
            return "Warning: Couldn't create table and store data into DB"

class Session:
    def __init__(self, params=None):
        if params:
            self.active = {
                'well': params['well'],
                'run': params['run'],
                'pass': params['pass'],
                'DBpath': params['DBpath'],
            }
        else:
            self.active = {
                'well': "",
                'run': "",
                'pass': "",
                'DBpath': "",
                'mode': ""
            }

class Pass:
    def __init__(self):
        pass

    def create_table(self, database):
        con = sqlite3.connect(database)
        table_name = datetime.today().strftime("pass_%Y%m%d_%H%M%S")
        con.execute("""CREATE TABLE {} (id_seq int, depth int, """
                    """ccl int, tension int)""".format(table_name))
        con.close()
        return table_name

class WellRunTable:

    def __init__(self):
        pass

    def write(self, session):
        con = sqlite3.connect(session.active['DBpath'])
        idWell = con.execute("""SELECT rowid from well where """
                             """name = '{}'""".\
                             format(session.active['well'])).\
                             fetchone()[0]
        try:
            con.execute("""INSERT INTO well_run_pass (id_well, """
                        """run, id_pass) values ({},{},'{}')""".\
                        format(idWell, session.active['run'],
                               session.active['pass']))
            con.commit()
            con.close()
            return ""
        except:
            pass

        # try to create table if can't insert data into table
        try:
            con.execute("""CREATE TABLE well_run_pass(id_well integer, """
                        """run integer, id_pass text, foreign key(id_well) """
                        """references well(rowid))""")

            con.execute("""INSERT INTO well_run_pass (id_well, """
                        """run, id_pass) values ({},{},'{}')""".\
                        format(idWell, session.active['run'],
                               session.active['pass']))
            con.commit()
            con.close()
            return
        except Exception as e:
            return str(e)
