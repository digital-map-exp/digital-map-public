import logging
from config import config_login


def get_my_logger(name):
    file_formatter = logging.Formatter(config_login.login_file_formatter)
    console_formatter = logging.Formatter(config_login.login_console_formatter)

    file_handler = logging.FileHandler(config_login.login_file)
    file_handler.setLevel(config_login.login_file_level)
    file_handler.setFormatter(file_formatter)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(config_login.login_console_level)
    console_handler.setFormatter(console_formatter)

    logger = logging.getLogger(name)
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    logger.setLevel(config_login.logger_level)

    logger.debug("MODULE LOGGER INITIALIZED: " + logger.name)
    return logger

def get_existing_logger(name):
    logger = logging.getLogger(name)
    logger.debug("MODULE LOGGER REUSED: " + logger.name)
    return logger

def login_decorator(func):
    logger = get_existing_logger(func.__module__)
    def run(*args, **kwargs):
        logger.debug("START FUNCTION: " + func.__module__ + ":" + func.__name__)
        result = func(*args, **kwargs)
        logger.debug("END FUNCTION  : " + func.__module__ + ":" + func.__name__)
        return result

    return run

def loging_shutdown():
    logging.shutdown()

