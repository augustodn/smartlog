import sqlite3

con = sqlite3.connect('BASEBLOK.db')
cur = con.cursor()
data = cur.execute("SELECT * FROM pass_20191029_121616").fetchall()
depth = 0

for row in data:
    cur.execute("update pass_20191029_121616 set depth = {} where id_seq = {}".
         format(depth, row[0]))
    print("update pass_20191029_121616 set depth = {} where id_seq = {}".
         format(depth, row[0]))
    depth += 45

con.commit()
con.close()
