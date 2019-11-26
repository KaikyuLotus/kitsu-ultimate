import logging

from configuration import configuration

_inited = None
_config = configuration.default()
_level = getattr(logging, _config.get("logging.level", "DEBUG"))
_file_level = getattr(logging, _config.get("logging.file.level", "INFO"))
_format = _config.get("logging.format", '[%(levelname)-8s] - %(asctime)s - %(funcName)-20s -> %(message)s')
_date_format = _config.get("logging.date_format", "%H:%M:%S")
_file_name = _config.get("logging.file.name", "resources/log.txt")

logging.basicConfig(level=_file_level,
                    format=_format,
                    datefmt=_date_format,
                    filename=_file_name,
                    filemode='w')

_console = logging.StreamHandler()
_console.setLevel(_level)
_formatter = logging.Formatter(_format, _date_format)
_console.setFormatter(_formatter)

_logger = logging.getLogger("logger")
_logger.setLevel(_level)
_logger.addHandler(_console)

i = _logger.info
e = _logger.error
d = _logger.debug
w = _logger.warning
