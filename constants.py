___all__ = ['UUIDS']


class Immutable(type):

    def __call__(*args):
        raise Exception("You can't create instance of immutable object")

    def __setattr__(*args):
        raise Exception("You can't modify immutable object")


class UUIDS(object):

    __metaclass__ = Immutable

    BASE = "0000%s-0000-1000-8000-00805f9b34fb"

    SERVICE_MIBAND1 = "0000fee0-0000-1000-8000-00805f9b34fb"
    SERVICE_MIBAND2 = "0000fee1-0000-1000-8000-00805f9b34fb"

    SERVICE_ALERT = "00001802-0000-1000-8000-00805f9b34fb"
    SERVICE_HEART_RATE = "0000180d-0000-1000-8000-00805f9b34fb"

    CHARACTERISTIC_AUTH = "00000009-0000-3512-2118-0009af100700"
    CHARACTERISTIC_HEART_RATE_MEASURE = "00002a37-0000-1000-8000-00805f9b34fb"
    CHARACTERISTIC_HEART_RATE_CONTROL = "00002a39-0000-1000-8000-00805f9b34fb"
    CHARACTERISTIC_HEART_RATE_CONFIG = "00002902-0000-1000-8000-00805f9b34fb"
    CHARACTERISTIC_ALERT = "00002a06-0000-1000-8000-00805f9b34fb"
    CHARACTERISTIC_BATTERY = "00000006-0000-3512-2118-0009af100700"
    CHARACTERISTIC_STEPS = "00000007-0000-3512-2118-0009af100700"
    CHARACTERISTIC_LE_PARAMS = BASE % "FF09"

    CHARACTERISTIC_CURRENT_TIME = BASE % '2A2B'
    CHARACTERISTIC_AGE = BASE % '2A80'
    CHARACTERISTIC_USER_SETTINGS = "00000008-0000-3512-2118-0009af100700"

    DESCRIPTOR_AUTH = BASE % '2902'


class AUTH_STATES(object):

    __metaclass__ = Immutable

    AUTH_OK = "Auth ok"
    AUTH_FAILED = "Auth failed"
    ENCRIPTION_KEY_FAILED = "Encryption key auth fail, sending new key"
    KEY_SENDING_FAILED = "Key sending failed"
    REQUEST_RN_ERROR = "Something went wrong when requesting the random number"


class ALERT_TYPES(object):

    __metaclass__ = Immutable

    NONE = b'\x00'
    MESSAGE = b'\x01'
    PHONE = b'\x02'


class QUEUE_TYPES(object):

    __metaclass__ = Immutable

    HEART = 'heart'
