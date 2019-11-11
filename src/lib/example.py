import arducom
import time

ser = arducom.Serial()
db = arducom.DB()

while(not ser.start_acq('/dev/ttyUSB0', 500000, 1)):
    time.sleep(.5)

db.open_db('winchdata.sql')
table = db.create_table()
id_seq_acum = 0

while(id_seq_acum < 70):
    data, id_seq_acum = ser.get_data(id_seq_acum, 1)
    if data:
        while(not db.write_toDB(data, table)):
            time.sleep(.1)

ser.close()
db.close()
