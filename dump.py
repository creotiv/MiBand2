import sys
import time
from base import MiBand2

MAC = sys.argv[1]
fp = open(sys.argv[2], 'a')
fp.write('time, heartrate\n')


def log(rate):
    data = "%s, %s" % (int(time.time()), rate)
    fp.write(data)
    print data

band = MiBand2(MAC, debug=True)
band.setSecurityLevel(level="medium")
band.authenticate()
band.get_heart_rate_realtime(log, 60 * 60 * 12)

band.disconnect()
