from exceptions.kitsu_exception import KitsuException


class ConfigurationError(KitsuException):
    def __init__(self, message):
        self.message = f"Bad config: {message}"
