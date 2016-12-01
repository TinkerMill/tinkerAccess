from __future__ import absolute_import

import logging
import unittest
import requests as _request

from mock import patch, Mock
from tinker_access_client.tinker_access_client.LoggedRequest import LoggedRequest


class LoggedRequestTest(unittest.TestCase):

    @patch.object(_request, 'get')
    @patch.object(logging, 'getLogger')
    def test_getRaisesExceptionIfMaximumRetriesExceeded(self, get_logger, mock_get):
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = _request.RequestException()
        mock_get.return_value = mock_response

        logger = get_logger.return_value
        self.assertRaises(_request.RequestException, LoggedRequest.get, 'foo')
        self.assertEqual(logger.debug.call_count, 1)
        self.assertEqual(logger.exception.call_count, 1)