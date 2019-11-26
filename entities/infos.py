import re
import time
from typing import Dict, Optional

from configuration.config import config
from core import reply_parser
from ktelegram import methods
from core.lowlevel import mongo_interface
from entities import user, group
from exceptions.bad_request import BadRequest

_maker_owner_id = config["defaults"]["owner"]["id"]
_default_language = config["defaults"]["language"]


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
        self.is_reply_to_this_bot = False
        self.is_message = "message" in update
        self.is_callback_query = "callback_query" in update
        self.is_channel_post = "channel_post" in update
        self.is_edited_message = "edited_message" in update
        self.is_edited_channel_post = "edited_channel_post" in update
        self.update_type = None

        if self.is_edited_message:
            update["message"] = update["edited_message"]
            del update["edited_message"]

        if self.is_message or self.is_edited_message:
            # Workaround for edited messages
            self._load_message(update["message"], bot)
            self.update_type = "message" if self.is_message else "edited_message"
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

        gid = None
        if self.chat and not self.chat.is_channel and not self.chat.is_private:
            gid = self.chat.cid

        uid = None
        if self.user:
            uid = self.user.uid

        quoted = None
        if self.to_user:
            quoted = self.to_user.uid

        self.db = DB(self.bot.bot_id, gid, uid, quoted, self.chat.is_private if self.chat else False)
        self.is_to_bot = (self.is_reply and self.to_user.is_this_bot if self.to_user else False) or self.chat.is_private

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
              parse_mode: Optional[str] = "markdown",
              markup: Dict = None):

        if parse:
            return reply_parser.execute(text, self, markup=markup)
        return methods.send_message(self.bot.token, self.chat.cid, text, parse_mode=parse_mode, reply_markup=markup)

    def edit(self, text: str,
             parse_mode: str = "markdown",
             disable_web_page_preview: bool = None,
             reply_markup: str = None,
             parse: bool = True,
             inline: bool = False,
             msg_id: int = None,
             force_markdown: bool = False):

        text, quote, nolink, markdown, markup = reply_parser.parse(text, self, not parse)

        if not disable_web_page_preview and nolink:
            disable_web_page_preview = nolink

        if not reply_markup and markup:
            reply_markup = markup

        inline_msg = None
        if inline:
            inline_msg = self.callback_query.inline_message_id

        chat_id = self.chat.cid if not inline else None

        if not msg_id:
            msg_id = self.message.message_id if not inline else None

        if force_markdown:
            markdown = True

        try:
            return methods.edit_message_text(self.bot.token, text,
                                             inline_message_id=inline_msg,
                                             message_id=msg_id,
                                             chat_id=chat_id,
                                             parse_mode=parse_mode if markdown else None,
                                             disable_web_page_preview=disable_web_page_preview,
                                             reply_markup=reply_markup)
        except BadRequest:
            return methods.edit_message_text(self.bot.token,
                                             "Sorry, message was too long, don't try again!",
                                             inline_message_id=inline_msg,
                                             message_id=msg_id,
                                             chat_id=chat_id)

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
        self.name = chat["title"] if "title" in chat else chat["first_name"]

        self.is_private = self.chat_type == "private"
        self.is_group = self.chat_type == "group"
        self.is_supergroup = self.chat_type == "supergroup"
        self.is_channel = self.chat_type == "channel"


class User:
    def __init__(self, usr: dict, bot):
        self.name = usr["first_name"]
        self.surname = usr["last_name"] if "last_name" in usr else None
        self.username = usr["username"] if "username" in usr else None
        self.language_code = usr["language_code"] if "language_code" in usr else None

        self.uid = usr["id"]
        self.is_bot = usr["is_bot"]
        self.is_this_bot = self.uid == bot.bot_id
        self.is_bot_owner = self.uid == bot.owner_id
        self.is_maker_owner = self.uid == _maker_owner_id

    def __int__(self):
        return self.uid


class Message:
    def __init__(self, message: dict, bot):

        self.text = None
        self.sticker = None
        self.photo = None
        self.audio = None
        self.document = None

        self.message_id = message["message_id"]

        self.is_text = "text" in message
        if self.is_text:
            self.text = message["text"]

        self.is_sticker = "sticker" in message
        if self.is_sticker:
            self.sticker = Sticker(message["sticker"])

        self.is_photo = "photo" in message
        if self.is_photo:
            caption = message["caption"] if "caption" in message else None
            self.photo = Photo(message["photo"], caption)

        self.is_audio = "audio" in message
        if self.is_audio:
            self.audio = Audio(message["audio"])

        self.is_voice = "voice" in message
        if self.is_voice:
            self.voice = Voice(message["voice"])

        self.is_document = "document" in message
        if self.is_document:
            self.document = Document(message["document"], bot.token)

        self.args = []
        self.is_command = False
        self.command = None
        self.is_at_bot = False

        if self.is_text:  # TODO set right regex?
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


class Document:
    def __init__(self, document: dict, token: str):
        self.token = token
        self.file_name = document["file_name"] if "file_name" in document else "name"
        self.mime_type = document["mime_type"] if "mime_type" in document else "mime"
        self.file_size = document["file_size"] if "file_size" in document else 0
        self.docid = document["file_id"]

    def download(self):
        path = methods.get_file(self.token, self.docid).file_path
        return methods.download(self.token, path)


class Voice:
    def __init__(self, voice: dict):
        self.voiceid = voice["file_id"]
        self.duration = voice["duration"]
        self.mime_type = voice["mime_type"]
        self.file_size = voice["file_size"]


class Audio:
    def __init__(self, audio: dict):
        self.audid = audio["file_id"]
        self.duration = audio["duration"]
        self.mime_type = audio["mime_type"]
        self.file_size = audio["file_size"]
        if "title" in audio:
            self.title = audio["title"]
        else:
            self.title = "NoTitle"
        if "performer" in audio:
            self.performer = audio["performer"]
        else:
            self.performer = "NoPerformer"


class Photo:
    def __init__(self, photo: dict, caption: str):
        self.phtid = photo[-1]["file_id"]
        self.caption = caption


class Sticker:
    def __init__(self, sticker: dict):
        self.stkid = sticker["file_id"]


class DB:
    def __init__(self, bid, cid, uid, quoted, is_private):
        self.bid = bid

        self.group = None
        self.user = None
        self.quoted = None
        self.language = None

        # If it's a group
        if cid:
            self.group = mongo_interface.get_group(cid)
            # If the group doesn't exist
            if not self.group:
                # Create it and add it
                self.group = group.Group(cid, [bid], _default_language)
                mongo_interface.add_group(self.group)
            else:
                # Otherwise check if the bot is not present
                if bid not in self.group.present_bots:
                    # If so add it and update the group
                    self.group.present_bots.append(bid)
                    mongo_interface.update_group_by_id(self.group)

        if uid:
            self.user = mongo_interface.get_user(uid)
            if not self.user:
                self.user = user.User(uid, [bid], self.group is None)
                mongo_interface.add_user(self.user)

        if quoted:
            self.quoted = mongo_interface.get_user(quoted)
            if not self.quoted:
                self.quoted = user.User(quoted, [bid], self.group is None)
                mongo_interface.add_user(self.quoted)

        if is_private:
            self.language = self.user.language
        else:
            self.language = self.group.language

    def get_groups_count(self) -> int:
        return len(mongo_interface.get_bot_groups(self.bid))

    def get_users_count(self) -> int:
        return len(mongo_interface.get_known_users(self.bid))

    def get_started_users_count(self) -> int:
        return len(mongo_interface.get_known_started_users(self.bid))

    def update_user(self):
        mongo_interface.update_user_by_id(self.user)

    def update_group(self):
        mongo_interface.update_group_by_id(self.group)

    def update_quoted_user(self):
        mongo_interface.update_user_by_id(self.quoted)
