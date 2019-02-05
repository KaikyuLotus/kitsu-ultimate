import re
import time
from typing import Dict

from core import reply_parser
from telegram import methods

maker_owner_id = 487353090


class Infos:
    def __init__(self, bot, update: dict):
        self.time = time.time()
        self.bot = bot

        self.message: Message = None
        self.callback_query: CallbackQuery = None
        self.chat: Chat = None
        self.user: User = None

        self.reply_to: Message = None
        self.to_user: User = None

        self.is_reply = False
        self.is_message = "message" in update
        self.is_callback_query = "callback_query" in update
        self.is_channel_post = "channel_post" in update
        self.is_edited_message = "edited_message" in update
        self.is_edited_channel_post = "edited_channel_post" in update
        self.update_type = None

        if self.is_message:
            self._load_message(update["message"], bot)
            self.update_type = "message"
        elif self.is_callback_query:
            self._load_callback_query(update)
            self._load_message(update["callback_query"]["message"], bot)
            self.user = self.callback_query.user
            self.update_type = "callback"
        elif self.is_channel_post:
            self.update_type = "channel_post"
        elif self.is_edited_message:
            self.update_type = "edited_message"
        elif self.is_edited_channel_post:
            self.update_type = "edited_channel_post"

    def _load_callback_query(self, update):
        self.callback_query = CallbackQuery(update["callback_query"], self.bot)

    def _load_message(self, message, bot):
        self.message = Message(message, bot)
        self.user = User(message["from"], self.bot)
        self.chat = Chat(message["chat"])

        self.is_reply = "reply_to_message" in message

        if self.is_reply:
            quoted_msg = message["reply_to_message"]
            self.reply_to = Message(quoted_msg, bot)
            self.to_user = User(quoted_msg["from"], self.bot)

    def reply(self, text: str,
              parse: bool = True,
              parse_mode: str = "markdown",
              quote: bool = True,
              markup: Dict = None):

        if parse:
            text, quote = reply_parser.parse(text, self)

        methods.send_message(self.bot, self.chat.cid, text,
                             self.message.message_id if quote else None,
                             parse_mode=parse_mode,
                             reply_markup=markup)

    def edit(self, text: str,
             parse_mode: str = "markdown",
             disable_web_page_preview: bool = None,
             reply_markup: str = None,
             parse: bool = True,
             inline: bool = False,
             msg_id: int = None):

        if parse:
            text, quote = reply_parser.parse(text, self)

        inline_msg = None
        if inline:
            inline_msg = self.callback_query.inline_message_id

        chat_id = self.chat.cid if not inline else None

        if not msg_id:
            msg_id = self.message.message_id if not inline else None

        return methods.edit_message_text(self.bot.token, text,
                                         inline_message_id=inline_msg,
                                         message_id=msg_id,
                                         chat_id=chat_id,
                                         parse_mode=parse_mode,
                                         disable_web_page_preview=disable_web_page_preview,
                                         reply_markup=reply_markup)

    def delete_message(self, chat_id: int = None, message_id: int = None):
        if not chat_id:
            chat_id = self.chat.cid

        if not message_id:
            message_id = self.message.message_id

        methods.delete_message(self.bot.token, chat_id=chat_id,
                               message_id=message_id)


class CallbackQuery:
    def __init__(self, callback_query, bot):
        self._token = bot.token
        self.id = callback_query["id"]
        self.user = User(callback_query["from"], bot)
        self.chat_instance = callback_query["chat_instance"]

        # TODO Replace dict defaults ?
        self.inline_message_id = None
        if "inline_message_id" in callback_query:
            self.inline_message_id = callback_query["inline_message_id"]

        self.data = None
        if "data" in callback_query:
            self.data = callback_query["data"]

        self.game_short_name = None
        if "game_short_name" in callback_query:
            self.game_short_name = callback_query["game_short_name"]

    def answer(self, text: str = None,
               show_alert: bool = None,
               url: str = None,
               cache_time: int = None):
        return methods.answer_callback_query(self._token, self.id,
                                             text=text, show_alert=show_alert,
                                             url=url, cache_time=cache_time)


class Chat:
    def __init__(self, chat: dict):
        self.cid = chat["id"]
        self.chat_type = chat["type"]

        self.is_private = self.chat_type == "private"
        self.is_group = self.chat_type == "group"
        self.is_supergroup = self.chat_type == "supergroup"
        self.is_channel = self.chat_type == "channel"


class User:
    def __init__(self, user: dict, bot):
        self.name = user["first_name"]
        self.surname = user["last_name"] if "last_name" in user else None
        self.username = user["username"] if "username" in user else None
        self.uid = user["id"]
        self.is_bot = user["is_bot"]
        self.is_bot_owner = self.uid == bot.owner_id
        self.is_maker_owner = self.uid == maker_owner_id

    def __int__(self):
        return self.uid


class Message:
    def __init__(self, message: dict, bot):
        self.message_id = message["message_id"]

        self.is_text = "text" in message
        self.text = message["text"] if self.is_text else None

        self.is_sticker = "sticker" in message
        self.sticker = Sticker(message["sticker"]) if self.is_sticker else None

        self.is_photo = "photo" in message
        self.photo = "si" if self.is_photo else None

        self.args = []
        self.is_command = False
        self.command = None
        self.is_at_bot = False

        if self.is_text:  # TODO set right regex
            match = re.fullmatch(rf"^/(\w+)(@({bot.username}))?( +(.+))?", self.text, re.I)
            if match:
                self.is_command = True
                self.is_at_bot = True
                self.command = match.group(1)
                if match.group(5):
                    self.args = match.group(5).split()

        if self.text:
            self.what = "text"
        elif self.sticker:
            self.what = "sticker"
        elif self.photo:
            self.what = "photo"
        else:
            self.what = "unknown"


class Sticker:
    def __init__(self, sticker: dict):
        self.stkid = sticker["file_id"]
