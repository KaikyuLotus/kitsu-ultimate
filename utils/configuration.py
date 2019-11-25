import os

_env_variable = "KAI_ENVIRONMENT"


def get_current_env():
    return os.environ["KAI_ENVIRONMENT"]
