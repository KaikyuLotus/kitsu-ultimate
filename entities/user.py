from typing import List


class User:
    def __init__(self, uid, known_bots, started, language="IT", extra=None):
        self.uid: int = uid
        self.known_bots: List[int] = known_bots
        self.started: bool = started
        self.language: str = language
        self.extra: dict = extra if extra is not None else {}

    def __iter__(self):
        yield "uid", self.uid
        yield "known_bots", self.known_bots
        yield "started", self.started
        yield "language", self.language
        yield "extra", self.extra

    @classmethod
    def from_json(cls, json):
        if not json:
            return None
        return cls(json["uid"],
                   json["known_bots"],
                   json["started"],
                   json["language"],
                   json["extra"])
