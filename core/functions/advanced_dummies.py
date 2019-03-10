from core.lowlevel import mongo_interface


def drop_users():
    mongo_interface.drop_users()
    return "Users dropped successffully"
