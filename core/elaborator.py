import base64
import json
from typing import List

from configuration import configuration
from core.functions import maker_functions, functions
from core.lowlevel import mongo_interface
from core.functions.maker_master_functions import stop
from entities.dialog import Dialog
from entities.infos import Infos
from random import choice, randint

from entities.trigger import Trigger
from logger import log
from utils import regex_utils

_config = configuration.default()
_autom_min = _config.get("autom.min", 1)
_autom_max = _config.get("autom.max", 100)
_autom_choice = _config.get("autom.choice", 10)
_backup_password = _config.get("backup.password", "")

_commands = {
    "bid": functions.bid,
    "start": functions.start,
    "uid": functions.uid
}

_owner_commands = {
    "menu": functions.menu,
}

_maker_commands = {
    "newbot": maker_functions.newbot,
    "myid": maker_functions.myid
}

_maker_master_commands = {
    "stop": stop
}


def complete_dialog_sec(infos: Infos, section: str):
    log.d(f"Elaborating reply of section {section}")
    dialogs: List[Dialog] = mongo_interface.get_dialogs_of_section(
        infos.bot.bot_id, section, infos.db.language)

    if not dialogs:
        log.d(f"No dialogs set for section {section}")
        infos.bot.notify(f"No dialogs set for section {section}")
        return

    dialog = choice(dialogs)

    while dialogs:
        dialog = choice(dialogs)
        # Ignore 100%
        if dialog.probability == 100:
            break

        # I wont accept a number higher than the probability
        if randint(1, 100) > dialog.probability:
            dialogs.remove(dialog)
        else:
            break  # Found!

        # Reset and retry
        dialog = None

    if not dialog:
        log.d("All dialogs where ignored")
        return

    infos.reply(dialog.reply, parse_mode=None)
    mongo_interface.increment_dialog_usages(dialog)


def complete_dialog(infos: Infos, trigger: Trigger):
    complete_dialog_sec(infos, trigger.section)
    mongo_interface.increment_sent_messages(infos.bot.bot_id)
    mongo_interface.increment_trigger_usages(trigger)
    return True


def elaborate_equal(infos: Infos, equal: Trigger):
    if regex_utils.is_equal(infos.message.text, equal.re_trigger):
        return complete_dialog(infos, equal)


def elaborate_content(infos: Infos, content: Trigger):
    if regex_utils.is_content(infos.message.text, content.re_trigger):
        return complete_dialog(infos, content)


def elaborate_interaction(infos: Infos, interaction: Trigger):
    is_inter = regex_utils.is_interaction(infos.message.text,
                                          infos.bot.regexed_name)

    if any([is_inter, infos.is_to_bot]):
        if regex_utils.is_in_message(infos.message.text, interaction.re_trigger):
            return complete_dialog(infos, interaction)


def elaborate_eteraction(infos: Infos, eteraction: Trigger):
    is_inter = regex_utils.is_interaction(infos.message.text,
                                          infos.bot.regexed_name)
    if is_inter and infos.is_reply:
        log.d("Message is a reply and starts/ends with bot's name")
        log.d(f"Checking trigger {eteraction.re_trigger}")
        if regex_utils.is_in_message(infos.message.text, eteraction.re_trigger):
            log.d("Trigger is present in text")
            return complete_dialog(infos, eteraction)


_t_type_elaborators = {
    "equal": elaborate_equal,
    "content": elaborate_content,
    "interaction": elaborate_interaction,
    "eteraction": elaborate_eteraction
}


def elaborate(infos: Infos):
    if not infos.message.is_text:
        return

    for t_type_elaborator in _t_type_elaborators:
        triggers = mongo_interface.get_triggers_of_type(infos.bot.bot_id,
                                                        t_type_elaborator,
                                                        infos.db.language)
        for trigger in triggers:
            if "@" in trigger.trigger:
                trigger.trigger, identifier = trigger.trigger.split("@")
                if identifier.lower() == "owner":
                    identifier = str(infos.bot.owner_id)
                if identifier.isnumeric():
                    if infos.user.uid != int(identifier):
                        continue

            if _t_type_elaborators[t_type_elaborator](infos, trigger):
                return

    if infos.bot.automs_enabled:
        log.d("Autom enabled, elaborating...")
        if randint(_autom_min, _autom_max) == _autom_choice:
            complete_dialog_sec(infos, "automatics")
            return

    if infos.is_to_bot:
        complete_dialog_sec(infos, "generic")


def command(infos: Infos):
    if infos.message.command in _commands:
        log.d(f"User issued command {infos.message.command}")
        _commands[infos.message.command](infos)
        return True
    return False


def owner_command(infos: Infos):
    if not infos.user.is_bot_owner:
        return False

    if infos.message.command in _owner_commands:
        log.d(f"Owner issued command {infos.message.command}")
        _owner_commands[infos.message.command](infos)
        return True

    return False


def maker_command(infos: Infos):
    if not infos.bot.is_maker:
        return False

    if infos.message.command in _maker_commands:
        log.d(f"{infos.user.uid} issued maker "
              f"command {infos.message.command}")
        _maker_commands[infos.message.command](infos)
        return True

    return False


def maker_master_command(infos: Infos):
    if not infos.user.is_maker_owner:
        return False

    if infos.message.command in _maker_master_commands:
        log.d(f"Maker owner issued command {infos.message.command}")
        _maker_master_commands[infos.message.command](infos)
        return True
    return False


# Move this part to a module
conversions = {
    "+nome+": "{user.name}",
    "+nome2+": "{quote.name}",
    "+gnome+": "{chat.name}"
}


def update_dummies(reply: str) -> str:
    for old_dummy in conversions:
        reply = reply.replace(old_dummy, conversions[old_dummy])
    return reply


def elaborate_dialogs(dialogs: dict, infos: Infos):
    log.d("Elaborating dialogs...")
    mongo_interface.drop_dialogs()

    final_dialogs_list = []

    for section in dialogs:
        if not dialogs[section]:
            continue

        for reply in dialogs[section]:
            n_d = Dialog(update_dummies(reply), section, infos.db.user.language, infos.bot.bot_id)
            print(dict(n_d))
            final_dialogs_list.append(n_d)

    mongo_interface.add_dialogs(final_dialogs_list)
    log.d("Elaborated!")


def elaborate_triggers(triggers: dict, infos: Infos):
    log.d("Elaborating triggers....")
    mongo_interface.drop_triggers()

    final_trigger_list = []

    for t_type in triggers:
        if isinstance(triggers[t_type], str):
            triggers[t_type] = [trigger.replace("_", " ") for trigger in triggers[t_type].split()]

        actual_triggers = triggers[t_type]
        section = None

        if t_type == "equals":
            t_type = "equal"

        elif t_type == "contents":
            t_type = "content"

        elif t_type == "eteractions":
            t_type = "eteraction"

        elif t_type == "interactions":
            t_type = "interaction"

        else:
            if t_type in ["bot_commands", "antispam time", "bot_comm_symbol",
                          "day_parts", "notte", "giorno", "admin_actions"]:
                continue

            section = t_type
            t_type = "interaction"

        for trigger in actual_triggers:
            trigger = update_dummies(trigger)
            n_t = Trigger(t_type, trigger, trigger if not section else section, infos.bot.bot_id, infos.db.user.language, 0)
            print(dict(n_t))
            final_trigger_list.append(n_t)

    mongo_interface.add_triggers(final_trigger_list)
    log.d("Elaborated!")


def elaborate_json_backup(infos: Infos):
    with open("resources/backup.json", "r") as f:
        jts = json.loads(f.read())
        triggers = jts["triggers"]
        dialogs = jts["dialogs"]
        elaborate_triggers(triggers, infos)
        elaborate_dialogs(dialogs, infos)


def decode(key, enc):
    dec = []
    enc = base64.urlsafe_b64decode(enc).decode()
    for i in range(len(enc)):
        key_c = key[i % len(key)]
        dec_c = chr((256 + ord(enc[i]) - ord(key_c)) % 256)
        dec.append(dec_c)
    return "".join(dec)


def elaborate_file(infos: Infos):
    if not infos.user.is_bot_owner:
        return

    if not infos.message.document.file_name.endswith(".kb"):
        return

    log.d("Found a kitsu backup, trying to decrypt it...")
    content = infos.message.document.download()
    jts = json.loads(decode(_backup_password, content))

    with open("resources/backup.json", "w") as f:
        f.write(json.dumps(jts))

    triggers = jts["triggers"]
    dialogs = jts["dialogs"]
    elaborate_triggers(triggers, infos)
    elaborate_dialogs(dialogs, infos)
