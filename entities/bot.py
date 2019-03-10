import time
import traceback
from pprint import pprint

from core import elaborator, reply_parser, core
from core.lowlevel import mongo_interface
from entities.infos import Infos
from exceptions.conflict import Conflict
from exceptions.unauthorized import Unauthorized
from logger import log
from telegram import methods

# TODO make a config file
from utils import regex_utils

_bot_maker_id = 777706082
_maker_owner_id = 487353090


class Bot:
    def __init__(self, token: str):
        log.d("Initializing new bot")

        self._callback = None
        self.waiting_data = {}

        self.is_maker: bool = False
        self.username: str = None
        self.name: str = None
        self.owner_id: int = None
        self.clean_start: bool = False
        self.running: bool = False
        self.offset: int = 0
        self.token: str = token
        self.bot_id: int = int(token.split(":")[0])
        self._load_data()
        self._get_telegram_data()
        self.is_maker = _bot_maker_id == self.bot_id
        self.regexed_name = regex_utils.string_to_regex(
            self.name.split(" ")[0].lower())
        log.d("Bot ready")

    def _get_telegram_data(self):
        log.d("Getting bot data from Telegram")
        bot_data = methods.get_me(self.token)
        self.name = bot_data["first_name"]
        self.username = bot_data["username"]

    def _load_data(self):
        log.d("Getting bot data from mongo")
        bot_data = mongo_interface.get_bot_data(self.token)
        self.owner_id = int(bot_data["owner_id"])
        self.clean_start = bot_data["clean_start"]

    def _update_elaborator(self, update: dict):
        self.offset = update["update_id"] + 1
        infos = Infos(self, update)

        if infos.is_edited_message or infos.is_channel_post or infos.is_edited_channel_post:
            log.d(f"Ignoring update of type {infos.update_type}")
            return

        if not self._callback:
            self.waiting_data = {}

        if infos.user and not infos.message.is_command:
            if infos.user.is_bot_owner and self._callback:
                log.d(f"Calling callback {self._callback.__name__}")
                self._callback = self._callback(infos)
                return
        else:
            if infos.user.is_bot_owner and self._callback:
                if infos.message.command == "cancel":
                    self._callback = None
                    infos.reply("Operation cancelled.")
                    return

        if infos.message.is_command:
            mongo_interface.increment_read_messages(self.bot_id)
            self._command_elaborator(infos)
        elif infos.is_callback_query:
            self._callback_elaborator(infos)
        elif infos.is_message:
            mongo_interface.increment_read_messages(self.bot_id)
            self._message_elaborator(infos)

    def _callback_elaborator(self, infos: Infos):
        # Answer if it's not awaited
        log.d("Unawaited callback, answering with default answer")
        infos.callback_query.answer("Please don't.")

    def _message_elaborator(self, infos: Infos):
        elaborator.elaborate(infos)  # Not a command, elaborate the message

    def _command_elaborator(self, infos: Infos):

        if not elaborator.command(infos):
            if not elaborator.owner_command(infos):
                # It's a command and not a normal one
                if not elaborator.maker_command(infos):
                    # Not a maker command
                    elaborator.maker_master_command(infos)

    def _updater(self):
        try:
            updates = methods.get_updates(self.token, self.offset, 120)
            for update in updates:
                t = time.process_time_ns()
                self._update_elaborator(update)
                elapsed_time = (time.process_time_ns() - t) / 1_000_000
                if elapsed_time > 50:
                    log.w(f"Update #{update['update_id']} elaboration "
                          f"took {elapsed_time} ms")
        except Unauthorized:
            log.e(f"Unauthorized bot {self.bot_id}, detaching...")
            core.detach_bot(self.token)
        except Conflict:
            log.e(f"Telegram said that bot {self.bot_id} is already running, detaching...")
            core.detach_bot(self.token)
        except Exception as e:
            log.e(str(e))
            traceback.print_tb(e.__traceback__)
            pprint(update)

    def run(self):
        self.running = True
        log.d("Starting update loop")
        while self.running:
            self._updater()

    def stop(self):
        log.d("Setting bot to a not running state,"
              " it'll stop after the next get updates request")
        self.running = False

    def cancel_wait(self):
        self._callback = None
        self.waiting_data = {}
        log.d("Waiting cancelled")

    def reply(self, infos: Infos, text: str, quote: bool = True):
        log.d("Replying with a message")
        methods.send_message(self.token, infos.chat.cid, text,
                             reply_to_message_id=infos.message.message_id
                             if quote else None)

    def execute_reply(self, infos: Infos, reply: str):
        reply, quote = reply_parser.parse(reply, infos)
        self.reply(infos, reply, quote=quote)

    def notify(self, message: str):
        log.d("Sending a notification message to the bot's owner")
        methods.send_message(self.token, _maker_owner_id, message)

    def __str__(self):
        return self.token

    def __int__(self):
        return self.bot_id
