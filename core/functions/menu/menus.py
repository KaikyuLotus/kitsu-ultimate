import re
from typing import Callable, List, Optional

from core.functions.menu.vars import media_types, trigger_type_list
from core.lowlevel import mongo_interface
from entities.dialog import Dialog
from entities.infos import Infos
from entities.trigger import Trigger
from utils import keyboards, regex_utils


# FLOW
# menu |->  dialogs  ->| add dialog   -> inp. section -> inp. dialog
#      |               | del dialog   -> inp. section -> inp. number <- [loop]
#      |<--------------------------------------------- done
#      |               | list dialogs -> inp. section ->|
#      |<-----------------------------------------------|
#      |<--------------| back
#      |
#      |->  triggers ->| add trigger
#      |               | del trigger
#      |               | list triggers
#      |<--------------| back
#      |
#      |->  sections ->| list sections ->|
#      |<--------------------------------|
#      |
#      |->  close    ->| <del message>


# TODO change section message layout?
def make_sections_list(infos: Infos) -> Callable:
    sections = mongo_interface.get_sections(infos.bot.bot_id, infos.db.language)
    res = ""
    i = 1
    bid = infos.bot.bot_id
    for section in sections:
        d_count = len(mongo_interface.get_dialogs_of_section(bid, section, infos.db.language))
        t_count = len(mongo_interface.get_triggers_of_section(bid, section, infos.db.language))
        res += f"{i}] `{section}`\n  Triggers: `{t_count}` - Dialogs: `{d_count}`\n"
        i += 1
    return res


def make_trigger_list(triggers: List[Trigger]) -> str:
    out = ""
    i = 1
    for trigger in triggers:
        out += f"{i}] `{trigger.trigger}` -> `{trigger.section}` ({trigger.usages} usages)\n"
        i += 1
    return out


def check_reply_media(reply: str) -> str:
    match = re.search(r"{media:(\w{3}),(.+?)(,(.+))?}", reply)
    if match:
        media_type = match.group(1)
        media_id = match.group(2)
        caption = match.group(4)
        nice_media_type = media_types[media_type]
        reply = f"{nice_media_type}: `{media_id}`"
        if caption:
            reply += f"\nCaption: `{caption}`"
        return reply + "\n"
    return f"`{reply}`"


def make_dialogs_list(dialogs: List[Dialog]) -> str:
    out = ""
    i = 1
    for dialog in dialogs:
        out += f"{i}] {check_reply_media(dialog.reply)} [{dialog.probability}%] ({dialog.usages} usages)\n"
        i += 1
    return out


def read_trigger(infos: Infos) -> Callable:
    if infos.is_callback_query:
        if infos.callback_query.data == "done":
            return to_menu(infos)

    new_trigger = infos.message.text
    t_type = infos.bot.waiting_data["type"]
    section = infos.bot.waiting_data["section"]

    t = Trigger(t_type, new_trigger, section, infos.bot.bot_id, infos.db.language)
    mongo_interface.add_trigger(t)

    triggers = mongo_interface.get_triggers_of_type_and_section(
        infos.bot.bot_id, t_type, section, infos.db.language
    )

    msg = "Now send the triggers as replies."
    if triggers:
        triggs = make_trigger_list(triggers)
        msg = f"[md]Triggers of type `{t_type}` in section `{section}`:\n{triggs}\n" + msg

    infos.edit(msg,
               msg_id=infos.bot.waiting_data["msg"].message_id,
               reply_markup=keyboards.done(),
               parse=False)

    return read_trigger


def select_trigger_type(infos: Infos):
    if infos.callback_query.data not in trigger_type_list:
        infos.callback_query.answer("What...?")
        sel_type = None
    else:
        sel_type = infos.callback_query.data

    return sel_type


def wait_del_trigger_index(infos: Infos) -> Callable:
    if infos.is_callback_query:
        if infos.callback_query.data == "done":
            return to_menu(infos)

    to_remove: List[Trigger] = []

    sel_type = infos.bot.waiting_data["type"]
    triggers = mongo_interface.get_triggers_of_type(infos.bot.bot_id, sel_type, infos.db.language)

    indexes: List[str] = infos.message.text.split("," if "," in infos.message.text else " ")
    for stringIndex in indexes:
        try:
            index = int(stringIndex.strip())
        except ValueError:
            infos.reply(f"{infos.message.text} is not a valid index.")
            return wait_del_trigger_index

        if index < 1:
            infos.reply("Index can't be lesser than one.")
            return wait_del_trigger_index

        if index - 1 > len(triggers):
            infos.reply(f"{index} is too high, max: {len(triggers)}")
            return wait_del_trigger_index

        trigger = triggers[index - 1]
        to_remove.append(trigger)

    for trigger in to_remove:
        triggers.remove(trigger)
        mongo_interface.delete_trigger(trigger)

    if not triggers:
        return to_menu(infos, f"No more triggers of type {sel_type}\n"
        f"Do you need something else?")

    triggs = make_trigger_list(triggers)

    infos.edit(f"[md]Trigger of type `{sel_type}`:\n"
               f"{triggs}\n"
               "Please send the number of the trigger to delete",
               msg_id=infos.bot.waiting_data["msg"].message_id,
               reply_markup=keyboards.done(),
               parse=False)

    return wait_del_trigger_index


def wait_trigger_type_del_trigger(infos: Infos) -> Callable:
    if not infos.is_callback_query:
        return wait_trigger_type_del_trigger

    sel_type = select_trigger_type(infos)
    if not sel_type:
        return wait_trigger_type_del_trigger

    infos.bot.waiting_data["type"] = sel_type

    triggers = mongo_interface.get_triggers_of_type(infos.bot.bot_id, sel_type, infos.db.language)

    if not triggers:
        return to_menu(infos, f"No triggers of type {sel_type}.\n"
                              "Do you need something else?")

    triggs = make_trigger_list(triggers)

    infos.edit(f"[md]Trigger of type `{sel_type}`:\n"
               f"{triggs}\n"
               "Please send the number of the trigger to delete",
               msg_id=infos.bot.waiting_data["msg"].message_id,
               reply_markup=keyboards.done(),
               parse=False)

    return wait_del_trigger_index


def wait_trigger_type_add_reply(infos: Infos) -> Callable:
    if not infos.is_callback_query:
        return wait_trigger_type_add_reply

    if infos.callback_query.data == "cancel":
        return to_menu(infos, f"Operation cancelled, do you need something else, {infos.user.name}?")

    sel_type = select_trigger_type(infos)
    if not sel_type:
        return wait_trigger_type_add_reply

    section = infos.bot.waiting_data["section"]
    triggers = mongo_interface.get_triggers_of_type_and_section(
        infos.bot.bot_id, sel_type, section, infos.db.language
    )
    triggs = make_trigger_list(triggers)

    infos.bot.waiting_data["type"] = sel_type
    infos.edit(f"[md]Trigger of type `{sel_type}` in section `{section}`:\n"
               f"{triggs}\n"
               "Now send the triggers as replies.",
               msg_id=infos.bot.waiting_data["msg"].message_id,
               reply_markup=keyboards.done(),
               parse=False)

    return read_trigger


def add_trigger(infos: Infos) -> Callable:
    if not infos.is_message:
        return add_trigger

    if not infos.message.is_text:
        return add_trigger

    infos.bot.waiting_data["section"] = infos.message.text
    infos.edit("Please now select the trigger type",
               msg_id=infos.bot.waiting_data["msg"].message_id,
               reply_markup=keyboards.trigger_type(),
               parse=False)

    return wait_trigger_type_add_reply


def list_triggers(infos: Infos) -> Callable:
    if not infos.is_message:
        return list_triggers

    if not infos.message.is_text:
        return list_triggers

    sect = infos.message.text
    triggers = mongo_interface.get_triggers_of_section(infos.bot.bot_id, sect, infos.db.language)
    trigs = make_trigger_list(triggers)
    msg = f"[md]Triggers for section `{sect}`:\n{trigs}"
    return to_menu(infos, msg)


def del_trigger(infos: Infos) -> Callable:
    return to_menu(infos)


def menu_triggers(infos: Infos) -> Callable:
    if not infos.is_callback_query:
        return menu_triggers

    markup = None
    if infos.callback_query.data == "add_trigger":
        fun = add_trigger
        msg = "Please now send the dialog section"
    elif infos.callback_query.data == "del_trigger":
        fun = wait_trigger_type_del_trigger
        markup = keyboards.trigger_type()
        msg = "Please select the trigger section."
    elif infos.callback_query.data == "list_triggers":
        fun = list_triggers
        msg = "Please now send the trigger section"
    elif infos.callback_query.data == "menu_back":
        fun = menu_choice
        msg = f"Welcome {infos.user.name}, what do you need?"
        markup = keyboards.menu()
    else:
        infos.callback_query.answer("What...?")
        return menu_triggers

    infos.edit(msg,
               msg_id=infos.bot.waiting_data["msg"].message_id,
               reply_markup=markup,
               parse=False)
    return fun


def wait_del_dialog_reply(infos: Infos) -> Callable:
    # Here we can handle both text and callbacks
    if infos.is_callback_query:
        if infos.callback_query.data == "done":
            return to_menu(infos)

    if infos.message.is_sticker:
        reply = "{media:stk," + infos.message.sticker.stkid + "}"
    elif infos.message.is_photo:
        reply = "{media:pht," + infos.message.photo.phtid
        if infos.message.photo.caption:
            reply += "," + infos.message.photo.caption + "}"
        else:
            reply += "}"
    elif infos.message.is_audio:
        reply = "{media:aud," + infos.message.audio.audid + "}"
    elif infos.message.is_voice:
        reply = "{media:voe," + infos.message.voice.voiceid + "}"
    elif infos.message.is_document:
        reply = "{media:doc," + infos.message.document.docid + "}"
    elif infos.message.is_text:
        reply = infos.message.text
    else:
        infos.reply("Unsupported.")
        return wait_del_dialog_reply

    probability, reply = regex_utils.get_dialog_probability(reply)
    if probability is None:
        probability = 100

    section = infos.bot.waiting_data["section"]

    dialog = Dialog(reply, section, infos.db.language, infos.bot.bot_id, 0, probability)
    mongo_interface.add_dialog(dialog)
    dialogs = mongo_interface.get_dialogs_of_section(infos.bot.bot_id, section, infos.db.language)

    # Final message to append
    f_msg = "Please send the replies you want!"

    if not dialogs:
        msg = f"[md]No dialogs for section `{section}`\n{f_msg}"
    else:
        dials = make_dialogs_list(dialogs)
        msg = f"[md]Dialogs for section `{section}`:\n{dials}\n{f_msg}"

    infos.edit(msg,
               reply_markup=keyboards.done(),
               msg_id=infos.bot.waiting_data["msg"].message_id,
               parse=False)

    return wait_del_dialog_reply


def add_dialog(infos: Infos) -> Callable:
    # Waiting for a message (section)
    if not infos.is_message:
        return list_dialogs

    if not infos.message.is_text:
        return add_dialog

    section = infos.message.text
    infos.bot.waiting_data["section"] = section

    dialogs = mongo_interface.get_dialogs_of_section(infos.bot.bot_id, section, infos.db.language)

    # Final message to append
    f_msg = "Please send the replies you want!"

    if not dialogs:
        msg = f"[md]No dialogs for section `{section}`\n{f_msg}"
    else:
        dials = make_dialogs_list(dialogs)
        msg = f"[md]Dialogs for section `{section}`:\n{dials}\n{f_msg}"

    infos.edit(msg,
               reply_markup=keyboards.done(),
               msg_id=infos.bot.waiting_data["msg"].message_id,
               parse=False)

    return wait_del_dialog_reply


def wait_del_dialog_number(infos: Infos) -> Callable:
    if infos.is_callback_query:
        if infos.callback_query.data == "done":
            return to_menu(infos)

    to_delete: List[Dialog] = []

    section = infos.bot.waiting_data["section"]
    dialogs = mongo_interface.get_dialogs_of_section(infos.bot.bot_id, section, infos.db.language)

    indexes: List[str] = infos.message.text.split("," if "," in infos.message.text else " ")

    for string_index in indexes:
        try:
            string_index = string_index.strip()
            index = int(string_index)
        except ValueError:
            infos.reply(f"[md]`{string_index}` is not a valid number.")
            return wait_del_dialog_number

        if index <= 0:
            infos.reply("The minimum index is 1!")
            return wait_del_dialog_number

        if index - 1 > len(dialogs):
            infos.reply(f"You've selected dialog n°{index} but "
                        f"there are only {len(dialogs) + 1} dialogs")
            return wait_del_dialog_number

        dialog = dialogs[index - 1]
        to_delete.append(dialog)

    for dialog in to_delete:
        mongo_interface.delete_dialog(dialog)
        dialogs.remove(dialog)

    if not dialogs:
        msg = f"[md]No more dialogs for section `{section}`\nDo you need something else?"
        return to_menu(infos, msg)

    infos.edit(f"[md]Dialogs for section `{section}`:\n{make_dialogs_list(dialogs)}"
               f"\n\nPlease send the number of the dialog you want to delete.",
               reply_markup=keyboards.done(),
               msg_id=infos.bot.waiting_data["msg"].message_id,
               parse=False)

    return wait_del_dialog_number


def del_dialog(infos: Infos) -> Callable:
    # Waiting for a message (section)
    if not infos.is_message:
        return del_dialog

    if not infos.message.is_text:
        return del_dialog

    section = infos.message.text
    dialogs = mongo_interface.get_dialogs_of_section(infos.bot.bot_id, section, infos.db.language)

    # Final message to append
    f_msg = "Please send the number of the dialog you want to delete."

    if not dialogs:
        msg = f"[md]No dialogs for section `{section}`\nDo you need something else?"
        return to_menu(infos, msg)

    dials = make_dialogs_list(dialogs)
    msg = f"[md]Dialogs for section `{section}`:\n{dials}\n\n{f_msg}"

    infos.edit(msg,
               reply_markup=keyboards.done(),
               msg_id=infos.bot.waiting_data["msg"].message_id,
               parse=False)

    infos.bot.waiting_data["section"] = section
    return wait_del_dialog_number


def list_dialogs(infos: Infos) -> Callable:
    # Waiting for a message (section)
    if not infos.is_message:
        return list_dialogs

    if not infos.message.is_text:
        return list_dialogs

    section = infos.message.text
    dialogs = mongo_interface.get_dialogs_of_section(infos.bot.bot_id, section, infos.db.language)

    # Final message to append
    f_msg = f"Do you need something else, {infos.user.name}?"

    if not dialogs:
        msg = f"[md]No dialogs for section `{section}`\n\n{f_msg}"
    else:
        dials = make_dialogs_list(dialogs)
        msg = f"[md]Dialogs for section `{section}`:\n{dials}\n\n{f_msg}"

    return to_menu(infos, msg)


def menu_dialogs(infos: Infos):
    if not infos.is_callback_query:
        return menu_triggers

    markup = None

    if infos.callback_query.data == "add_dialog":
        fun = add_dialog
        msg = "Please now send the dialog section"
    elif infos.callback_query.data == "del_dialog":
        fun = del_dialog
        msg = "Please now send the dialog section"
    elif infos.callback_query.data == "list_dialogs":
        fun = list_dialogs
        msg = "Please now send the dialog section"
    elif infos.callback_query.data == "menu_back":
        fun = menu_choice
        msg = f"Welcome {infos.user.name}, what do you need?"
        markup = keyboards.menu()
    else:
        infos.callback_query.answer("What...?")
        return menu_dialogs

    infos.edit(msg, msg_id=infos.bot.waiting_data["msg"].message_id,
               reply_markup=markup,
               parse=False)
    return fun


def wait_del_section_number(infos: Infos) -> Callable:
    if infos.is_callback_query:
        if infos.callback_query.data == "done":
            return to_menu(infos)

    to_delete: List[str] = []

    sections = mongo_interface.get_sections(infos.bot.bot_id, infos.db.language)

    indexes: List[str] = infos.message.text.split("," if "," in infos.message.text else " ")

    for string_index in indexes:
        try:
            string_index = string_index.strip()
            index = int(string_index)
        except ValueError:
            infos.reply(f"`{string_index}` is not a valid number.")
            return wait_del_section_number

        if index <= 0:
            infos.reply("The minimum index is 1!")
            return wait_del_section_number

        if index - 1 > len(sections):
            infos.reply(f"You've selected section n°{index} but "
                        f"there are only {len(sections) + 1} sections")
            return wait_del_section_number

        section = sections[index - 1]
        to_delete.append(section)

    for section in to_delete:
        mongo_interface.delete_dialogs_of_section(infos.bot.bot_id, section, infos.db.language)
        mongo_interface.delete_triggers_of_section(infos.bot.bot_id, section, infos.db.language)
        sections.remove(section)

    if not sections:
        msg = f"I don't have anymore sections\nDo you need something else?"
        return to_menu(infos, msg)

    infos.edit(f"[md]Current sections:\n{make_sections_list(infos)}"
               f"\n\nPlease send the number of the section you want to delete.\n"
               f"*Remember that deleting a section means deleting every dialog/trigger linked to it!!*",
               reply_markup=keyboards.done(),
               msg_id=infos.bot.waiting_data["msg"].message_id,
               parse=False)

    return wait_del_section_number


def del_section(infos: Infos) -> Callable:
    # Waiting for a message (section)
    if not infos.is_callback_query:
        return del_section

    sections = mongo_interface.get_sections(infos.bot.bot_id, infos.db.language)

    if not sections:
        msg = f"I don't have any section\nDo you need something else?"
        return to_menu(infos, msg)

    msg = f"[md]Here's the list of my sections:\n" \
            f"\n{make_sections_list(infos)}\n" \
            f"\nPlease now send the section to delete\n" \
            f"*Remember that deleting a sections means deleting every message/trigger linked to it!!*"

    infos.edit(msg,
               reply_markup=keyboards.done(),
               msg_id=infos.bot.waiting_data["msg"].message_id,
               parse=False)

    return wait_del_section_number


def menu_wait_command_symbol(infos: Infos):
    if infos.is_callback_query:
        if infos.callback_query.data == "cancel":
            return to_menu(infos, "Operation cancelled\nDo you need something else?")

    if len(infos.message.text) != 1:
        infos.edit("Invalid symbol specified!\nPlease send just a symbol",
                   msg_id=infos.bot.waiting_data["msg"].message_id,
                   reply_markup=keyboards.cancel(),
                   parse=False)
        return menu_wait_command_symbol

    infos.bot.custom_command_symb = infos.message.text
    mongo_interface.update_bot(infos.bot.token, infos.bot)

    infos.edit(f"You want to edit some options, master?",
               msg_id=infos.bot.waiting_data["msg"].message_id,
               reply_markup=keyboards.menu_options(infos.bot),
               parse=False)
    return menu_options


def menu_options(infos: Infos):
    if not infos.is_callback_query:
        return menu_options

    if infos.callback_query.data == "options_autom":
        infos.bot.automs_enabled = not infos.bot.automs_enabled
        mongo_interface.update_bot(infos.bot.token, infos.bot)
        infos.edit("Option changed!",
                   reply_markup=keyboards.menu_options(infos.bot),
                   parse=False)
        return menu_options

    if infos.callback_query.data == "options_comm_symbol":
        infos.edit("Please send a custom command symbol",
                   reply_markup=keyboards.cancel(),
                   parse=False)
        return menu_wait_command_symbol

    if infos.callback_query.data == "options_back":
        return to_menu(infos)

    return menu_options


def menu_sections(infos: Infos):
    if not infos.is_callback_query:
        return menu_triggers

    if infos.callback_query.data == "del_section":
        return del_section(infos)
    elif infos.callback_query.data == "list_sections":
        fun = menu_choice
        msg = f"[md]{make_sections_list(infos)}\n" \
            f"Do you need something else, {infos.user.name}?"
        markup = keyboards.menu()
    elif infos.callback_query.data == "menu_back":
        fun = menu_choice
        msg = f"Welcome {infos.user.name}, what do you need?"
        markup = keyboards.menu()
    else:
        infos.callback_query.answer("What...?")
        return menu_dialogs

    infos.edit(msg,
               msg_id=infos.bot.waiting_data["msg"].message_id,
               reply_markup=markup,
               parse=False)
    return fun


def menu_choice(infos: Infos) -> Optional[Callable]:
    if not infos.is_callback_query:
        return menu_choice

    infos.bot.waiting_data["msg"] = infos.message

    if infos.callback_query.data == "menu_dialogs":
        infos.edit(f"Please choose an option",
                   reply_markup=keyboards.menu_dialogs(),
                   parse=False)
        return menu_dialogs

    if infos.callback_query.data == "menu_triggers":
        infos.edit(f"Please choose an option",
                   reply_markup=keyboards.menu_triggers(),
                   parse=False)
        return menu_triggers

    if infos.callback_query.data == "menu_sections":
        infos.edit(f"Please choose an option",
                   reply_markup=keyboards.menu_sections(),
                   parse=False)
        return menu_sections

    if infos.callback_query.data == "menu_options":
        infos.edit(f"You want to edit some options, master?",
                   reply_markup=keyboards.menu_options(infos.bot),
                   parse=False)
        return menu_options

    if infos.callback_query.data == "menu_close":
        infos.delete_message(infos.chat.cid, infos.message.message_id)
        return

    infos.callback_query.answer("What...?")
    return menu_choice


def menu(infos: Infos) -> Callable:
    infos.reply(f"Welcome {infos.user.name}, what do you need?", markup=keyboards.menu())
    return menu_choice


def to_menu(infos: Infos, msg=None) -> Callable:
    infos.edit("Do you need something else" if not msg else msg,
               reply_markup=keyboards.menu(),
               msg_id=infos.bot.waiting_data["msg"].message_id,
               parse=False)
    # Reset waiting_data
    infos.bot.cancel_wait()

    return menu_choice
