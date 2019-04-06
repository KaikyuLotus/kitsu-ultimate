import os
from typing import Dict, Optional

from configuration import config_parser

_default_config_file_name = "resources/config.properties"
_env_variable = "ENVIRONMENT"  # TODO read from env
_default_env = "prod"

class Configuration:
    def __init__(self, file_name):
        self._config: Dict[str, str] = config_parser.parse_config_file(file_name)

    def get(self, key, default_value=None):
        if key not in self._config:
            return default_value
        return self._config[key]

    def get_int(self, key, default_value=None) -> Optional[int]:
        if key not in self._config:
            return default_value
        try:
            return int(self._config[key])
        except ValueError:
            return None

    def get_bool(self, key, default_value=False):
        if key not in self._config:
            return default_value
        return self._config[key].lower() == "true"

    def get_list(self, key, default_value=None):
        if key not in self._config:
            return default_value
        return [elem.strip() for elem in self._config[key].split(",")]


# Declared here to get the type...
_configs: Dict[str, Configuration] = {}


def get_current_env(forced_env: str = None):
    if forced_env:
        return forced_env
    return os.getenv(_env_variable, _default_env)


def get_configuration(file_name) -> Configuration:
    if file_name not in _configs:
        _configs[file_name] = Configuration(file_name)

    if _configs[file_name].get_bool("config.live_reload", False):
        return Configuration(file_name)
    else:
        return _configs[file_name]


def default():
    return get_configuration(_default_config_file_name)
