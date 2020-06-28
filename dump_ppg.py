import sys
import os
import time
from base import MiBand2
from bluepy.btle import BTLEException

MAC = sys.argv[1]
filepath = sys.argv[2]
if os.path.exists(sys.argv[2]):
    os.remove(sys.argv[2])
fp = open(filepath, 'a')
fp.write('time, PPG_data\n')


def log(raw_ppg_array):
    data = "%s, %s\n" % (int(time.time()), raw_ppg_array)
    fp.write(data)
    print(raw_ppg_array)

try:
    band = MiBand2(MAC, debug=True)
    band.setSecurityLevel(level="medium")
    band.authenticate()
    band.start_ppg_data_realtime(heart_raw_callback=log)
    band.disconnect()
except BTLEException:
    pass
