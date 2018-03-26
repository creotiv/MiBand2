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
fp.write('time, heartrate\n')


def log(rate):
    data = "%s, %s\n" % (int(time.time()), rate)
    fp.write(data)
    print data

while True:
    try:
        band = MiBand2(MAC, debug=True)
        band.setSecurityLevel(level="medium")
        band.authenticate()
        band.start_heart_rate_realtime(heart_measure_callback=log)
        band.disconnect()
    except BTLEException:
        pass
