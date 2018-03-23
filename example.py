import sys
import time
from base import MiBand2
from constants import ALERT_TYPES

MAC = sys.argv[1]

band = MiBand2(MAC, debug=True)
band.setSecurityLevel(level="medium")

if len(sys.argv) > 2:
    if band.initialize():
        print("Init OK")
    band.set_heart_monitor_sleep_support(enabled=False)
    band.disconnect()
    sys.exit(0)
else:
    band.authenticate()

print 'Message notif'
band.send_alert(ALERT_TYPES.MESSAGE)
time.sleep(3)
# this will vibrate till not off
print 'Phone notif'
band.send_alert(ALERT_TYPES.PHONE)
time.sleep(8)
print 'OFF'
band.send_alert(ALERT_TYPES.NONE)
print 'Soft revision:',band.get_revision()
print 'Hardware revision:',band.get_hrdw_revision()
print 'Serial:',band.get_serial()
print 'Battery:', band.get_battery_info()
print 'Time:', band.get_current_time()
print 'Steps:', band.get_steps()
print 'Heart rate oneshot:', band.get_heart_rate_one_time()


def l(x):
    print 'Realtime heart:', x


def b(x):
    print 'Raw heart:', x.encode('hex')


def f(x):
    print 'Raw accel heart:', x.encode('hex')

# band.start_heart_rate_realtime(heart_measure_callback=l)
band.start_raw_data_realtime(heart_measure_callback=l, heart_raw_callback=b, accel_raw_callback=f)
band.disconnect()
