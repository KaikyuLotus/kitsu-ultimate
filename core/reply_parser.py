import random
import threading
import time
import re

from inspect import signature
from random import choice

# Eval imports
# noinspection PyUnresolvedReferences
from typing import List, Optional, Dict

from core import manager
# noinspection PyUnresolvedReferences
from core.functions import advanced_dummies

from core.lowlevel import mongo_interface
from logger import log
from telegram import methods

string_dummies = {
    "[_]": "\n"
}

dummies = {
    "$base": {
        "{triggers.count}": "'unimplemented'",
        "{dialogs.count}": "'unimplemented'",
        "{equals.count}": "'unimplemented'",
        "{contents.count}": "'unimplemented'",
        "{interactions.count}": "'unimplemented'",
        "{eteractions.count}": "'unimplemented'",
        "{user.name}": "infos.user.name",
        "{user.id}": "infos.user.uid",
        "{user.last_name}": "infos.user.surname",
        "{user.username}": "infos.user.username",
        "{user.lang}": "infos.db.user.language",
        "{bot.id}": "infos.bot.bot_id",
        "{bot.name}": "infos.bot.name",
        "{bot.username}": "infos.bot.username",
        "{bot.groups}": "infos.db.get_groups_count()",
        "{bot.users}": "infos.db.get_users_count()",
        "{bot.started_users}": "infos.db.get_started_users_count()",
        "{chat.name}": "infos.chat.name",
        "{chat.id}": "infos.chat.cid",
        "{bots_count}": "manager.get_bots_count()",
        "{exec_time}": "ping(infos)",
        "{stats.read}": "manager.get_read_messages(infos.bot.bot_id)",
        "{stats.sent}": "manager.get_sent_messages(infos.bot.bot_id)",
        "{stats.uptime.date}": "advanced_dummies.uptime_date(infos)",
        "{stats.uptime.hour}": "advanced_dummies.uptime_hour(infos)",
        "{stats.uptime.days}": "advanced_dummies.uptime_days(infos)",
        "<drop_users>": "advanced_dummies.drop_users()",
        "<to_en>": "advanced_dummies.to_en(infos)",
        "<to_it>": "advanced_dummies.to_it(infos)"
    },

    "$on_reply": {
        "{quoted.name}": "infos.to_user.name",
        "{quoted.uid}": "infos.to_user.uid",
        "{quoted.surname}": "infos.to_user.surname",
        "{quoted.username}": "infos.to_user.username",
        "{quoted.is_bot}": "infos.to_user.is_bot",
        "{quoted.lang}": "infos.db.quoted.language"
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
            if dummy in reply:
                if dummy.startswith(">") and dummy.endswith("<"):
                    if not infos.user.is_maker_owner:
                        continue
                # eval is dangerous but here it's totally under control
                to_execute = dummies[dummy_t][dummy]
                if isinstance(to_execute, str):
                    reply = reply.replace(dummy, str(eval(to_execute)))
                elif callable(to_execute):
                    sign = signature(to_execute)
                    if len(sign.parameters) == 1:
                        reply = reply.replace(dummy, str(to_execute(infos)))
                    else:
                        reply = reply.replace(dummy, str(to_execute()))
                else:
                    log.w("Unknown dummy execution type")
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
        dialogs = mongo_interface.get_dialogs_of_section(infos.bot.bot_id, section, infos.db.language)

        if not dialogs:
            sub = "-"
            log.d(f"No dialogs found for section '{section}'")
        else:
            sub = choice(dialogs).reply

        reply = re.sub(r"\${(.*?)}", sub, reply, count=1)
        log.d(f"Substitution of section '{section}' done")

    return reply


def elaborate_multx(reply: str, infos):
    last_msg_id = None
    for action, var in re.findall(r"(send|action|wait|edit):(?:(.+?)(?: then|]))", reply):
        # TODO this can cause loops
        log.d(f"Action: {action}, var: {var}")
        if action == "send" or action == "edit":
            dialogs = mongo_interface.get_dialogs_of_section(infos.bot.bot_id, var, infos.db.language)
            if not dialogs:
                log.d(f"No dialogs for section {var}")
                continue
            dialog = choice(dialogs)
            log.d(f"Choosed reply {dialog.reply}")
            if action == "send":
                last_msg_id = infos.reply(dialog.reply, parse_mode=None)["message_id"]
            else:
                if not last_msg_id:
                    log.w("This action has not sent a message before, so there's nothing to edit.")
                    continue
                infos.edit(dialog.reply, parse_mode=None, msg_id=last_msg_id)
        elif action == "action":
            actions = {"type": "typing"}
            if var not in actions:
                log.d(f"Unknown action: {var}")
                continue
            methods.send_chat_action(infos.bot.token, infos.chat.cid, actions[var])
        elif action == "wait":
            try:
                var = int(var)
            except ValueError:
                log.w(f"Invalid value: {var}")
                continue
            time.sleep(var)


def execute(reply: str, infos, markup=None):
    if re.search(r"^\[.+]$", reply):
        threading.Thread(target=elaborate_multx, args=(reply, infos)).start()
        return

    match = re.search(r"{media:(\w{3}),(.+?)(,(.+))?}", reply)
    if match:
        log.d("Matched media regex")
        media_type = match.group(1)
        media_id = match.group(2)
        caption = match.group(4)
        if media_type == "stk":
            methods.send_sticker(infos.bot.token, infos.chat.cid, media_id, reply_markup=markup)
        elif media_type == "pht":
            methods.send_photo(infos.bot.token, infos.chat.cid, media_id, caption, reply_markup=markup)
        elif media_type == "aud":
            methods.send_audio(infos.bot.token, infos.chat.cid, media_id, reply_markup=markup)
        elif media_type == "voe":
            methods.send_voice(infos.bot.token, infos.chat.cid, media_id, reply_markup=markup)
        elif media_type == "doc":
            methods.send_doc(infos.bot.token, infos.chat.cid, media_id, reply_markup=markup)
        return

    reply, quote, markdown, markup_msg = parse(reply, infos)

    if not markup and markup_msg:
        markup = markup_msg

    if reply == "":
        log.d("Ignoring empty message")
        return

    log.d("Sending message")
    return methods.send_message(infos.bot.token, infos.chat.cid, reply,
                                parse_mode="markdown" if markdown else None,
                                reply_markup=markup)


def parse_rnd(reply):
    reg = r"rnd\[(\d+),\s*?(\d+)]"
    for minn, maxx in re.findall(reg, reply):
        reply = re.sub(reg, str(random.randint(int(minn), int(maxx))), reply, count=1)
    return reply


def parse_buttons(reply: str) -> [str, Optional[Dict]]:
    btns = []
    for row in re.findall(r"\[(.+?)\]", reply):
        btn_row = []
        for link, text in re.findall(r"<btn:(.+?)\|(.+?)>", row):
            btn_row.append(methods.link_button(text, link))
        btns.append(btn_row)

    reply = re.sub(r"\[(.+?)\]", "", reply)
    return reply, methods.inline_keyboard(btns) if btns else None


def parse(reply: str, infos, only_formatting=False) -> (str, bool, bool, List):

    mkup = None

    quote = "[quote]" in reply
    markdown = "[md]" in reply

    reply = reply.replace("[md]", "")
    reply = reply.replace("[quote]", "")

    if not only_formatting:
        log.d("Parsing reply string")
        reply = parse_sections(reply, infos)
        reply = parse_dummies(reply, infos)
        reply = parse_str_dummies(reply, infos)
        reply = parse_rnd(reply)
        reply, mkup = parse_buttons(reply)

    return reply, quote, markdown, mkup
