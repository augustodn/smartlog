import sqlite3
import sys

conn = sqlite3.connect('../data/LLan-123.db')
cur = conn.cursor()
result = cur.execute("SELECT * FROM {} order by id_seq asc".format(sys.argv[1]))
prev = -1
count_err = 0
count_all = 0

for row in result:
    if (row[0] != (prev + 1)):
        #print(row[0], prev)
        count_err = count_err + 1
        if (row[0] > (prev+2)):
            print(row[0], prev, row[0] - prev)

    prev = row[0]
    count_all = count_all + 1

print(count_err, count_all)
