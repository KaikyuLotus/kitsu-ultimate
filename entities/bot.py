import os
import time
import traceback

from core import elaborator, reply_parser, core
from core.lowlevel import mongo_interface
from entities.infos import Infos
from exceptions.unauthorized import Unauthorized
from logger import log
from ktelegram import methods

# TODO make a config file
from utils import regex_utils

_bot_maker_id = int(os.environ["BOT_MAKER_ID"])
_maker_owner_id = int(os.environ["MAKER_OWNER_ID"])

_logger = log.get_logger("bot")


class Bot:
    def __init__(self, token: str):
        _logger.debug("Initializing new bot")

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
        _logger.debug("Bot ready")

    def _get_telegram_data(self):
        _logger.debug("Getting bot data from Telegram")
        bot_data = methods.get_me(self.token)
        self.name = bot_data["first_name"]
        self.username = bot_data["username"]

    def _load_data(self):
        _logger.debug("Getting bot data from mongo")
        bot_data = mongo_interface.get_bot_data(self.token)
        self.owner_id = int(bot_data["owner_id"])
        self.clean_start = bot_data["clean_start"]

    def _update_elaborator(self, update: dict):
        self.offset = update["update_id"] + 1
        infos = Infos(self, update)

        # _logger.debug(f"Elaborating update {update['update_id']} "
        #               f"of type {infos.update_type}")

        if not self._callback:
            self.waiting_data = {}

        if infos.user and not infos.message.is_command:
            if infos.user.is_bot_owner and infos.chat.is_private and self._callback:
                _logger.debug(f"Calling callback {self._callback.__name__}")
                self._callback = self._callback(infos)
                return

        if infos.is_edited_message:
            pass  # TODO implement edited message handling
        elif infos.is_channel_post:
            pass  # TODO implement channel post handling
        elif infos.is_edited_channel_post:
            pass  # TODO implement edited channel post handling
        elif infos.message.is_command:
            self._command_elaborator(infos)
        elif infos.is_callback_query:
            self._callback_elaborator(infos)
        elif infos.is_message:
            self._message_elaborator(infos)

    def _callback_elaborator(self, infos: Infos):
        # Answer if it's not awaited
        _logger.debug("Unawaited callback, answering with default answer")
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
                    _logger.warn(f"Update #{update['update_id']} elaboration "
                                 f"took {elapsed_time} ms")

        except Unauthorized:
            print("Unauthorized bot, detaching...")
            core.detach_bot(str(self))
        except Exception as e:
            print(e)
            traceback.print_tb(e.__traceback__)

    def run(self):
        self.running = True
        _logger.debug("Starting update loop")
        while self.running:
            self._updater()

    def stop(self):
        _logger.debug("Setting bot to a not running state,"
                      " it'll stop after the next get updates request")
        self.running = False

    def cancel_wait(self):
        self._callback = None
        self.waiting_data = {}
        _logger.debug("Waiting cancelled")

    def reply(self, infos: Infos, text: str, quote: bool = True):
        _logger.debug("Replying with a message")
        methods.send_message(self.token, infos.chat.cid, text,
                             reply_to_message_id=infos.message.message_id
                             if quote else None)

    def execute_reply(self, infos: Infos, reply: str):
        reply, quote = reply_parser.parse(reply, infos)
        self.reply(infos, reply, quote=quote)

    def notify(self, message: str):
        _logger.info("Sending a notification message to the bot's owner")
        methods.send_message(self.token, _maker_owner_id, message)

    def __str__(self):
        return self.token

    def __int__(self):
        return self.bot_id
