from typing import List

from pymongo import MongoClient
from threading import Lock

from pymongo.collection import Collection

from entities.dialog import Dialog
from entities.group import Group
from entities.user import User
from entities.trigger import Trigger
from exceptions.telegram_exception import TelegramException
from exceptions.unregistered_bot import UnregisteredBot
from logger import log

from telegram import methods

# TODO make a config file
from configuration import configuration

# _db = configuration.get_current_env()
# _logger.info(f"Using environment {_db}")
log.i("Getting data from configuration file")
_config = configuration.default()
_password = _config.get("mongo.password")
_username = _config.get("mongo.username")
_ip = _config.get("mongo.ip")
_db_name = _config.get("mongo.db_name")

_mongo_uri = f"mongodb://{_username}:{_password}@{_ip}/{_db_name}?retryWrites=true&authSource=admin"

_client = None
_singleton_lock = Lock()


def _get_client():
    global _client
    _singleton_lock.acquire()
    if not _client:
        _client = MongoClient(_mongo_uri)
    _singleton_lock.release()
    return _client


def stop():
    _get_client().close()


def _get_db(): return getattr(_get_client(), _db_name)


def _get_bots_collection():
    return _get_db().bots


def get_bots():
    return list(_get_bots_collection().find())


def drop_collection(collection_name: str):
    getattr(_get_db(), collection_name).drop()


def drop_bot_collection(bot: int): drop_collection(str(bot))


def drop_bots(): _get_bots_collection().drop()


def get_user_bots(user_id: int):
    return list(_get_bots_collection().find({"owner_id": {user_id}}))


def _get_bot(token: str):
    bot = _get_bots_collection().find_one({"token": str(token)})
    if not bot:
        raise UnregisteredBot(token)
    return bot


def _get_bot_collection(bot_id: int) -> Collection:
    return getattr(_get_db(), str(int(bot_id)))


def is_registered(token: str):
    return _get_bots_collection().find_one(
        {"token": str(token)}).count() is not 0


def get_bot_data(token: str):
    return _get_bot(token)


def register_bot(token: str, owner_id: int):
    # Check first if it's a real bot token
    try:
        methods.get_me(token)
    except TelegramException:
        return None

    _get_bots_collection().insert_one({
        "token": token,
        "owner_id": owner_id,
        # TODO make a method to change the start mode
        "clean_start": True,
        # TODO implement languages
        "language": "IT"
    })


def get_dialogs_of_section(bot_id: int, section: str) -> List[Dialog]:
    return [Dialog.from_json(dialog) for dialog in _get_db().dialogs.find({
        "bot_id": bot_id,
        "section": section
    })]


def get_triggers_of_type(bot_id: int, t_type: str) -> List[Trigger]:
    return [Trigger.from_json(trigger) for trigger in _get_db().triggers.find({
        "bot_id": bot_id,
        "type": t_type
    })]


def get_triggers_of_section(bot_id: int, section: str) -> List[Trigger]:
    return [Trigger.from_json(trigger) for trigger in _get_db().triggers.find({
        "bot_id": bot_id,
        "section": section
    })]


def get_triggers_of_type_and_section(bot_id: int, t_type: str, section: str) \
        -> List[Trigger]:
    return [Trigger.from_json(trigger) for trigger in _get_db().triggers.find({
        "bot_id": bot_id,
        "type": t_type,
        "section": section
    })]


def get_sections(bot_id: int):
    triggers = get_triggers(bot_id)
    dialogs = get_dialogs(bot_id)

    t_sections = [trigger.section for trigger in triggers]
    d_sections = [dialog.section for dialog in dialogs]

    for t_section in t_sections:
        if t_section not in d_sections:
            d_sections.append(t_section)

    x = []
    [x.append(t) for t in d_sections if t not in x]

    return x


def get_dialogs_count(bot_id: int) -> int:
    return _get_db().dialogs.find({"bot_id": bot_id}).count()


def get_triggers_count(bot_id: int) -> int:
    return _get_db().triggers.find({"bot_id": bot_id}).count()


def get_triggers(bot_id: int):
    return [Trigger.from_json(trigger) for trigger in _get_db().triggers.find({
        "bot_id": bot_id
    })]


def get_dialogs(bot_id: int) -> List[Dialog]:
    return [Dialog.from_json(dialog) for dialog in _get_db().dialogs.find({
        "bot_id": bot_id
    })]


def add_trigger(trigger: Trigger): _get_db().triggers.insert_one(dict(trigger))


def add_dialog(dialog: Dialog): _get_db().dialogs.insert_one(dict(dialog))


def get_bot_triggers(bot_id: int) -> List[Trigger]:
    return [Trigger.from_json(trigger) for trigger in _get_db().triggers.find({
        "bot_id": bot_id
    })]


def get_bot_dialogs(bot_id: int) -> List[Dialog]:
    return [Dialog.from_json(dialog) for dialog in _get_db().dialogs.find({
        "bot_id": bot_id
    })]


def update_dialog(old_dialog: Dialog, new_dialog: Dialog):
    _get_db().dialogs.update_one(dict(old_dialog), dict(new_dialog))


def update_trigger(old_trigger: Trigger, new_trigger: Trigger):
    _get_db().triggers.update_one(dict(old_trigger), dict(new_trigger))


def delete_dialog(dialog: Dialog): _get_db().dialogs.delete_one(dict(dialog))


def delete_trigger(trigger): _get_db().triggers.delete_one(dict(trigger))


def add_group(group: Group):
    _get_db().groups.insert_one(dict(group))


def delete_group(group: Group):
    _get_db().groups.delete_one(dict(group))


def get_groups() -> List[Group]:
    return [Group.from_json(group) for group in _get_db().groups.find()]


def get_group(group_id: int) -> Group:
    return Group.from_json(_get_db().groups.find_one({"cid": group_id}))


def get_bot_groups(bid: int) -> List[Group]:
    return [Group.from_json(group) for group in _get_db().groups.find({
        "present_bots": {"$in": [bid]}
    })]


def update_group(old_group: Group, new_group: Group):
    _get_db().groups.update_one(dict(old_group), dict(new_group))


def update_group_by_id(new_group: Group):
    _get_db().groups.replace_one({"cid": new_group.cid}, dict(new_group))


def add_user(user: User):
    _get_db().users.insert_one(dict(user))


def delete_user(user: User):
    _get_db().users.delete_one(dict(user))


def get_users() -> List[User]:
    return [User.from_json(user) for user in _get_db().users.find()]


def get_user(user_id: int) -> User:
    return User.from_json(_get_db().users.find_one({"uid": user_id}))


def update_user(old_user: User, new_user: User):
    _get_db().users.update_one(dict(old_user), dict(new_user))


def update_user_by_id(new_user: User):
    _get_db().users.replace_one({"uid": new_user.uid}, dict(new_user))


def get_known_users(bid: int):
    return [User.from_json(user) for user in _get_db().users.find({
        "known_bots": {"$in": [bid]}
    })]


def get_known_started_users(bid: int):
    return [User.from_json(user) for user in _get_db().users.find({
        "known_bots": {"$in": [bid]},
        "started": True
    })]


def drop_users():
    _get_db().users.drop()


def drop_groups():
    _get_db().groups.drop()
