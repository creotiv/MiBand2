import sys
import time
import argparse
from datetime import datetime
from base import MiBand2
from constants import ALERT_TYPES

parser = argparse.ArgumentParser()
parser.add_argument('-s', '--standard',  action='store_true',help='Shows device information')
parser.add_argument('-r', '--recorded',  action='store_true',help='Shows previews recorded data')
parser.add_argument('-l', '--live',  action='store_true',help='Measures live heart rate')
parser.add_argument('-i', '--init',  action='store_true',help='Initializes the device')
parser.add_argument('-m', '--mac', required=True, help='Mac address of the device')
args = parser.parse_args()

MAC = args.mac # sys.argv[1]

band = MiBand2(MAC, debug=True)
band.setSecurityLevel(level="medium")

if  args.init:
    if band.initialize():
        print("Init OK")
    band.set_heart_monitor_sleep_support(enabled=False)
    band.disconnect()
    sys.exit(0)
else:
    band.authenticate()

if args.recorded:
    print 'Print previews recorded data'
    band._auth_previews_data_notif(True)
    start_time = datetime.strptime("12.03.2018 01:01", "%d.%m.%Y %H:%M")
    band.start_get_previews_data(start_time)
    while band.active:
        band.waitForNotifications(0.1)

if args.standard:
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
    print 'Raw heart:', x


def f(x):
    print 'Raw accel heart:', x

if args.live:
    # band.start_heart_rate_realtime(heart_measure_callback=l)
    band.start_raw_data_realtime(
            heart_measure_callback=l,
            heart_raw_callback=b,
            accel_raw_callback=f)

band.disconnect()
