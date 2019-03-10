class Dialog:
    def __init__(self, reply: str, section: str, language: str, bot_id: int, usages: int = 0):
        self.reply: str = reply
        self.section: str = section
        self.language: str = language
        self.bot_id: int = int(bot_id)
        self.usages: int = usages

    def __iter__(self):
        yield "language", self.language,
        yield "reply", self.reply,
        yield "bot_id", self.bot_id,
        yield "section", self.section
        yield "usages", self.usages

    @classmethod
    def from_json(cls, json):
        if not json:
            return None
        return cls(json["reply"],
                   json["section"],
                   json["language"],
                   json["bot_id"],
                   json["usages"] if "usages" in json else 0)
