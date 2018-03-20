import sys
import time
from base import MiBand2
from constants import ALERT_TYPES

MAC = sys.argv[1]

band = MiBand2(MAC, debug=True)
band.setSecurityLevel(level="medium")

if len(sys.argv) > 2:
    band.initialize()
    band.disconnect()
    sys.exit(0)
else:
    band.authenticate()

# print 'Message notif'
# band.send_alert(ALERT_TYPES.MESSAGE)
# time.sleep(3)
# # this will vibrate till not off
# print 'Phone notif'
# band.send_alert(ALERT_TYPES.PHONE)
# time.sleep(8)
# print 'OFF'
# band.send_alert(ALERT_TYPES.NONE)
# print 'Battery:', band.get_battery_info()
# print 'Time:', band.get_current_time()
# print 'Steps:', band.get_steps()
# print 'Heart rate oneshot:', band.get_heart_rate_one_time()

# def l(x):
#     print 'Realtime heart:', x
# band.get_heart_rate_realtime(l, 60)
band.debug()

band.disconnect()
