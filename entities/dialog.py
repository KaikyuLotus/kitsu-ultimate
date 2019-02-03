class Dialog:
    def __init__(self, reply: str, section: str, language: str, bot_id: int):
        self.reply: str = reply
        self.section: str = section
        self.language: str = language
        self.bot_id: int = int(bot_id)

    def __iter__(self):
        yield "language", self.language,
        yield "reply", self.reply,
        yield "bot_id", self.bot_id,
        yield "section", self.section

    @classmethod
    def from_json(cls, json):
        return cls(json["reply"],
                   json["section"],
                   json["language"],
                   json["bot_id"])
