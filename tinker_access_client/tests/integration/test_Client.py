from __future__ import absolute_import

import tempfile
import unittest
import requests
from mock import patch, Mock
from backports import tempfile
from tests.integration.utils.CustomAssertions import CustomAssertions

from tinker_access_client.tinker_access_client.State import State
from tinker_access_client.tinker_access_client.PackageInfo import PackageInfo
from tinker_access_client.tinker_access_client.ClientOption import ClientOption
from tinker_access_client.tinker_access_client.ClientOptionParser import ClientOptionDefaults

from tinker_access_client.tests.integration.utils.VirtualDevice import VirtualDevice


def get_default_opts(temp_dir, opts=None):
    default_opts = ClientOptionDefaults.copy()
    default_opts.update({
        ClientOption.DEBUG: True,
        ClientOption.LOG_LEVEL: 10,
        ClientOption.MAX_POWER_DOWN_TIMEOUT: 5,
        ClientOption.PID_FILE: '{0}/{1}.pid'.format(temp_dir, PackageInfo.pip_package_name),
        ClientOption.LOG_FILE: '{0}/{1}.log'.format(temp_dir, PackageInfo.pip_package_name),
        ClientOption.CONFIG_FILE: '{0}/{1}.conf'.format(temp_dir, PackageInfo.pip_package_name),
        ClientOption.STATUS_FILE: '{0}/{1}.status'.format(temp_dir, PackageInfo.pip_package_name),
        ClientOption.LOGGING_CONFIG_FILE: '{0}/{1}.logging.conf'.format(temp_dir, PackageInfo.pip_package_name)
    })
    default_opts.update(opts or {})
    return default_opts


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


valid_login_response = Mock()
valid_login_response.json.return_value = {
    'username': user_name,
    'devicename': device_name,
    'userid': user_id,
    'time': session_seconds,
    'remaining_extensions': remaining_extensions
}

invalid_login_response = Mock()
invalid_login_response.json.return_value = {
    'username': user_name,
    'devicename': device_name,
    'userid': user_id,
    'time': 0,
    'remaining_extensions': remaining_extensions
}


class ClientTest(unittest.TestCase, CustomAssertions):

    def test_login(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            opts = get_default_opts(temp_dir)
            with patch.object(requests, 'get') as mock_get, VirtualDevice(opts) as device:

                #TODO: add assertions for LCD display prompts

                expected_transitions = [
                    State.INITIALIZED,
                    State.IDLE
                ]

                # Assert that the device has initialized and is idle
                self.assertTransitions(device, expected_transitions)
                self.assertIdlePins(opts, device)

                # Assert that an invalid login, doesn't cause any state changes, the device should still be idle
                mock_get.return_value = invalid_login_response
                device.scan_badge('some_badge_code')
                self.assertTransitions(device, expected_transitions)
                self.assertIdlePins(opts, device)

                # Assert that a valid login causes the device to transition to in_use and enables the expected pins.
                mock_get.return_value = valid_login_response
                device.scan_badge('some_badge_code')
                expected_transitions.append(State.IN_USE)
                self.assertTransitions(device, expected_transitions)
                self.assertInUsePins(opts, device)

                # Asssert the the logout pin cause the device to return to an idle state.
                device.hold_logout()
                expected_transitions.append(State.IDLE)
                self.assertTransitions(device, expected_transitions)
                self.assertIdlePins(opts, device)

    def test_training(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            opts = get_default_opts(temp_dir)
            with patch.object(requests, 'get') as mock_get, VirtualDevice(opts) as device:

                expected_transitions = [
                    State.INITIALIZED,
                    State.IDLE
                ]

                #TODO: add assertions for LCD display prompts

                # Assert that the device has initialized and is idle
                self.assertTransitions(device, expected_transitions)
                self.assertIdlePins(opts, device)

                # Assert that holding the logout pin down causes a transition into training mode, keeping the pins idle
                device.hold_logout(3)
                expected_transitions.append(State.IN_TRAINING)
                self.assertTransitions(device, expected_transitions)
                self.assertIdlePins(opts, device)

                # Assert that a bad login attempt for the trainer doesn't cause any state transition
                mock_get.return_value = invalid_login_response
                device.scan_badge('some_badge_code')
                self.assertTransitions(device, expected_transitions)
                self.assertIdlePins(opts, device)

                # Assert that a good login attempt for the trainer doesn't cause any state transition
                mock_get.return_value = valid_login_response
                device.scan_badge('some_badge_code')
                self.assertTransitions(device, expected_transitions)
                self.assertIdlePins(opts, device)

                # Assert that a bad login attempt for the student doesn't cause any state transition
                mock_get.return_value = invalid_login_response
                device.scan_badge('some_badge_code')
                self.assertTransitions(device, expected_transitions)
                self.assertIdlePins(opts, device)

                # Assert that a good login attempt for the student doesn't cause any state transition
                mock_get.return_value = valid_login_response
                device.scan_badge('some_badge_code')
                self.assertTransitions(device, expected_transitions)
                self.assertIdlePins(opts, device)

                # Assert the the logout pin cause the device to return to an idle state.
                device.hold_logout()
                expected_transitions.append(State.IDLE)
                self.assertTransitions(device, expected_transitions)
                self.assertIdlePins(opts, device)

    #TODO: test that an unexpected exception terminates the client and schedules a reboot