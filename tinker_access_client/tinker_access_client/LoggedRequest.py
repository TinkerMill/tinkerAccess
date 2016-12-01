import logging
import requests

from retry.api import retry_call


class LoggedRequest(object):

    @staticmethod
    def get(url, params=None, **kwargs):
        logger = logging.getLogger(__name__)

        try:
            response = retry_call(
                LoggedRequest.__get,
                fargs=(url,  params),
                fkwargs=kwargs,
                tries=4,
                delay=1,
                backoff=3,
                logger=logger
            )

        except Exception as e:
            logger.debug('API request failed\n\turl: %s\n\tparams: %s\n\tkwargs: %s.', url, params, kwargs)
            logger.exception(e)
            raise e

        return response

    @staticmethod
    def __get(url, params=None, **kwargs):
        response = requests.get(url, params, timeout=5, **kwargs)
        response.raise_for_status()
        return response

