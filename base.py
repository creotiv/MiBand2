import struct
import time
import logging
from datetime import datetime
from Crypto.Cipher import AES
from Queue import Queue, Empty
from bluepy.btle import Peripheral, DefaultDelegate, ADDR_TYPE_RANDOM

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
            print 'LEN:', len(data)
            rate = struct.unpack('bb', data)[1]
            self.device.queue.put((QUEUE_TYPES.HEART, rate))
        else:
            self.device._log.error("Unhandled Response " + hex(hnd) + ": " +
                                   str(data.encode("hex")) + " len:" + str(len(data)))


class MiBand2(Peripheral):
    _KEY = b'\x30\x31\x32\x33\x34\x35\x36\x37\x38\x39\x40\x41\x42\x43\x44\x45'
    _send_key_cmd = struct.pack('<18s', b'\x01\x08' + _KEY)
    _send_rnd_cmd = struct.pack('<2s', b'\x02\x08')
    _send_enc_key = struct.pack('<2s', b'\x03\x08')

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

        self.svc_1 = self.getServiceByUUID(UUIDS.SERVICE_MIBAND1)
        self.svc_2 = self.getServiceByUUID(UUIDS.SERVICE_MIBAND2)
        self.svc_heart = self.getServiceByUUID(UUIDS.SERVICE_HEART_RATE)

        self._char_auth = self.svc_2.getCharacteristics(UUIDS.CHARACTERISTIC_AUTH)[0]
        self._desc_auth = self._char_auth.getDescriptors(forUUID=UUIDS.DESCRIPTOR_AUTH)[0]

        self._char_heart_ctrl = self.svc_heart.getCharacteristics(UUIDS.CHARACTERISTIC_HEART_RATE_CONTROL)[0]
        self._char_heart_measure = self.svc_heart.getCharacteristics(UUIDS.CHARACTERISTIC_HEART_RATE_MEASURE)[0]

        # Enable auth service notifications on startup
        self._auth_notif(True)
        # Let MiBand2 to settle
        self.waitForNotifications(0.1)

    def _auth_notif(self, enabled):
        if enabled:
            self._log.info("Enabling Auth Service notifications status...")
            self._desc_auth.write(b"\x01\x00", True)
        elif not enabled:
            self._log.info("Disabling Auth Service notifications status...")
            self._desc_auth.write(b"\x00\x00", True)
        else:
            self._log.error("Something went wrong while changing the Auth Service notifications status...")

    def _get_from_queue(self, _type):
        try:
            res = self.queue.get(False)
        except Empty:
            return None
        if res[0] != _type:
            self.queue.put(res)
            return None
        return res[1]

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

    def _parse_date(self, bytes):
        year = struct.unpack('h', bytes[0:2])[0] if len(bytes) >= 2 else None
        month = struct.unpack('b', bytes[2])[0] if len(bytes) >= 3 else None
        day = struct.unpack('b', bytes[3])[0] if len(bytes) >= 4 else None
        hours = struct.unpack('b', bytes[4])[0] if len(bytes) >= 5 else None
        minutes = struct.unpack('b', bytes[5])[0] if len(bytes) >= 6 else None
        seconds = struct.unpack('b', bytes[6])[0] if len(bytes) >= 7 else None

        return datetime(*(year, month, day, hours, minutes, seconds))

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

    def _init_after_auth(self):
        # char = self.svc_heart.getCharacteristics(UUIDS.CHARACTERISTIC_LE_PARAMS)[0]
        # print char.read()
        # char.write(b"\x03\x01", True)
        return
        # desc = self._char_heart_measure.getDescriptors(forUUID=UUIDS.DESCRIPTOR_AUTH)[0]
        # desc.write(b"\x01\x01", True)

    def initialize(self):
        self.setDelegate(AuthenticationDelegate(self))
        self._send_key()

        while True:
            self.waitForNotifications(0.1)
            if self.state == AUTH_STATES.AUTH_OK:
                self._log.info('Initialized')
                return True

            self._log.error(self.state)
            return False

    def authenticate(self):
        self.setDelegate(AuthenticationDelegate(self))
        self._req_rdn()

        while True:
            self.waitForNotifications(0.1)
            if self.state == AUTH_STATES.AUTH_OK:
                self._log.info('Authenticated')
                self._init_after_auth()
                return True

            self._log.error(self.state)
            return False

    def get_battery_info(self):
        char = self.svc_1.getCharacteristics(UUIDS.CHARACTERISTIC_BATTERY)[0]
        return self._parse_battery_response(char.read())

    def get_current_time(self):
        char = self.svc_1.getCharacteristics(UUIDS.CHARACTERISTIC_CURRENT_TIME)[0]
        return self._parse_date(char.read()[0:7])

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

        rate = res
        return rate

    def get_heart_rate_realtime(self, callback, timeout=10):
        """
            I though that mechanics of this request is not a realtime heart rate measure,
            but instead iterative measure of N times with sending reasults one by one.
            Thus we just make loop in which we sending iterative heart measure request after each 15sec, and that
            seems to work.
        """
        # stop continous
        self._char_heart_ctrl.write(b'\x15\x01\x00', True)
        # stop manual
        self._char_heart_ctrl.write(b'\x15\x02\x00', True)

        timeout = time.time() + timeout
        while timeout > time.time():
            timeout_base = time.time() + 15
            # start continous
            self._char_heart_ctrl.write(b'\x15\x01\x01', True)
            while timeout_base > time.time():
                self.waitForNotifications(self.timeout)
                res = self._get_from_queue(QUEUE_TYPES.HEART)
                if res:
                    callback(res)

    def debug(self):
        char_m = self.svc_heart.getCharacteristics(UUIDS.CHARACTERISTIC_HEART_RATE_MEASURE)[0]
        char_d = char_m.getDescriptors(forUUID=UUIDS.CHARACTERISTIC_HEART_RATE_CONFIG)[0]
        char_ctrl = self.svc_heart.getCharacteristics(UUIDS.CHARACTERISTIC_HEART_RATE_CONTROL)[0]

        char_sensor1 = self.svc_1.getCharacteristics('000000020000351221180009af100700')[0]
        char_sens_d1 = char_sensor1.getDescriptors(forUUID=0x2902)[0]

        char_sensor2 = self.svc_1.getCharacteristics('000000010000351221180009af100700')[0]
        char_sens_d2 = char_sensor2.getDescriptors(forUUID=0x2902)[0]

        char_sensor3 = self.svc_1.getCharacteristics('000000070000351221180009af100700')[0]
        char_sens_d3 = char_sensor3.getDescriptors(forUUID=0x2902)[0]

        # stop heart monitor continues
        char_ctrl.write(b'\x15\x01\x00', True)
        # stop heart monitor notifications
        char_d.write(b'\x00\x00', True)
        # IMO: enable notifications from Sensor 1
        char_sens_d1.write(b'\x01\x00', True)

        # IMO: This set band to get raw measures and processed heart measures in parallel
        char_sens_d2.write(b'\x01\x00', True)
        char_sensor2.write(b'\x01\x03\x19')
        char_sens_d2.write(b'\x00\x00', True)

        # char_sens_d3.write(b'\x01\x00', True)

        # IMO: enablee heart monitor notifications
        char_d.write(b'\x01\x00', True)

        # start hear monitor continues
        char_ctrl.write(b'\x15\x01\x01', True)
        # WTF
        char_sensor2.write(b'\x02')
        try:
            while True:
                self.waitForNotifications(0.5)
                char_ctrl.write(b'\x16')
                char_sensor2.write(b'\x00\x00')
        except Exception as e:
            print e
            pass
        finally:
            # stop heart monitor continues
            char_ctrl.write(b'\x15\x01\x00', True)
            char_ctrl.write(b'\x15\x01\x00', True)
            # IMO: stop heart monitor notifications
            char_d.write(b'\x00\x00', True)
            # WTF
            char_sensor2.write(b'\x03')
            # IMO: stop notifications from sensors
            char_sens_d1.write(b'\x00\x00', True)
            char_sens_d2.write(b'\x00\x00', True)
            char_sens_d3.write(b'\x00\x00', True)
