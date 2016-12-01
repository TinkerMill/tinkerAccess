import copy
import threading
from mock import Mock

default_pins = [
    [
        {'pin': 2, 'desc': '5v Power', 'status': False},
        {'pin': 4, 'desc': '5v Power', 'status': False},
        {'pin': 6, 'desc': 'Ground', 'status': False},
        {'pin': 8, 'desc': 'BCM 14', 'status': True},
        {'pin': 10, 'desc': 'BCM 15', 'status': True},
        {'pin': 12, 'desc': 'BCM 18', 'status': True},
        {'pin': 14, 'desc': 'Ground', 'status': False},
        {'pin': 16, 'desc': 'BCM 23', 'status': True},
        {'pin': 18, 'desc': 'BCM 24', 'status': True},
        {'pin': 20, 'desc': 'Ground', 'status': False},
        {'pin': 22, 'desc': 'BCM 25', 'status': True},
        {'pin': 24, 'desc': 'BCM 8', 'status': True},
        {'pin': 26, 'desc': 'BCM 7', 'status': True},
        {'pin': 28, 'desc': 'BCM 1', 'status': True},
        {'pin': 30, 'desc': 'Ground', 'status': False},
        {'pin': 32, 'desc': 'BCM 12', 'status': True},
        {'pin': 34, 'desc': 'Ground', 'status': False},
        {'pin': 36, 'desc': 'BCM 16', 'status': True},
        {'pin': 38, 'desc': 'BCM 20', 'status': True},
        {'pin': 40, 'desc': 'BCM 21', 'status': True}],
    [
        {'pin': 1, 'desc': '3v3 Power', 'status': False},
        {'pin': 3, 'desc': 'BCM 2', 'status': False},
        {'pin': 5, 'desc': 'BCM 3', 'status': False},
        {'pin': 7, 'desc': 'BCM 4', 'status': False},
        {'pin': 9, 'desc': 'Ground', 'status': False},
        {'pin': 11, 'desc': 'BCM 17', 'status': True},
        {'pin': 13, 'desc': 'BCM 27', 'status': True},
        {'pin': 15, 'desc': 'BCM 22', 'status': True},
        {'pin': 17, 'desc': '3v3 Power', 'status': False},
        {'pin': 19, 'desc': 'BCM 10', 'status': True},
        {'pin': 21, 'desc': 'BCM 9', 'status': True},
        {'pin': 23, 'desc': 'BCM 11', 'status': True},
        {'pin': 25, 'desc': 'Ground', 'status': False},
        {'pin': 27, 'desc': 'BCM 0', 'status': True},
        {'pin': 29, 'desc': 'BCM 5', 'status': True},
        {'pin': 31, 'desc': 'BCM 6', 'status': True},
        {'pin': 33, 'desc': 'BCM 13', 'status': True},
        {'pin': 35, 'desc': 'BCM 19', 'status': True},
        {'pin': 37, 'desc': 'BCM 26', 'status': True},
        {'pin': 39, 'desc': 'Ground', 'status': False}
    ]
]


class GPIO(object):
    HIGH = 1
    LOW = 0
    BCM = 11
    IN = 0
    OUT = 1
    PUD_DOWN = 1
    PUD_UP = 2

    RISING = True

    setmode = Mock()
    cleanup = Mock()
    setwarnings = Mock()
    setup = Mock()

    # noinspection PyShadowingBuiltins
    input = Mock()
    output = Mock()

    def __init__(self, opts):
        self.__opts = opts
        self.__pins = copy.deepcopy(default_pins)
        self.__callbacks = []

    def setup(self, pin, direction, status=False):
        self.__write_to_pin(pin, status)

    # GPIO.add_event_detect(pin, direction, callback=rising_edge_detected, bouncetime=500)  #
    def add_event_detect(self, pin, direction, **kwargs):

        # TODO: code for other arguments.. direction, bouncetime etc..
        self.__callbacks.append({'pin': pin, 'callback': kwargs.get('callback')})

    def __write_to_pin(self, target, status):
        for rows in self.__pins:
            for pin in rows:
                if pin['pin'] == int(target):
                    pin['status'] = status

                    # TODO: trigger any edge detection callbacks
                    for cb in self.__callbacks:
                        call_back_pin = cb.get('pin')
                        call_back_function = cb.get('callback')
                        if call_back_pin == int(target) and call_back_function:

                            def do_callback():
                                #time.sleep(hold_time) ## boundtime delay..
                                call_back_function(int(target))

                            t = threading.Thread(target=do_callback)
                            t.daemon = True
                            t.start()
                    break

    def output(self, pin, status):
        self.__write_to_pin(pin, status)

    def input(self, target):
        for rows in self.__pins:
            for pin in rows:
                if pin['pin'] == int(target):
                    return pin['status']
