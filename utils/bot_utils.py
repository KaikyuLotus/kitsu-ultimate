import re
from typing import Optional

from core.lowlevel import mongo_interface
from entities.dialog import Dialog
from ktelegram import methods

_token_length = 45


def is_bot_token(token: str):
    return isinstance(token, str) and len(token) == _token_length


def download_file(token: str, file_id: str):
    path = methods.get_file(token, file_id).file_path
    return methods.download(token, path)


def get_reply_media_id(reply: str) -> Optional[str]:
    match = re.search(r"{media:(\w{3}),(.+?)(,(.+))?}", reply)
    if match:
        return match.group(2)
    return None


def convert_to_voice_precondition(infos, index, section) -> Optional[Dialog]:
    dialogs = mongo_interface.get_dialogs_of_section(infos.bot.bot_id, section, infos.db.language)
    if index < 0 or index + 1 > len(dialogs):
        infos.reply("Wrong index!")
        return None

    dialog: Dialog = dialogs[index]
    if "aud" in dialog.reply:
        return dialog

    return None


def convert_to_voice(infos, index, section):
    dialog = convert_to_voice_precondition(infos, index, section)
    if not dialog:
        return False
    # Get old ID
    file_id = get_reply_media_id(dialog.reply)
    # Download from Telegram
    f_data = download_file(infos.bot.token, file_id)
    # Send it
    msg = methods.send_voice(infos.bot.token, infos.chat.cid, voice_data=f_data)
    # Save new ID
    new_id = msg["voice"]["file_id"]
    # Delete useless sent message
    methods.delete_message(infos.bot.token, infos.chat.cid, msg["message_id"])
    # Delete old dialog
    mongo_interface.delete_dialog(dialog)
    # Update new media
    dialog.reply = dialog.reply.replace("aud", "voe").replace(file_id, new_id)
    # Add new dialog
    mongo_interface.add_dialog(dialog)
    return True


def handle_add_reply_command(infos, match, section):
    command = match.group(3)
    if command.lower() == "to voice":
        return convert_to_voice(infos, int(match.group(1)) - 1, section)
    # More commands here
    infos.reply("Unknown command.")
    return False


def delete_bot(infos):
    mongo_interface.delete_bot(infos.bot.token)
    mongo_interface.drop_bot_dialogs(infos.bot.bot_id)
    mongo_interface.drop_bot_triggers(infos.bot.bot_id)

