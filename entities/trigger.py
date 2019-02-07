import re


class Trigger:
    def __init__(self, t_type, trigger, section, bot_id, lang):
        self.trigger = re.escape(trigger)
        self.raw_trigger = trigger
        self.type = t_type
        self.section = section
        self.bot_id = int(bot_id)
        self.language = lang

    def __iter__(self):
        yield "bot_id", self.bot_id,
        yield "trigger", self.trigger,
        yield "type", self.type,
        yield "section", self.section,
        yield "language", self.language

    @classmethod
    def from_json(cls, json):
        if not json:
            return None
        return cls(json["type"],
                   json["trigger"],
                   json["section"],
                   json["bot_id"],
                   json["language"])
