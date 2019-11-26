import logging

from configuration.config import config

logging.basicConfig(level=config["logging"]["level"],
                    format=config["logging"]["format"],
                    datefmt=config["logging"]["date-format"],
                    filename=config["logging"]["file-name"],
                    filemode='w')

_console = logging.StreamHandler()
_console.setLevel(config["logging"]["level"])
_formatter = logging.Formatter(config["logging"]["format"],
                               config["logging"]["date-format"])
_console.setFormatter(_formatter)

_logger = logging.getLogger("logger")
_logger.setLevel(config["logging"]["level"])
_logger.addHandler(_console)

i = _logger.info
e = _logger.error
d = _logger.debug
w = _logger.warning
