class VirtualSerial(object):

    def __init__(self, *args):
        self.__badge_code = None

    # noinspection PyPep8Naming
    def flushInput(self, *args):
        self.__badge_code = None

    # noinspection PyPep8Naming
    def flushOutput(self, *args):
        pass

    def inWaiting(self, *args):
        return len(self.__badge_code) if self.__badge_code is not None else 0

    def readline(self, *args):
        return self.__badge_code

    def scan_badge(self, badge_code):
        self.__badge_code = badge_code