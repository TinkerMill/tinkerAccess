from __future__ import absolute_import

import logging
import unittest

from mock import patch, Mock
from tinker_access_client.tinker_access_client.ClientOption import ClientOption
from tinker_access_client.tinker_access_client.TinkerAccessServerApi import TinkerAccessServerApi
from tinker_access_client.tinker_access_client.LoggedRequest import LoggedRequest
from tinker_access_client.tinker_access_client.UserRegistrationException import UserRegistrationException
from tinker_access_client.tinker_access_client.UnauthorizedAccessException import UnauthorizedAccessException

user_id = 'someUserId'
session_seconds = 60
device_id = 'someDevice'
remaining_extensions = 2
user_name = 'someUserName'
trainer_id = 'someTrainerId'
server_address = 'someServer'
device_name = 'someDeviceName'
user_badge_code = 'someBadgeCode'
trainer_badge_code = 'someTrainerBadgeCode'


class TinkerAccessServerApiTests(unittest.TestCase):

    @patch.object(logging, 'getLogger')
    def setUp(self, get_logger):
        self.__logger = get_logger.return_value
        self.__api = TinkerAccessServerApi({
                ClientOption.DEVICE_ID: device_id,
                ClientOption.SERVER_ADDRESS: server_address
            })
        self.__logger.reset_mock()

    @patch.object(LoggedRequest, 'get')
    def test_loginRaisesUnauthorizedAccessException(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            'time': 0
        }
        mock_get.return_value = mock_response

        self.assertRaises(UnauthorizedAccessException, self.__api.login, user_badge_code)
        mock_get.assert_called_with('{0}/device/{1}/code/{2}'.format(server_address, device_id, user_badge_code))
        self.assertEqual(self.__logger.debug.call_count, 1)

    @patch.object(LoggedRequest, 'get')
    def test_loginReturnsLoginResponse(self, mock_get):
        mock_response = Mock()
        mock_response.json.return_value = {
            'username': user_name,
            'devicename': device_name,
            'userid': user_id,
            'time': session_seconds,
            'remaining_extensions': remaining_extensions
        }

        mock_get.return_value = mock_response
        login_response = self.__api.login(user_badge_code)
        self.assertTrue(login_response.get('user_name'), user_name)
        self.assertTrue(login_response.get('device_name'), device_name)
        self.assertTrue(login_response.get('user_id'), user_id)
        self.assertTrue(login_response.get('badge_code'), user_badge_code)
        self.assertTrue(login_response.get('session_seconds'), session_seconds)
        self.assertTrue(login_response.get('remaining_seconds'), session_seconds)
        self.assertTrue(login_response.get('remaining_extensions'), remaining_extensions)
        self.assertTrue(login_response.get('user_name'), user_name)

    @patch.object(LoggedRequest, 'get')
    def test_loginRaisesUnexpectedExceptionFromRequests(self, mock_get):
        mock_get.side_effect = RuntimeError
        self.assertRaises(RuntimeError, self.__api.login, user_name)
        self.assertEqual(self.__logger.debug.call_count, 1)

    @patch.object(LoggedRequest, 'get')
    def test_logoutRaisesUnexpectedExceptionFromRequests(self, mock_get):
        mock_get.side_effect = RuntimeError
        self.assertRaises(RuntimeError, self.__api.logout, user_id)
        self.assertEqual(self.__logger.debug.call_count, 1)

    @patch.object(LoggedRequest, 'get')
    def test_logout(self, mock_get):
        self.__api.logout(user_id)
        mock_get.assert_called_with('{0}/device/{1}/logout/{2}'.format(server_address, device_id, user_id))

    @patch.object(LoggedRequest, 'get')
    def test_register_userRaisesUserRegistrationException(self, _):
        self.assertRaises(UserRegistrationException, self.__api.register_user,
                          trainer_id, trainer_badge_code, user_badge_code)
        self.assertEqual(self.__logger.debug.call_count, 1)

    @patch.object(LoggedRequest, 'get')
    def test_register_userRaisesUnexpectedExceptionFromRequests(self, mock_get):
        mock_get.side_effect = RuntimeError
        self.assertRaises(RuntimeError, self.__api.register_user,
                          trainer_id, trainer_badge_code, user_badge_code)
        self.assertEqual(self.__logger.debug.call_count, 1)

    @patch.object(LoggedRequest, 'get')
    def test_register_user(self, mock_get):
        mock_response = Mock()
        mock_response.text = 'true'
        mock_get.return_value = mock_response
        self.__api.register_user(trainer_id, trainer_badge_code, user_badge_code)
        mock_get.assert_called_with('{0}/admin/marioStar/{1}/{2}/{3}/{4}'.format(
            server_address, trainer_id, trainer_badge_code, device_id, user_badge_code
        ))
