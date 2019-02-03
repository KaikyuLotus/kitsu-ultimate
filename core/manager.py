from core.lowlevel import mongo_interface


def get_tokens():
    return [bot["token"] for bot in mongo_interface.get_bots()]


def get_bots():
    return mongo_interface.get_bots()


def get_bots_count():
    return len(get_bots())


def get_user_bots(user_id: int):
    return mongo_interface.get_user_bots(user_id)


def get_user_bots_count(user_id: int):
    return len(get_user_bots(user_id))
