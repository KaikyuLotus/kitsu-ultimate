from typing import List


class User:
    def __init__(self, uid, known_bots, started):
        self.uid: int = uid
        self.known_bots: List[int] = known_bots
        self.started: bool = started

    def __iter__(self):
        yield "uid", self.uid
        yield "known_bots", self.known_bots
        yield "started", self.started

    @classmethod
    def from_json(cls, json):
        if not json:
            return None
        return cls(json["uid"], json["known_bots"], json["started"])
