import importlib.util

spec = importlib.util.spec_from_file_location("arducom", "../lib/arducom.py")
arducom = importlib.util.module_from_spec(spec)
spec.loader.exec_module(arducom)

serial = arducom.Serial()
serial.open('/dev/ttyUSB0', 500000, 1)
serial.start()
serial.set_depth(876.5, 98.9)
serial.set_depthCal(116.697)
serial.set_tensionCal(12021)
data, _ = serial.get_data(0)
print(data)

serial.close()
