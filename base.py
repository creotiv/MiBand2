import struct
import time
import logging
from datetime import datetime
from Crypto.Cipher import AES
from Queue import Queue, Empty
from bluepy.btle import Peripheral, DefaultDelegate, ADDR_TYPE_RANDOM, BTLEException


from constants import UUIDS, AUTH_STATES, ALERT_TYPES, QUEUE_TYPES


class AuthenticationDelegate(DefaultDelegate):

    """This Class inherits DefaultDelegate to handle the authentication process."""

    def __init__(self, device):
        DefaultDelegate.__init__(self)
        self.device = device

    def handleNotification(self, hnd, data):
        # Debug purposes
        # self.device._log.debug("DATA: " + str(data.encode("hex")))
        # self.device._log.debug("HNd" + str(hnd))
        if hnd == self.device._char_auth.getHandle():
            if data[:3] == b'\x10\x01\x01':
                self.device._req_rdn()
            elif data[:3] == b'\x10\x01\x04':
                self.device.state = AUTH_STATES.KEY_SENDING_FAILED
            elif data[:3] == b'\x10\x02\x01':
                # 16 bytes
                random_nr = data[3:]
                self.device._send_enc_rdn(random_nr)
            elif data[:3] == b'\x10\x02\x04':
                self.device.state = AUTH_STATES.REQUEST_RN_ERROR
            elif data[:3] == b'\x10\x03\x01':
                self.device.state = AUTH_STATES.AUTH_OK
            elif data[:3] == b'\x10\x03\x04':
                self.device.status = AUTH_STATES.ENCRIPTION_KEY_FAILED
                self.device._send_key()
            else:
                self.device.state = AUTH_STATES.AUTH_FAILED
        elif hnd == self.device._char_heart_measure.getHandle():
            self.device.queue.put((QUEUE_TYPES.HEART, data))
        elif hnd == 0x38:
            # Not sure about this, need test
            if len(data) == 20 and struct.unpack('b', data[0])[0] == 1:
                self.device.queue.put((QUEUE_TYPES.RAW_ACCEL, data))
            elif len(data) == 16:
                self.device.queue.put((QUEUE_TYPES.RAW_HEART, data))
        else:
            self.device._log.error("Unhandled Response " + hex(hnd) + ": " +
                                   str(data.encode("hex")) + " len:" + str(len(data)))


class MiBand2(Peripheral):
    # _KEY = b'\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x40\x41\x42\x43\x44\x45'
    # _send_key_cmd = struct.pack('<18s', b'\x01\x08' + _KEY)
    # _send_rnd_cmd = struct.pack('<2s', b'\x02\x08')
    # _send_enc_key = struct.pack('<2s', b'\x03\x08')
    _KEY = b'\xf5\xd2\x29\x87\x65\x0a\x1d\x82\x05\xab\x82\xbe\xb9\x38\x59\xcf'
    _send_key_cmd = struct.pack('<18s', b'\x01\x00' + _KEY)
    _send_rnd_cmd = struct.pack('<2s', b'\x02\x00')
    _send_enc_key = struct.pack('<2s', b'\x03\x00')

    def __init__(self, mac_address, timeout=0.5, debug=False):
        FORMAT = '%(asctime)-15s %(name)s (%(levelname)s) > %(message)s'
        logging.basicConfig(format=FORMAT)
        log_level = logging.WARNING if not debug else logging.DEBUG
        self._log = logging.getLogger(self.__class__.__name__)
        self._log.setLevel(log_level)

        self._log.info('Connecting to ' + mac_address)
        Peripheral.__init__(self, mac_address, addrType=ADDR_TYPE_RANDOM)
        self._log.info('Connected')

        self.timeout = timeout
        self.mac_address = mac_address
        self.state = None
        self.queue = Queue()
        self.heart_measure_callback = None
        self.heart_raw_callback = None
        self.accel_raw_callback = None

        self.svc_1 = self.getServiceByUUID(UUIDS.SERVICE_MIBAND1)
        self.svc_2 = self.getServiceByUUID(UUIDS.SERVICE_MIBAND2)
        self.svc_heart = self.getServiceByUUID(UUIDS.SERVICE_HEART_RATE)

        self._char_auth = self.svc_2.getCharacteristics(UUIDS.CHARACTERISTIC_AUTH)[0]
        self._desc_auth = self._char_auth.getDescriptors(forUUID=UUIDS.NOTIFICATION_DESCRIPTOR)[0]

        self._char_heart_ctrl = self.svc_heart.getCharacteristics(UUIDS.CHARACTERISTIC_HEART_RATE_CONTROL)[0]
        self._char_heart_measure = self.svc_heart.getCharacteristics(UUIDS.CHARACTERISTIC_HEART_RATE_MEASURE)[0]

        # Enable auth service notifications on startup
        self._auth_notif(True)
        # Let MiBand2 to settle
        self.waitForNotifications(0.1)

    # Auth helpers ######################################################################

    def _auth_notif(self, enabled):
        if enabled:
            self._log.info("Enabling Auth Service notifications status...")
            self._desc_auth.write(b"\x01\x00", True)
        elif not enabled:
            self._log.info("Disabling Auth Service notifications status...")
            self._desc_auth.write(b"\x00\x00", True)
        else:
            self._log.error("Something went wrong while changing the Auth Service notifications status...")

    def _encrypt(self, message):
        aes = AES.new(self._KEY, AES.MODE_ECB)
        return aes.encrypt(message)

    def _send_key(self):
        self._log.info("Sending Key...")
        self._char_auth.write(self._send_key_cmd)
        self.waitForNotifications(self.timeout)

    def _req_rdn(self):
        self._log.info("Requesting random number...")
        self._char_auth.write(self._send_rnd_cmd)
        self.waitForNotifications(self.timeout)

    def _send_enc_rdn(self, data):
        self._log.info("Sending encrypted random number")
        cmd = self._send_enc_key + self._encrypt(data)
        send_cmd = struct.pack('<18s', cmd)
        self._char_auth.write(send_cmd)
        self.waitForNotifications(self.timeout)

    # Parse helpers ###################################################################

    def _parse_raw_accel(self, bytes):
        res = []
        for i in xrange(3):
            g = struct.unpack('hhh', bytes[2 + i * 6:8 + i * 6])
            res.append({'x': g[0], 'y': g[1], 'wtf': g[2]})
        # WTF
        # if len(bytes) == 20 and struct.unpack('b', bytes[0])[0] == 2:
        #     print struct.unpack('B', bytes[1])
        #     print "Accel x: %s y: %s z: %s" % struct.unpack('hhh', bytes[2:8])
        #     print "Accel x: %s y: %s z: %s" % struct.unpack('hhh', bytes[8:14])
        #     print "Accel x: %s y: %s z: %s" % struct.unpack('hhh', bytes[14:])
        return res

    def _parse_raw_heart(self, bytes):
        res = struct.unpack('HHHHHHH', bytes[2:])
        return res

    def _parse_date(self, bytes):
        year = struct.unpack('h', bytes[0:2])[0] if len(bytes) >= 2 else None
        month = struct.unpack('b', bytes[2])[0] if len(bytes) >= 3 else None
        day = struct.unpack('b', bytes[3])[0] if len(bytes) >= 4 else None
        hours = struct.unpack('b', bytes[4])[0] if len(bytes) >= 5 else None
        minutes = struct.unpack('b', bytes[5])[0] if len(bytes) >= 6 else None
        seconds = struct.unpack('b', bytes[6])[0] if len(bytes) >= 7 else None
        day_of_week = struct.unpack('b', bytes[7])[0] if len(bytes) >= 8 else None
        fractions256 = struct.unpack('b', bytes[8])[0] if len(bytes) >= 9 else None

        return {"date": datetime(*(year, month, day, hours, minutes, seconds)), "day_of_week": day_of_week, "fractions256": fractions256}

    def _parse_battery_response(self, bytes):
        level = struct.unpack('b', bytes[1])[0] if len(bytes) >= 2 else None
        last_level = struct.unpack('b', bytes[19])[0] if len(bytes) >= 20 else None
        status = 'normal' if struct.unpack('b', bytes[2])[0] == 0 else "charging"
        datetime_last_charge = self._parse_date(bytes[11:18])
        datetime_last_off = self._parse_date(bytes[3:10])

        # WTF?
        # struct.unpack('b', bytes[10])
        # struct.unpack('b', bytes[18])
        # print struct.unpack('b', bytes[10]), struct.unpack('b', bytes[18])

        res = {
            "status": status,
            "level": level,
            "last_level": last_level,
            "last_level": last_level,
            "last_charge": datetime_last_charge,
            "last_off": datetime_last_off
        }
        return res

    # Queue ###################################################################

    def _get_from_queue(self, _type):
        try:
            res = self.queue.get(False)
        except Empty:
            return None
        if res[0] != _type:
            self.queue.put(res)
            return None
        return res[1]

    def _parse_queue(self):
        while True:
            try:
                res = self.queue.get(False)
                _type = res[0]
                if self.heart_measure_callback and _type == QUEUE_TYPES.HEART:
                    self.heart_measure_callback(struct.unpack('bb', res[1])[1])
                elif self.heart_raw_callback and _type == QUEUE_TYPES.RAW_HEART:
                    self.heart_raw_callback(self._parse_raw_heart(res[1]))
                elif self.accel_raw_callback and _type == QUEUE_TYPES.RAW_ACCEL:
                    self.accel_raw_callback(self._parse_raw_accel(res[1]))
            except Empty:
                break

    # API ####################################################################

    def initialize(self):
        self.setDelegate(AuthenticationDelegate(self))
        self._send_key()

        while True:
            self.waitForNotifications(0.1)
            if self.state == AUTH_STATES.AUTH_OK:
                self._log.info('Initialized')
                self._auth_notif(False)
                return True
            elif self.state is None:
                continue

            self._log.error(self.state)
            return False

    def authenticate(self):
        self.setDelegate(AuthenticationDelegate(self))
        self._req_rdn()

        while True:
            self.waitForNotifications(0.1)
            if self.state == AUTH_STATES.AUTH_OK:
                self._log.info('Authenticated')
                return True
            elif self.state is None:
                continue

            self._log.error(self.state)
            return False

    def get_battery_info(self):
        char = self.svc_1.getCharacteristics(UUIDS.CHARACTERISTIC_BATTERY)[0]
        return self._parse_battery_response(char.read())

    def get_current_time(self):
        char = self.svc_1.getCharacteristics(UUIDS.CHARACTERISTIC_CURRENT_TIME)[0]
        return self._parse_date(char.read()[0:9])

    def get_revision(self):
        svc = self.getServiceByUUID(UUIDS.SERVICE_DEVICE_INFO)
        char = svc.getCharacteristics(UUIDS.CHARACTERISTIC_REVISION)[0]
        data = char.read()
        revision = struct.unpack('9s', data[-9:])[0] if len(data) == 9 else None
        return revision

    def get_hrdw_revision(self):
        svc = self.getServiceByUUID(UUIDS.SERVICE_DEVICE_INFO)
        char = svc.getCharacteristics(UUIDS.CHARACTERISTIC_HRDW_REVISION)[0]
        data = char.read()
        revision = struct.unpack('8s', data[-8:])[0] if len(data) == 8 else None
        return revision

    def set_encoding(self, encoding="en_US"):
        char = self.svc_1.getCharacteristics(UUIDS.CHARACTERISTIC_CONFIGURATION)[0]
        packet = struct.pack('5s', encoding)
        packet = b'\x06\x17\x00' + packet
        return char.write(packet)

    def set_heart_monitor_sleep_support(self, enabled=True, measure_minute_interval=1):
        char_m = self.svc_heart.getCharacteristics(UUIDS.CHARACTERISTIC_HEART_RATE_MEASURE)[0]
        char_d = char_m.getDescriptors(forUUID=UUIDS.NOTIFICATION_DESCRIPTOR)[0]
        char_d.write(b'\x01\x00', True)
        self._char_heart_ctrl.write(b'\x15\x00\x00', True)
        # measure interval set to off
        self._char_heart_ctrl.write(b'\x14\x00', True)
        if enabled:
            self._char_heart_ctrl.write(b'\x15\x00\x01', True)
            # measure interval set
            self._char_heart_ctrl.write(b'\x14' + str(measure_minute_interval).encode(), True)
        char_d.write(b'\x00\x00', True)

    def get_serial(self):
        svc = self.getServiceByUUID(UUIDS.SERVICE_DEVICE_INFO)
        char = svc.getCharacteristics(UUIDS.CHARACTERISTIC_SERIAL)[0]
        data = char.read()
        serial = struct.unpack('12s', data[-12:])[0] if len(data) == 12 else None
        return serial

    def get_steps(self):
        char = self.svc_1.getCharacteristics(UUIDS.CHARACTERISTIC_STEPS)[0]
        a = char.read()
        steps = struct.unpack('h', a[1:3])[0] if len(a) >= 3 else None
        meters = struct.unpack('h', a[5:7])[0] if len(a) >= 7 else None
        fat_gramms = struct.unpack('h', a[2:4])[0] if len(a) >= 4 else None
        # why only 1 byte??
        callories = struct.unpack('b', a[9])[0] if len(a) >= 10 else None
        return {
            "steps": steps,
            "meters": meters,
            "fat_gramms": fat_gramms,
            "callories": callories

        }

    def send_alert(self, _type):
        svc = self.getServiceByUUID(UUIDS.SERVICE_ALERT)
        char = svc.getCharacteristics(UUIDS.CHARACTERISTIC_ALERT)[0]
        char.write(_type)

    def get_heart_rate_one_time(self):
        # stop continous
        self._char_heart_ctrl.write(b'\x15\x01\x00', True)
        # stop manual
        self._char_heart_ctrl.write(b'\x15\x02\x00', True)
        # start manual
        self._char_heart_ctrl.write(b'\x15\x02\x01', True)
        res = None
        while not res:
            self.waitForNotifications(self.timeout)
            res = self._get_from_queue(QUEUE_TYPES.HEART)

        rate = struct.unpack('bb', res)[1]
        return rate

    def start_heart_rate_realtime(self, heart_measure_callback):
        char_m = self.svc_heart.getCharacteristics(UUIDS.CHARACTERISTIC_HEART_RATE_MEASURE)[0]
        char_d = char_m.getDescriptors(forUUID=UUIDS.NOTIFICATION_DESCRIPTOR)[0]
        char_ctrl = self.svc_heart.getCharacteristics(UUIDS.CHARACTERISTIC_HEART_RATE_CONTROL)[0]

        self.heart_measure_callback = heart_measure_callback

        # stop heart monitor continues & manual
        char_ctrl.write(b'\x15\x02\x00', True)
        char_ctrl.write(b'\x15\x01\x00', True)
        # enable heart monitor notifications
        char_d.write(b'\x01\x00', True)
        # start hear monitor continues
        char_ctrl.write(b'\x15\x01\x01', True)
        t = time.time()
        while True:
            self.waitForNotifications(0.5)
            self._parse_queue()
            # send ping request every 12 sec
            if (time.time() - t) >= 12:
                char_ctrl.write(b'\x16', True)
                t = time.time()

    def start_raw_data_realtime(self, heart_measure_callback=None, heart_raw_callback=None, accel_raw_callback=None):
        char_m = self.svc_heart.getCharacteristics(UUIDS.CHARACTERISTIC_HEART_RATE_MEASURE)[0]
        char_d = char_m.getDescriptors(forUUID=UUIDS.NOTIFICATION_DESCRIPTOR)[0]
        char_ctrl = self.svc_heart.getCharacteristics(UUIDS.CHARACTERISTIC_HEART_RATE_CONTROL)[0]

        if heart_measure_callback:
            self.heart_measure_callback = heart_measure_callback
        if heart_raw_callback:
            self.heart_raw_callback = heart_raw_callback
        if accel_raw_callback:
            self.accel_raw_callback = accel_raw_callback

        char_sensor = self.svc_1.getCharacteristics(UUIDS.CHARACTERISTIC_SENSOR)[0]
        # char_sens_d = char_sensor1.getDescriptors(forUUID=UUIDS.NOTIFICATION_DESCRIPTOR)[0]

        # char_sensor2 = self.svc_1.getCharacteristics('000000010000351221180009af100700')[0]
        # char_sens_d2 = char_sensor2.getDescriptors(forUUID=UUIDS.NOTIFICATION_DESCRIPTOR)[0]

        # char_sensor3 = self.svc_1.getCharacteristics('000000070000351221180009af100700')[0]
        # char_sens_d3 = char_sensor3.getDescriptors(forUUID=UUIDS.NOTIFICATION_DESCRIPTOR)[0]

        # char_sens_d1.write(b'\x01\x00', True)
        # char_sens_d2.write(b'\x01\x00', True)
        # char_sensor2.write(b'\x01\x03\x19')
        # char_sens_d2.write(b'\x00\x00', True)
        # char_d.write(b'\x01\x00', True)
        # char_ctrl.write(b'\x15\x01\x01', True)
        # char_sensor2.write(b'\x02')

        # stop heart monitor continues & manual
        char_ctrl.write(b'\x15\x02\x00', True)
        char_ctrl.write(b'\x15\x01\x00', True)
        # WTF
        # char_sens_d1.write(b'\x01\x00', True)
        # enabling accelerometer & heart monitor raw data notifications
        char_sensor.write(b'\x01\x03\x19')
        # IMO: enablee heart monitor notifications
        char_d.write(b'\x01\x00', True)
        # start hear monitor continues
        char_ctrl.write(b'\x15\x01\x01', True)
        # WTF
        char_sensor.write(b'\x02')
        t = time.time()
        while True:
            self.waitForNotifications(0.5)
            self._parse_queue()
            # send ping request every 12 sec
            if (time.time() - t) >= 12:
                char_ctrl.write(b'\x16', True)
                t = time.time()

    def stop_realtime(self):
        char_m = self.svc_heart.getCharacteristics(UUIDS.CHARACTERISTIC_HEART_RATE_MEASURE)[0]
        char_d = char_m.getDescriptors(forUUID=UUIDS.NOTIFICATION_DESCRIPTOR)[0]
        char_ctrl = self.svc_heart.getCharacteristics(UUIDS.CHARACTERISTIC_HEART_RATE_CONTROL)[0]

        char_sensor1 = self.svc_1.getCharacteristics(UUIDS.CHARACTERISTIC_HZ)[0]
        char_sens_d1 = char_sensor1.getDescriptors(forUUID=UUIDS.NOTIFICATION_DESCRIPTOR)[0]

        char_sensor2 = self.svc_1.getCharacteristics(UUIDS.CHARACTERISTIC_SENSOR)[0]

        # stop heart monitor continues
        char_ctrl.write(b'\x15\x01\x00', True)
        char_ctrl.write(b'\x15\x01\x00', True)
        # IMO: stop heart monitor notifications
        char_d.write(b'\x00\x00', True)
        # WTF
        char_sensor2.write(b'\x03')
        # IMO: stop notifications from sensors
        char_sens_d1.write(b'\x00\x00', True)

        self.heart_measure_callback = None
        self.heart_raw_callback = None
        self.accel_raw_callback = None
