import os
import logging
import logging.config as config
import logging.handlers as handlers
from ContextFilter import ContextFilter
from ClientOptionParser import ClientOptionParser, ClientOption


class ClientLogger(object):

    @staticmethod
    def setup(opts=None, phase=None):
        #TODO: remove ClientOptionParser, pass in opts always
        opts = opts if opts else ClientOptionParser(phase=phase).parse_args()[0]

        # if a logging config file exists, we will use that...
        logging_config_file = opts.get(ClientOption.LOGGING_CONFIG_FILE)
        if os.path.exists(logging_config_file):
            config.fileConfig(logging_config_file)
            return logging.getLogger()

        # otherwise add default handlers etc...
        logger = logging.getLogger()
        logger.filters = []
        logger.handlers = []

        log_level = opts.get(ClientOption.LOG_LEVEL)
        if phase == 'install' or opts.get(ClientOption.DEBUG):
            log_level = logging.DEBUG
        logger.setLevel(log_level)

        context_info = ' %(app_id)s (%(version)s) %(device_id)s %(device_name)s %(user_id)s %(user_name)s %(badge_code)s'

        # dev/log
        sys_log_file = '/var/log/syslog'
        if os.path.exists(sys_log_file):
            sys_log_handler = handlers.SysLogHandler('/dev/log')
            formatter = logging.Formatter('%(message)s' + context_info)
            sys_log_handler.setFormatter(formatter)
            sys_log_handler.addFilter(ContextFilter(opts))
            logger.addHandler(sys_log_handler)

        # console
        logger.addHandler(logging.StreamHandler())

        # fileHandler
        try:
            log_file = opts.get(ClientOption.LOG_FILE)
            if log_file:
                if not os.path.exists(os.path.dirname(log_file)):
                    os.makedirs(os.path.dirname(log_file))
                file_handler = handlers.TimedRotatingFileHandler(log_file, when='D', interval=1, backupCount=7)
                formatter = logging.Formatter('%(asctime)s %(message)s' + context_info, datefmt='%FT%T')
                file_handler.setFormatter(formatter)
                file_handler.addFilter(ContextFilter(opts))
                logger.addHandler(file_handler)
        except Exception as e:
            logger.exception(e)

        return logger

    # @staticmethod
    # def setup(phase=None):
    #     (opts, args) = ClientOptionParser(phase=phase).parse_args()
    #
    #     # if a logging config file exists, we will use that...
    #     logging_config_file = opts.get(ClientOption.LOGGING_CONFIG_FILE)
    #     if os.path.exists(logging_config_file):
    #         config.fileConfig(logging_config_file)
    #         return logging.getLogger()
    #
    #     # otherwise add default handlers etc...
    #     logger = logging.getLogger()
    #     logger.filters = []
    #     logger.handlers = []
    #
    #     log_level = opts.get(ClientOption.LOG_LEVEL)
    #     if phase == 'install' or opts.get(ClientOption.DEBUG):
    #         log_level = logging.DEBUG
    #     logger.setLevel(log_level)
    #
    #     context_info = ' %(app_id)s (%(version)s) %(device_id)s %(device_name)s %(user_id)s %(user_name)s %(badge_code)s'
    #
    #     # dev/log
    #     sys_log_file = '/var/log/syslog'
    #     if os.path.exists(sys_log_file):
    #         sys_log_handler = handlers.SysLogHandler('/dev/log')
    #         formatter = logging.Formatter('%(message)s' + context_info)
    #         sys_log_handler.setFormatter(formatter)
    #         sys_log_handler.addFilter(ContextFilter(opts))
    #         logger.addHandler(sys_log_handler)
    #
    #     # console
    #     logger.addHandler(logging.StreamHandler())
    #
    #     # fileHandler
    #     try:
    #         log_file = opts.get(ClientOption.LOG_FILE)
    #         if log_file:
    #             if not os.path.exists(os.path.dirname(log_file)):
    #                 os.makedirs(os.path.dirname(log_file))
    #             file_handler = handlers.TimedRotatingFileHandler(log_file, when='D', interval=1, backupCount=7)
    #             formatter = logging.Formatter('%(asctime)s %(message)s' + context_info, datefmt='%FT%T')
    #             file_handler.setFormatter(formatter)
    #             file_handler.addFilter(ContextFilter(opts))
    #             logger.addHandler(file_handler)
    #     except Exception as e:
    #         logger.exception(e)
    #
    #     return logger
