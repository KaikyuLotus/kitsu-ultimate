from typing import Callable, List

from core.lowlevel import mongo_interface
from entities.dialog import Dialog
from entities.infos import Infos
from entities.trigger import Trigger
from utils import keyboards


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


def make_sections_list(infos: Infos) -> Callable:
    sections = mongo_interface.get_sections(infos.bot.bot_id)
    res = ""
    i = 1
    for section in sections:
        res += f"{i}] `{section}`\n"
        i += 1
    return res


def make_trigger_list(triggers: List[Trigger]) -> str:
    out = ""
    i = 1
    for trigger in triggers:
        out += f"{i}] `{trigger.trigger}` -> `{trigger.section}`\n"
        i += 1
    return out


def make_dialogs_list(dialogs: List[Dialog]) -> str:
    out = ""
    i = 1
    for dialog in dialogs:
        out += f"{i}] `{dialog.reply}`\n"
        i += 1
    return out


def read_trigger(infos: Infos) -> Callable:
    if infos.is_callback_query:
        if infos.callback_query.data == "done":
            return to_menu(infos)

    new_trigger = infos.message.text
    t_type = infos.bot.waiting_data["type"]
    section = infos.bot.waiting_data["section"]

    t = Trigger(t_type, new_trigger, section, infos.bot.bot_id, "IT")
    mongo_interface.add_trigger(t)

    triggers = mongo_interface.get_triggers_of_type_and_section(
        infos.bot.bot_id, t_type, section,
    )

    msg = "Now send the triggers as replies."
    if triggers:
        triggs = make_trigger_list(triggers)
        msg = f"Triggers of type `{t_type}` in section `{section}`:\n{triggs}\n" + msg

    infos.edit(msg,
               msg_id=infos.bot.waiting_data["msg"].message_id,
               reply_markup=keyboards.done())

    return read_trigger


def select_trigger_type(infos: Infos):
    if infos.callback_query.data == "interaction":
        sel_type = "interaction"
    elif infos.callback_query.data == "content":
        sel_type = "content"
    elif infos.callback_query.data == "eteraction":
        sel_type = "eteraction"
    elif infos.callback_query.data == "equal":
        sel_type = "equal"
    else:
        infos.callback_query.answer("What...?")
        sel_type = None

    return sel_type


def wait_del_trigger_index(infos: Infos) -> Callable:
    if infos.is_callback_query:
        if infos.callback_query.data == "done":
            return to_menu(infos)

    try:
        index = int(infos.message.text)
    except ValueError:
        infos.reply(f"{infos.message.text} is not a valid index.")
        return wait_del_trigger_index

    sel_type = infos.bot.waiting_data["type"]
    triggers = mongo_interface.get_triggers_of_type(infos.bot.bot_id, sel_type)

    if index < 1:
        infos.reply("Index can't be lesser than one.")
        return wait_del_trigger_index

    if index - 1 > len(triggers):
        infos.reply(f"{index} is too high, max: {len(triggers)}")
        return wait_del_trigger_index

    trigger = triggers[index - 1]
    triggers.remove(trigger)
    mongo_interface.delete_trigger(trigger)

    if not triggers:
        return to_menu(infos, f"No more triggers of type {sel_type}\n"
        f"Do you need something else?")

    triggs = make_trigger_list(triggers)

    infos.edit(f"Trigger of type `{sel_type}`:\n"
               f"{triggs}\n"
               "Please send the number of the trigger to delete",
               msg_id=infos.bot.waiting_data["msg"].message_id,
               reply_markup=keyboards.done())

    return wait_del_trigger_index


def wait_trigger_type_del_trigger(infos: Infos) -> Callable:
    if not infos.is_callback_query:
        return wait_trigger_type_del_trigger

    sel_type = select_trigger_type(infos)
    if not sel_type:
        return wait_trigger_type_del_trigger

    infos.bot.waiting_data["type"] = sel_type

    triggers = mongo_interface.get_triggers_of_type(infos.bot.bot_id, sel_type)

    if not triggers:
        return to_menu(infos, f"No triggers of type {sel_type}.\n"
        f"Do you need something else?")

    triggs = make_trigger_list(triggers)

    infos.edit(f"Trigger of type `{sel_type}`:\n"
               f"{triggs}\n"
               "Please send the number of the trigger to delete",
               msg_id=infos.bot.waiting_data["msg"].message_id,
               reply_markup=keyboards.done())

    return wait_del_trigger_index


def wait_trigger_type_add_reply(infos: Infos) -> Callable:
    if not infos.is_callback_query:
        return wait_trigger_type_add_reply

    sel_type = select_trigger_type(infos)
    if not sel_type:
        return wait_trigger_type_add_reply

    section = infos.bot.waiting_data["section"]
    triggers = mongo_interface.get_triggers_of_type_and_section(
        infos.bot.bot_id, sel_type, section
    )
    triggs = make_trigger_list(triggers)

    infos.bot.waiting_data["type"] = sel_type
    infos.edit(f"Trigger of type `{sel_type}` in section `{section}`:\n"
               f"{triggs}\n"
               "Now send the triggers as replies.",
               msg_id=infos.bot.waiting_data["msg"].message_id,
               reply_markup=keyboards.done())

    return read_trigger


def add_trigger(infos: Infos) -> Callable:
    if not infos.is_message:
        return add_trigger

    infos.bot.waiting_data["section"] = infos.message.text
    infos.edit("Please now select the trigger type",
               msg_id=infos.bot.waiting_data["msg"].message_id,
               reply_markup=keyboards.trigger_type())

    return wait_trigger_type_add_reply


def list_triggers(infos: Infos) -> Callable:
    sect = infos.message.text
    triggers = mongo_interface.get_triggers_of_section(infos.bot.bot_id, sect)
    trigs = make_trigger_list(triggers)
    msg = f"Triggers for section `{sect}`:\n{trigs}"
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
    else:
        infos.callback_query.answer("What...?")
        return menu_triggers

    infos.edit(msg, msg_id=infos.bot.waiting_data["msg"].message_id,
               reply_markup=markup)
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

    section = infos.bot.waiting_data["section"]

    dialog = Dialog(reply, section, "IT", infos.bot.bot_id)
    mongo_interface.add_dialog(dialog)
    dialogs = mongo_interface.get_dialogs_of_section(infos.bot.bot_id, section)

    # Final message to append
    f_msg = "Please send the replies you want!"

    if not dialogs:
        msg = f"No dialogs for section `{section}`\n{f_msg}"
    else:
        dials = make_dialogs_list(dialogs)
        msg = f"Dialogs for section `{section}`:\n{dials}\n{f_msg}"

    infos.edit(msg,
               reply_markup=keyboards.done(),
               msg_id=infos.bot.waiting_data["msg"].message_id)

    return wait_del_dialog_reply


def add_dialog(infos: Infos) -> Callable:
    # Waiting for a message (section)
    if not infos.is_message:
        return list_dialogs

    section = infos.message.text
    infos.bot.waiting_data["section"] = section

    dialogs = mongo_interface.get_dialogs_of_section(infos.bot.bot_id, section)

    # Final message to append
    f_msg = "Please send the replies you want!"

    if not dialogs:
        msg = f"No dialogs for section `{section}`\n{f_msg}"
    else:
        dials = make_dialogs_list(dialogs)
        msg = f"Dialogs for section `{section}`:\n{dials}\n{f_msg}"

    infos.edit(msg,
               reply_markup=keyboards.done(),
               msg_id=infos.bot.waiting_data["msg"].message_id)

    return wait_del_dialog_reply


def wait_del_dialog_number(infos: Infos) -> Callable:
    if infos.is_callback_query:
        if infos.callback_query.data == "done":
            return to_menu(infos)

    try:
        index = int(infos.message.text)
    except ValueError:
        infos.reply(f"`{infos.message.text}` is not a valid number.")
        return wait_del_dialog_number

    if index <= 0:
        infos.reply("The minimum index is 1!")
        return wait_del_dialog_number

    section = infos.bot.waiting_data["section"]
    dialogs = mongo_interface.get_dialogs_of_section(infos.bot.bot_id, section)

    if index - 1 > len(dialogs):
        infos.reply(f"You've selected dialog n°{index} but "
                    f"there are only {len(dialogs) + 1} dialogs")
        return wait_del_dialog_number

    dialog = dialogs[index - 1]
    mongo_interface.delete_dialog(dialog)
    dialogs.remove(dialog)

    if not dialogs:
        msg = f"No dialogs for section `{section}`\nDo you need something else?"
        return to_menu(infos, msg)

    infos.edit(f"Dialogs for section `{section}`:\n{make_dialogs_list(dialogs)}"
               f"\n\nPlease send the number of the dialog you want to delete.",
               reply_markup=keyboards.done(),
               msg_id=infos.bot.waiting_data["msg"].message_id)

    return wait_del_dialog_number


def del_dialog(infos: Infos) -> Callable:
    # Waiting for a message (section)
    if not infos.is_message:
        return list_dialogs

    section = infos.message.text
    dialogs = mongo_interface.get_dialogs_of_section(infos.bot.bot_id, section)

    # Final message to append
    f_msg = "Please send the number of the dialog you want to delete."

    if not dialogs:
        msg = f"No dialogs for section `{section}`\nDo you need something else?"
        return to_menu(infos, msg)

    dials = make_dialogs_list(dialogs)
    msg = f"Dialogs for section `{section}`:\n{dials}\n\n{f_msg}"

    infos.edit(msg,
               reply_markup=keyboards.done(),
               msg_id=infos.bot.waiting_data["msg"].message_id)

    infos.bot.waiting_data["section"] = section
    return wait_del_dialog_number


def list_dialogs(infos: Infos) -> Callable:
    # Waiting for a message (section)
    if not infos.is_message:
        return list_dialogs

    section = infos.message.text
    dialogs = mongo_interface.get_dialogs_of_section(infos.bot.bot_id, section)

    # Final message to append
    f_msg = "Do you need something else, {user.name}?"

    if not dialogs:
        msg = f"No dialogs for section `{section}`\n\n{f_msg}"
    else:
        dials = make_dialogs_list(dialogs)
        msg = f"Dialogs for section `{section}`:\n{dials}\n\n{f_msg}"

    return to_menu(infos, msg)


def menu_dialogs(infos: Infos):
    if not infos.is_callback_query:
        return menu_triggers

    if infos.callback_query.data == "add_dialog":
        fun = add_dialog
        msg = "Please now send the dialog section"
    elif infos.callback_query.data == "del_dialog":
        fun = del_dialog
        msg = "Please now send the dialog section"
    elif infos.callback_query.data == "list_dialogs":
        fun = list_dialogs
        msg = "Please now send the dialog section"
    else:
        infos.callback_query.answer("What...?")
        return menu_dialogs

    infos.edit(msg, msg_id=infos.bot.waiting_data["msg"].message_id)
    return fun


def menu_choice(infos: Infos) -> Callable:
    if not infos.is_callback_query:
        return menu_choice

    infos.bot.waiting_data["msg"] = infos.message

    if infos.callback_query.data == "menu_dialogs":
        infos.edit(f"Please choose an option",
                   reply_markup=keyboards.menu_dialogs())
        return menu_dialogs

    if infos.callback_query.data == "menu_triggers":
        infos.edit(f"Please choose an option",
                   reply_markup=keyboards.menu_triggers())
        return menu_triggers

    if infos.callback_query.data == "menu_get_sections":
        infos.edit(f"Sections:\n{make_sections_list(infos)}")
        return

    if infos.callback_query.data == "menu_close":
        infos.delete_message(infos.chat.cid, infos.message.message_id)
        return

    infos.callback_query.answer("What...?")
    return menu_choice


def menu(infos: Infos) -> Callable:
    infos.reply("Welcome {user.name}, what do you need?", markup=keyboards.menu())
    return menu_choice


def to_menu(infos: Infos, msg=None) -> Callable:
    infos.edit("Do you need something else" if not msg else msg,
               reply_markup=keyboards.menu(),
               msg_id=infos.bot.waiting_data["msg"].message_id)
    # Reset waiting_data
    infos.bot.cancel_wait()
    return menu_choice
