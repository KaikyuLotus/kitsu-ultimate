import re

from utils import regex_utils


class Trigger:
    def __init__(self, t_type: str, trigger: str, section: str, bot_id: int, lang: str, usages: int = 0):
        self.trigger: str = trigger
        if "@" in trigger:
            self.re_trigger: str = re.escape(trigger.split("@")[0])
        else:
            self.re_trigger: str = re.escape(trigger)
        self.re_trigger = regex_utils.string_to_regex(self.re_trigger)
        self.type: str = t_type
        self.section: str = section
        self.bot_id: int = int(bot_id)
        self.language: str = lang
        self.usages: int = usages

    def __iter__(self):
        yield "bot_id", self.bot_id,
        yield "trigger", self.trigger,
        yield "type", self.type,
        yield "section", self.section,
        yield "language", self.language
        yield "usages", self.usages

    @classmethod
    def from_json(cls, json):
        if not json:
            return None
        return cls(json["type"],
                   json["trigger"],
                   json["section"],
                   json["bot_id"],
                   json["language"],
                   json["usages"] if "usages" in json else 0)
