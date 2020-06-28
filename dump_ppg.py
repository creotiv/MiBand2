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

def heart(x):
    print ('Realtime heart:', x)


# Data arrives in arrays of either 3, 4 or 9 shorts:
#Realtime heart: 62
#[20073, 20084, 20044, 19940, 19825, 19737, 19660, 19624, 19605]
#[19581, 19570, 19556, 19553, 19553, 19582, 19595, 19612, 19652]
#[19682, 19701, 19754, 19784, 19830, 19873, 19900, 19945, 20044]
#[20202, 20399, 20611, 20756]
#Realtime heart: 63
#
# Print only lines of 10.

buffer =  []
buffer_len = 10

def writedata(data=None):
    global buffer, buffer_len
    if data is not None:
        buffer += data

        if len(buffer) >= buffer_len:
            data = "%s, %s\n" % (int(time.time()), buffer[:buffer_len])
            fp.write(data)
            buffer = buffer[buffer_len:]
    else:
            data = "%s, %s\n" % (int(time.time()), buffer)
            fp.write(data)

def log(raw_ppg_array):
    print(raw_ppg_array)
    writedata(raw_ppg_array)

try:
    band = MiBand2(MAC, debug=True)
    band.setSecurityLevel(level="medium")
    band.authenticate()
    band.start_ppg_data_realtime(sample_duration_seconds=30, heart_raw_callback=log, heart_measure_callback=heart)
    band.disconnect()
    writedata()
except BTLEException:
    pass
