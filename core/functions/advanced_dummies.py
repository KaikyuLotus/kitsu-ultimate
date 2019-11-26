from datetime import datetime
from datetime import date
from random import choice

from core import reply_parser
from core.lowlevel import mongo_interface
from logger import log


def drop_users():
    mongo_interface.drop_users()
    return "Users dropped successffully"


def to_en(infos):
    if infos.chat.is_private:
        infos.db.user.language = "EN"
        infos.db.update_user()

    if infos.chat.is_supergroup or infos.chat.is_group:
        infos.db.group.language = "EN"
        infos.db.update_group()

    dialogs = mongo_interface.get_dialogs_of_section(infos.bot.bot_id, "speak.eng", "EN")
    if not dialogs:
        # TODO handle better missing dialog
        return "Ok"

    reply_parser.execute(choice(dialogs).reply, infos)
    return ""


def to_it(infos):

    if infos.chat.is_private:
        infos.db.user.language = "IT"
        infos.db.update_user()

    if infos.chat.is_supergroup or infos.chat.is_group:
        log.d("Dummy found in a group")
        infos.db.group.language = "IT"
        infos.db.update_group()

    dialogs = mongo_interface.get_dialogs_of_section(infos.bot.bot_id, "speak.it", "IT")
    if not dialogs:
        # TODO handle better missing dialog
        return "Ok"

    reply_parser.execute(choice(dialogs).reply, infos)
    return ""


def uptime_date(infos): return datetime.fromtimestamp(infos.bot.start_time).strftime("%d/%m/%Y")


def uptime_hour(infos): return datetime.fromtimestamp(infos.bot.start_time).strftime("%H:%M:%S")


def uptime_days(infos):
    since = infos.bot.start_time
    return str((date.today() - date.fromtimestamp(since)).days)
