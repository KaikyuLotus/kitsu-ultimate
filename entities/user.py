# TODO add more fields
from typing import List


class User:
    def __init__(self, uid, name, known_bots):
        self.uid: int = uid
        self.name: str = name
        self.known_bots: List[int] = known_bots

    def __iter__(self):
        yield "uid", self.uid
        yield "name", self.name
        yield "known_bots", self.known_bots

    @classmethod
    def from_json(cls, json):
        return cls(json["uid"], json["name"], json["known_bots"])
