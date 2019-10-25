import serial
import time
import sqlite3
from datetime import datetime

class Serial:


    def __init__(self):
        self.STR_STRING = '#STR'
        self.DTA_STRING = '#DTA'
        self.SND_STRING = '#SND'
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
        # TODO: Fix this
        time.sleep(1)
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

    def set_depth(self, depth, depthCal):
        self.ser.reset_input_buffer()
        # Calculate the encoder counts for the depth value
        counts = int(depth * depthCal)
        if (counts > 2147483647 or counts < -2147483648):
            print("[ERROR] Depth exceeds min or max limit")
            return -1

        str2send = self.SND_STRING + str(counts)
        print("[CMD] Sending: {}".format(str2send))

        # Convert counts -> hex -> bin format
        countsHex = hex(counts)[2:]
        # If digits are less than 4 bytes
        # pad with 0's at the left
        if len(countsHex) < 8:
            countsHex = (8-len(countsHex)) * '0' + countsHex
        countsBytes = bytes.fromhex(countsHex)

        self.ser.write(self.SND_STRING.encode())
        self.ser.write(countsBytes)
        self.ser.write('\n'.encode())
        self.retry = 0
        # Wait in a loop until the response
        # reaches the buffer
        while(self.ser.inWaiting() < 3 and self.retry < 5):
            time.sleep(.1)
            self.retry = self.retry + 1

        if(self.ser.inWaiting() and
           self.ser.read(3) == self.ARDU_CONFIRM):

                print("[INFO] New depth value set sucessfully")
                return 0

        print("[ERROR] Depth value was not validated")
        return -2


    def set_depthCal(self, depthCal):
        SDC_STRING = '#SDC'
        # Convert to nearest integer
        depthCal = round(depthCal * 100)

        if (depthCal > 65535 or depthCal < 0):
            print("[ERROR] Cal factor exceeds min or max limit")
            return -1

        str2send = SDC_STRING + str(depthCal)
        print("[CMD] Sending: {}".format(str2send))

        # Convert counts -> hex -> bin format
        depthCalHex = hex(depthCal)[2:]
        # If digits are less than 4 bytes
        # pad with 0's at the left
        if len(depthCalHex) < 4:
            depthCalHex = (4-len(depthCalHex)) * '0' + depthCalHex
        depthCalBytes = bytes.fromhex(depthCalHex)

        self.ser.write(SDC_STRING.encode())
        self.ser.write(depthCalBytes)
        self.ser.write('\n'.encode())
        self.retry = 0
        # Wait in a loop until the response
        # reaches the buffer
        while(self.ser.inWaiting() < 3 and self.retry < 5):
            time.sleep(.1)
            self.retry = self.retry + 1

        if(self.ser.inWaiting() and
           self.ser.read(3) == self.ARDU_CONFIRM):

                print("[INFO] New depth calibration set sucessfully")
                return 0

        print("[ERROR] Depth calibration was not validated")
        return -2

    def set_tensionCal(self, tenCal):
        STC_STRING = '#STC'
        self.ser.write(STC_STRING.encode())

        self.retry = 0
        # Wait in a loop until the response
        # reaches the buffer
        while(self.ser.inWaiting() < 3 and self.retry < 5):
            time.sleep(.1)
            self.retry = self.retry + 1

        if self.ser.inWaiting():
            # Wait buffer to fill
            time.sleep(1)
            print (self.ser.read_all())


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
