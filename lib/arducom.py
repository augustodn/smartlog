import serial
import time
import sqlite3
from datetime import datetime

class Serial:


    def __init__(self):
        self.STR_STRING = '#STR'
        self.DTA_STRING = '#DTA'
        self.ARDU_CONFIRM = b'#OK'
        self.SEPARATOR = b'|-|'
        self.id_seq_old = -1


    def open(self, port, speed, timeout):
        self.port = port
        self.speed = speed
        self.timeout = timeout
        try:
            self.ser = serial.Serial(self.port,
                                     self.speed,
                                     timeout = self.timeout)
        except:
            print("[ERROR] Couldn't open serial port")
            return False
        # Wait until connection opens. Arduino restarts
        # when the connection is opened.
        print("[INFO] Serial port opened")
        return True

    def start(self):
        time.sleep(3)
        self.ser.reset_input_buffer()
        self.ser.write(self.STR_STRING.encode())
        self.retry = 0
        # Wait in a loop until the response
        # reaches the buffer
        while(self.ser.inWaiting() < 3 and self.retry < 5):
            time.sleep(.1)
            self.retry = self.retry + 1

        if self.ser.read(3) == self.ARDU_CONFIRM:
            print("[INFO] Serial connection established")
            return True
        else:
            print("[ERROR] Initialization not verified")
            return False

    def get_data(self, id_seq_acum):

        self.id_seq_acum = id_seq_acum
        # Send command to arduino
        print("[CMD] Give me data")
        self.ser.write(self.DTA_STRING.encode())
        self.inbuf = self.ser.inWaiting()
        if (self.inbuf):
            print("[INFO] Reading buffer")
            self.new_data = self.ser.read(self.inbuf)
            # TODO: Separator is not very funny
            data = self.new_data.split(self.SEPARATOR)
            data, self.id_seq_acum = self.process_buffer(data)
            return(data, self.id_seq_acum)

        return((), self.id_seq_acum)


    def process_buffer(self, data_list):
        data_list_ints = []

        for data in data_list:
            if len(data) == 10:
                # Convert to bytearray to enable assignments
                data = bytearray(data)

                # Get id_seq
                id_seq = 256*data[1] + data[0]
                # Handle integer overflow
                if (id_seq < self.id_seq_old):
                    self.id_seq_acum = self.id_seq_acum + 1
                    self.id_seq_old = -1
                else:
                    self.id_seq_old = id_seq

                id_seq  = id_seq + (self.id_seq_acum*65536)

                # Get depth value
                # Handle negative values as value complement
                neg_complement = 0
                if data[5] > 127:
                    data[5] = data[5] - 128
                    neg_complement = 2147483648

                depth = 16777216*data[5] + 65536*data[4]+\
                        256*data[3] + data[2] - neg_complement
                # Get CCL value
                ccl = 256*data[7] + data[6]
                # Get Tension value
                tension = 256*data[9] + data[8]

                data_list_ints.append((id_seq, depth, ccl, tension))

        print("[INFO] {} total packets read".format(id_seq))
        return(data_list_ints, self.id_seq_acum)

    def close(self):
        print("[INFO] Closing serial connection")
        self.ser.close()

class DB:

    def __init__(self):
        pass


    def open_db(self, database):
        try:
            # The default timeout is 5.0 seconds.
            # Check the API sqlite3 for reference.
            self.conn = sqlite3.connect(database)
            self.db_cur = self.conn.cursor()
            print("[INFO] DB Initialized")
            return(True)
        except:
            print("[ERROR] Couldn't initialize DB")
            return(False)

    def create_table(self):
        table_name = datetime.today().strftime("pass_%Y%m%d_%H%M%S")
        self.db_cur.execute("""CREATE TABLE {} (id_seq int, depth int, ccl int, tension int)""".
                            format(table_name))
        return(table_name)

    def write(self, data, table):
        self.db_cur.executemany('INSERT INTO {} VALUES (?,?,?,?)'.
                                format(table), data)

        try:
            self.conn.commit()
            return(True)
        except OperationalError:
            print("[ERROR] DB is busy")
            return(False)


    def close(self):
        print("[INFO] Closing DB connection")
        self.conn.close()
