# TODO more stats!
class Stats:
    def __init__(self, bot_id, sent_messages=0, read_messages=0):
        self.sent_messages = sent_messages
        self.read_messages = read_messages
        self.bot_id = bot_id

    def __iter__(self):
        yield "bot_id", self.bot_id
        yield "sent_messages", self.sent_messages
        yield "read_messages", self.read_messages

    @classmethod
    def from_json(cls, json):
        if not json:
            return None
        return cls(json["bot_id"],
                   json["sent_messages"] if "sent_messages" in json else 0,
                   json["read_messages"] if "read_messages" in json else 0)
