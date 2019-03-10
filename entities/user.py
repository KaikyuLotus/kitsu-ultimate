from typing import List


class User:
    def __init__(self, uid, known_bots, started, language="IT"):
        self.uid: int = uid
        self.known_bots: List[int] = known_bots
        self.started: bool = started
        self.language: str = language

    def __iter__(self):
        yield "uid", self.uid
        yield "known_bots", self.known_bots
        yield "started", self.started
        yield "language", self.language

    @classmethod
    def from_json(cls, json):
        if not json:
            return None
        return cls(json["uid"],
                   json["known_bots"],
                   json["started"],
                   json["language"] if "language" in json else "IT")
