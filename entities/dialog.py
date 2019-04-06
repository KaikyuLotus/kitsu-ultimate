class Dialog:
    def __init__(self, reply: str, section: str, language: str, bot_id: int, usages: int = 0, probability: int = 100):
        self.reply: str = reply
        self.section: str = section
        self.language: str = language
        self.bot_id: int = int(bot_id)
        self.usages: int = usages
        self.probability: int = probability

    def __iter__(self):
        yield "language", self.language,
        yield "reply", self.reply,
        yield "bot_id", self.bot_id,
        yield "section", self.section
        yield "usages", self.usages
        yield "probability", self.probability

    @classmethod
    def from_json(cls, json):
        if not json:
            return None
        if "probability" not in json:
            print(json["reply"],
                  json["section"],
                  json["language"],
                  json["bot_id"],
                  json["usages"])

        return cls(json["reply"],
                   json["section"],
                   json["language"],
                   json["bot_id"],
                   json["usages"],
                   json["probability"] if "probability" in json else 100)
