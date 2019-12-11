from typing import List


class TelegramException(Exception):
    def __init__(self, message, description, args: List, values):
        self.message = message
        self.description = description
        self.args: List = args
        self.vls = values

    def __str__(self):
        args = [f"{self.args[i]}: {self.vls[i]}" for i in range(len(self.args))]
        args = "{" + ", ".join(args) + "}"
        return f"{self.message}, message: {self.description}, args: {args}"
