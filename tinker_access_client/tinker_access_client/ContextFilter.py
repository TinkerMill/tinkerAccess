import logging
from PackageInfo import PackageInfo
from ClientOptionParser import ClientOption


class ContextFilter(logging.Filter):
    def __init__(self, opts):
        self.__device_id = opts.get(ClientOption.DEVICE_ID)
        self.__app_id = PackageInfo.pip_package_name
        self.__version = PackageInfo.version or '0.0.0'
        self.__user_info = None

    def update_user_context(self, user_info):
        self.__user_info = user_info

    def filter(self, record):
        record.app_id = self.__app_id
        record.device_id = self.__device_id
        record.version = self.__version

        if self.__user_info:
            record.user_id = self.__user_info.get('user_id')
            record.user_name = self.__user_info.get('user_name')
            record.badge_code = self.__user_info.get('badge_code')
            record.device_name = self.__user_info.get('device_name')
        else:
            record.user_id = \
                record.user_name = \
                record.badge_id = \
                record.badge_code = \
                record.device_name = ''

        return True
