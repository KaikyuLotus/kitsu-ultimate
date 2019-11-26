from exceptions.kitsu_exception import KitsuException


class BadConfigurationFileFormat(KitsuException):
    def __init__(self, file_name):
        self.message = f"Config file '{file_name}' has a bad format"
        self.file_name = file_name
