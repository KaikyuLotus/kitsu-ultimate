import time
import re

from random import choice

from core.lowlevel import mongo_interface
from logger import log

string_dummies = {
    "[_]": "\n"
}

dummies = {
    "$base": {
        "{user.name}": "infos.user.name",
        "{user.id}": "infos.user.uid",
        "{user.last_name}": "infos.user.surname",
        "{user.username}": "infos.user.username",
        "{bot.id}": "infos.bot.bot_id",
        "{bot.name}": "infos.bot.name",
        "{bot.username}": "infos.bot.username",
        "{bot.groups}": "infos.db.get_groups_count()",
        "{bot.users}": "infos.db.get_users_count()",
        "{bot.started_users}": "infos.db.get_started_users_count()",
        "{bots_count}": "manager.get_bots_count()",
        "{exec_time}": "ping(infos)",
        "{triggers.count}": "'unimplemented'",
        "{dialogs.count}": "'unimplemented'",
        "{equals.count}": "'unimplemented'",
        "{contents.count}": "'unimplemented'",
        "{interactions.count}": "'unimplemented'",
        "{eteractions.count}": "'unimplemented'"
    },

    "$on_reply": {
        "{to_name}": "infos.to_user.name",
        "{to_uid}": "infos.to_user.uid",
        "{to_surname}": "infos.to_user.surname",
        "{to_username}": "infos.to_user.username",
        "{is_bot}": "infos.to_user.is_bot"
    }
}


def ping(infos):
    return int((time.time() - infos.time) * 1000)


def parse_dummies(reply: str, infos) -> str:
    for dummy_t in dummies:
        if dummy_t == "$on_reply":
            if not infos.is_reply:
                continue

        for dummy in dummies[dummy_t]:
            if dummy in reply:  # eval is dangerous but here is totally controlled
                reply = reply.replace(dummy, str(eval(dummies[dummy_t][dummy])))

    return reply


def parse_str_dummies(reply: str, infos) -> str:
    for dummy in string_dummies:
        if dummy not in reply:
            continue

        reply = reply.replace(dummy, string_dummies[dummy])

    return reply


def parse_sections(reply: str, infos) -> str:
    for section in re.findall(r"\${(.*?)}", reply):
        log.d(f"Section '{section}' found")
        dialogs = mongo_interface.get_dialogs_of_section(infos.bot.bot_id, section)

        if not dialogs:
            sub = "-"
            log.d(f"No dialogs found for section '{section}'")
        else:
            sub = choice(dialogs).reply

        reply = re.sub(r"\${(.*?)}", sub, reply, count=1)
        log.d(f"Substitution of section '{section}' done")

    return reply


def parse(reply: str, infos) -> (str, bool):
    reply = parse_sections(reply, infos)
    reply = parse_dummies(reply, infos)
    reply = parse_str_dummies(reply, infos)

    quote = "[quote]" in reply
    reply = reply.replace("[quote]", "")

    return reply, quote
