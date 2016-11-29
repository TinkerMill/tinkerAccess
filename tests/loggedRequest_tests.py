#!/usr/bin/python
import requests
import unittest
from mock import patch, Mock
from LoggedRequest import LoggedRequest
from requests.exceptions import RequestException

urls = {
    'valid': {
        'url': 'mock://valid',
        'json': {'someKey': 'someValue'}
    },
    'invalid': {
        'url': 'mock://invalid'
    },
    'exception': {
        'url': 'mock://exception'
    },
}

def mocked_requests_get(*args, **kwargs):
    class MockResponse:
        def __init__(self, json_data, status_code):
            self.json_data = json_data
            self.status_code = status_code

        def json(self):
            return self.json_data

        def raise_for_status(self):
            if self.status_code != 200:
                raise RequestException()

    if args[0] == urls['valid']['url']:
        return MockResponse(urls['valid']['json'], 200)

    if args[0] == urls['invalid']['url']:
        return MockResponse({}, 404)

    raise RuntimeError()

class LoggedRequestTest(unittest.TestCase):
    def setUp(self):
        logger = Mock()
        self.logger = logger
        self.request = LoggedRequest(logger)

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_getLogsRequest(self, mocked_get):
        self.request.get(urls['valid']['url'])
        self.assertEqual(self.logger.debug.call_count, 3)
        self.assertEqual(self.logger.debug.mock_calls[1][1][1], urls['valid']['json'])

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_getRaisesExceptionOnInValidResponse(self, mocked_get):
        self.assertRaises(RequestException, self.request.get, urls['invalid']['url'])
        self.assertEqual(self.logger.debug.call_count, 3)
        self.assertEqual(self.logger.exception.call_count, 1)

    @patch('requests.get', side_effect=mocked_requests_get)
    def test_getLogsExceptions(self, mocked_get):
        self.assertRaises(RuntimeError, self.request.get, urls['exception']['url'])
        self.assertEqual(self.logger.debug.call_count, 2)
        self.assertEqual(self.logger.exception.call_count, 1)

