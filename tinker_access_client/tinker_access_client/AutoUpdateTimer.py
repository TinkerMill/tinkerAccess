import threading

from PackageInfo import PackageInfo
from ClientLogger import ClientLogger
from ClientOption import ClientOption
from CommandExecutor import CommandExecutor


class AutoUpdateTimer(object):

    def __init__(self, client, opts):
        self.__opts = opts
        self.__client = client
        self.__auto_update_timer = None
        self.__logger = ClientLogger.setup(opts)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__cancel_auto_update_timer()

    def __cancel_auto_update_timer(self):
        if self.__auto_update_timer:
            self.__auto_update_timer.cancel()

        self.__auto_update_timer = None

    # noinspection PyBroadException
    def __auto_update_timer_tick(self):
        if not self.__client.is_in_use():
            try:
                CommandExecutor().execute_commands([
                    '{0} update'.format(PackageInfo.pip_package_name)
                ])
            except Exception:
                pass

        self.__start_auto_update_timer()

    def __start_auto_update_timer(self):
        self.__cancel_auto_update_timer()

        auto_update = self.__opts.get(ClientOption.AUTO_UPDATE)
        if auto_update:
            auto_update_interval = self.__opts.get(ClientOption.AUTO_UPDATE_INTERVAL) * 60
            self.__auto_update_timer = threading.Timer(
                auto_update_interval,
                self.__auto_update_timer_tick
            )
            self.__auto_update_timer.start()

    def start(self):
        self.__start_auto_update_timer()
