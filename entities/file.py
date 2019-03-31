class File:
    def __init__(self, file_id: str, file_size: int, file_path: str):
        self.file_id = file_id
        self.file_size = file_size
        self.file_path = file_path

    def __iter__(self):
        yield "file_id", self.file_id
        yield "file_size", self.file_size
        yield "file_path", self.file_path

    @classmethod
    def from_json(cls, json):
        return cls(json["file_id"],
                   json["file_size"],
                   json["file_path"])
