# TODO add more fields
from typing import List


class Group:
    def __init__(self, cid, name, present_bots):
        self.cid: int = cid
        self.name: str = name
        self.present_bots: List[int] = present_bots

    def __iter__(self):
        yield "cid", self.cid
        yield "name", self.name
        yield "present_bots", self.present_bots

    @classmethod
    def from_json(cls, json):
        return cls(json["cid"], json["name"], json["present_bots"])
