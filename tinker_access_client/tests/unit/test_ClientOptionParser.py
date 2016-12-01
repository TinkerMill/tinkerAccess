from __future__ import absolute_import

import os
import unittest

from mock import patch
from optparse import OptionParser
from ConfigParser import RawConfigParser
from tinker_access_client.tinker_access_client.ClientOptionParser import ClientOption, ClientOptionParser


class ClientOptionParserTests(unittest.TestCase):

    @patch.object(os, 'path')
    @patch.object(RawConfigParser, 'read')
    @patch.object(RawConfigParser, 'items')
    @patch.object(RawConfigParser, 'has_section')
    @patch.object(OptionParser, 'set_usage')
    @patch.object(OptionParser, '_add_help_option')
    @patch.object(OptionParser, '_add_version_option')
    def test_ClientOptionParser(self, _0, _1, _2, mock_has_section, mock_items, _3, mock_path):
        mock_path.isfile.return_value = True
        mock_has_section.return_value = True
        config_file_device_id = 'foo-bar'
        config_file_log_level = 99
        mock_items.return_value = [
            (ClientOption.DEVICE_ID, config_file_device_id),
            (ClientOption.LOG_LEVEL, config_file_log_level)
        ]

        command_line_device_id = 'la-la'
        command_line_arguments = [
            '--device-id=' + command_line_device_id
        ]

        opts = ClientOptionParser().parse_args(command_line_arguments)[0]
        expected_keys = vars(ClientOption).keys()
        expected_keys.remove('__module__')
        expected_keys.remove('__doc__')
        expected_number_of_options = len(expected_keys)

        actual_keys = opts.keys()
        actual_number_of_options = len(actual_keys)

        for key in expected_keys:
            self.assertTrue(key.lower() in actual_keys, 'client options is missing the \'%s\' option' % key.lower())

        self.assertEqual(actual_number_of_options, expected_number_of_options)
        self.assertEqual(opts.get(ClientOption.DEVICE_ID), command_line_device_id)
        self.assertEqual(opts.get(ClientOption.LOG_LEVEL), config_file_log_level)
