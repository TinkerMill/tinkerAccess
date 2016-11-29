#!/usr/bin/python
import requests


class LoggedRequest(object):
    def __init__(self, logger):
        self.logger = logger

    #TODO: add retry logic & test see:https://pypi.python.org/pypi/retrying
    def get(self, url, params=None, **kwargs):
        self.logger.debug('Attempting API request...')
        try:
            response = requests.get(url, params, kwargs)
            self.logger.debug('API response: %s', response.json())
            response.raise_for_status()
        except Exception as e:
            self.logger.debug('API request failed!\n\turl: %s\n\tparams: %s\n\tkwargs: %s', url, params, kwargs)
            self.logger.exception(e)
            raise e

        self.logger.debug('API request succeeded.')
        return response
