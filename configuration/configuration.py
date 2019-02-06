import os

from configuration import config_parser

_env_variable = "ENVIRONMENT"  # TODO read from env
_default_env = "prod"
_configs = {}


class Configuration:
    def __init__(self, file_name):
        self._config = config_parser.parse_config_file(file_name)

    def get(self, key, default=None):
        if key not in self._config:
            return default
        return self._config[key]


def get_current_env():
    return os.getenv(_env_variable, _default_env)


def get_configuration(file_name) -> Configuration:
    if file_name not in _configs:
        _configs[file_name] = Configuration(file_name)
    return _configs[file_name]
