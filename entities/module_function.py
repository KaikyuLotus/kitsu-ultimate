from typing import Type

from core import reply_parser
from logger import log


class ModuleFunction:
    def __init__(self, name: str, return_type: Type, optional: bool):
        self.name = name
        self.type = return_type
        self.optional = optional

    def elaborate_data(self, data) -> str:
        try:
            data = dict(data)
            for key in data:
                if not callable(data[key]):
                    return "every value in the dict must be a callable."
            reply_parser.dummies["$base"] = {**reply_parser.dummies["$base"], **data}
            count = len(data)
            return f"loaded {count} custom {'dummy' if count == 1 else 'dummies'}"
        except ValueError as err:
            log.w(str(err))
            return "returned bad data."
