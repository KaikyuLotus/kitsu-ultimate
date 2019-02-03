from exceptions.kitsu_exception import KitsuException


class UnregisteredBot(KitsuException):
    def __init__(self, token):
        self.message = f"Bot with token '{token}' not found on MongoDB."
        self.token = token
