import logging

_inited = None
_level = logging.DEBUG
_file_level = logging.INFO
_format = '[%(levelname)-8s] - %(asctime)s - %(funcName)-20s -> %(message)s'
_date_format = "%H:%M:%S"
_file_name = "logger/log.txt"

logging.basicConfig(level=_file_level,
                    format=_format,
                    datefmt=_date_format,
                    filename=_file_name,
                    filemode='w')


def get_console():
    console = logging.StreamHandler()
    console.setLevel(_level)
    # set a format which is simpler for console use
    formatter = logging.Formatter(_format, _date_format)
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    return console


def get_logger(name: str):
    logger = logging.getLogger(name)
    logger.setLevel(_level)
    logger.addHandler(get_console())
    logger.debug(f"Logger {name} ready")
    return logger
