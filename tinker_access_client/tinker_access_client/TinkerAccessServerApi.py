import logging
from ClientOption import ClientOption
from LoggedRequest import LoggedRequest
from UserRegistrationException import UserRegistrationException
from UnauthorizedAccessException import UnauthorizedAccessException


class TinkerAccessServerApi(object):

    def __init__(self, opts):
        self.__logger = logging.getLogger(__name__)
        self.__device_id = opts.get(ClientOption.DEVICE_ID)
        self.__server_address = opts.get(ClientOption.SERVER_ADDRESS)
        self.__is_a_door = opts.get(ClientOption.IS_A_DOOR)
        self.__door_unlock_time = opts.get(ClientOption.DOOR_UNLOCK_TIME)

    def login(self, user_badge_code):
        try:
            url = "%s/device/%s/code/%s" % (self.__server_address, self.__device_id, user_badge_code)
            response = LoggedRequest.get(url)

        except Exception as e:
            self.__logger.debug('Login attempt failed due to unexpected exception.')
            raise e

        data = response.json()
        session_seconds = data.get('time', 0) * 60

        # Returns 0 for an unauthorized user, so only reset door timeout if non-zero
        if self.__is_a_door and session_seconds > 0:
            session_seconds = self.__door_unlock_time

        if self.__is_a_door:
            remaining_extensions = 0
        else:
            remaining_extensions = data.get('extensions', float('inf'))
        
        login_response = {
            'user_name': data.get('username'),
            'device_name': data.get('devicename'),
            'user_id': data.get('userid'),
            'badge_code': user_badge_code,
            'session_seconds': session_seconds,
            'remaining_seconds': session_seconds,
            'remaining_extensions': remaining_extensions
        }

        if login_response.get('remaining_seconds') > 0:
            return login_response

        self.__logger.debug('Login attempt failed. The user is not authorized for this device.')
        raise UnauthorizedAccessException

    def logout(self, user_id):
        try:
            url = "%s/device/%s/logout/%s" % (self.__server_address, self.__device_id, user_id)
            LoggedRequest.get(url)

        except Exception as e:
            self.__logger.debug('Logout attempt failed due to unexpected exception.')
            raise e

    def register_user(self, trainer_id, trainer_badge_code, user_badge_code):
        try:
            url = "%s/admin/marioStar/%s/%s/%s/%s" % (
                self.__server_address, trainer_id, trainer_badge_code, self.__device_id, user_badge_code)
            response = LoggedRequest.get(url)

        except Exception as e:
            self.__logger.debug(
                'User registration failed due to unexpected exception.')
            raise e

        else:
            if response.text == 'true':
                return

        self.__logger.debug('User registration failed. The user is not authorized for this device.')
        raise UserRegistrationException
