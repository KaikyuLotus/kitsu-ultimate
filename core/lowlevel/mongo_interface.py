import os

from typing import List

from pymongo import MongoClient
from threading import Lock

from pymongo.collection import Collection

from entities.dialog import Dialog
from entities.trigger import Trigger
from exceptions.telegram_exception import TelegramException
from exceptions.unregistered_bot import UnregisteredBot
from logger import log

from ktelegram import methods

# TODO make a config file
from utils import configuration

_logger = log.get_logger("mongo_interface")

_db = configuration.get_current_env()
_logger.info(f"Using environment {_db}")

_mongo_uri = f"mongodb://{os.environ['MONGO_USER']}:{os.environ['MONGO_PASS']}@{os.environ['MONGO_IP']}:27017/{_db}" \
             f"?retryWrites=true&authSource=admin"

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


def _get_db(): return getattr(_get_client(), _db)


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
        "token":       token,
        "owner_id":    owner_id,
        # TODO make a method to change the start mode
        "clean_start": True,
        # TODO implement languages
        "language":    "IT"
    })


def get_dialogs_of_section(bot_id: int, section: str) -> List[Dialog]:
    return [Dialog.from_json(dialog) for dialog in _get_db().dialogs.find({
        "bot_id":  bot_id,
        "section": section
    })]


def get_triggers_of_type(bot_id: int, t_type: str) -> List[Trigger]:
    return [Trigger.from_json(trigger) for trigger in _get_db().triggers.find({
        "bot_id": bot_id,
        "type":   t_type
    })]


def get_triggers_of_section(bot_id: int, section: str) -> List[Trigger]:
    return [Trigger.from_json(trigger) for trigger in _get_db().triggers.find({
        "bot_id":  bot_id,
        "section": section
    })]


def get_triggers_of_type_and_section(bot_id: int, t_type: str, section: str) \
        -> List[Trigger]:
    return [Trigger.from_json(trigger) for trigger in _get_db().triggers.find({
        "bot_id":  bot_id,
        "type":    t_type,
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
