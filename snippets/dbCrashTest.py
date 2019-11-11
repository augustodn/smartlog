import time
import sqlite3
"""
Run this script at the same time the logging system is
acquiring data to check if it stills filling the database
under r/w stress cycles.
"""

con = sqlite3.connect('../data/LLan-123.db')
i = 0

while (i < 100000):
    con.execute("select * from pass_20191031_145417").fetchall()
    i += 1
    time.sleep(.001)
    if ((i % 100) == 0):
        print(i)

con.close()
