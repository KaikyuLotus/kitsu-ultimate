import os

_env_variable = "ENVIRONMENT"  # TODO read from env
_default_env = "prod"


def get_current_env():
    return os.getenv(_env_variable, _default_env)
