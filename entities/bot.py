import os
import time
import traceback

from pprint import pprint
from typing import List

import requests

from configuration.config import config
from core import elaborator, reply_parser, lotus_interface
from core.lowlevel import mongo_interface
from entities.infos import Infos
from exceptions.bad_request import BadRequest
from exceptions.conflict import Conflict
from exceptions.unauthorized import Unauthorized
from logger import log
from ktelegram import methods
from utils import regex_utils

_bot_maker_id = config["defaults"]["maker"]["id"]
_maker_owner_id = config["defaults"]["owner"]["id"]
_connection_retry_time = config["defaults"]["retry-time"]


class Bot:
    def __init__(self, token: str):
        log.d("Initializing new bot")

        self._callback = None
        self.waiting_data = {}

        self.start_time: int = 0
        self.is_maker: bool = False
        self.username: str = None
        self.name: str = None
        self.owner_id: int = None
        self.clean_start: bool = False
        self.automs_enabled: bool = False
        self.running: bool = False
        self.offset: int = 0
        self.custom_command_symb = "/"
        self.token: str = token
        self.bot_id: int = int(token.split(":")[0])
        self._load_data()
        self._get_telegram_data()
        self.is_maker = _bot_maker_id == self.bot_id
        self.regexed_name = regex_utils.string_to_regex(self.name.split(" ")[0].lower())
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
        self.automs_enabled = bot_data["automs_enabled"] if "automs_enabled" in bot_data else False
        self.custom_command_symb = bot_data["command_symb"] if "command_symb" in bot_data else "/"

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
        elif infos.user:
            if infos.user.is_bot_owner and self._callback:
                if infos.message.command == "cancel":
                    self._callback = None
                    infos.reply("Operation cancelled.")
                    return
            if infos.user.is_bot_owner and infos.message.command == "test":
                elaborator.elaborate_json_backup(infos)

        if infos.message.is_document:
            elaborator.elaborate_file(infos)
        elif infos.message.is_command:
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
        infos.callback_query.answer("Sorry, that action is forbidden")

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
        last_update = None
        try:
            updates = methods.get_updates(self.token, self.offset, 120)
            for update in updates:
                last_update = update
                t = time.process_time_ns()
                self._update_elaborator(update)
                elapsed_time = (time.process_time_ns() - t) / 1_000_000
                if elapsed_time > 50:
                    log.w(f"Update #{update['update_id']} elaboration "
                          f"took {elapsed_time} ms")
            last_update = None
        except Unauthorized:
            log.e(f"Unauthorized bot {self.bot_id}, detaching...")
            lotus_interface.detach_bot(self.token)
        except Conflict:
            log.e(f"Telegram said that bot {self.bot_id} is already running, detaching...")
            lotus_interface.detach_bot(self.token)
        except requests.ConnectionError:
            log.e(f"A connection error happened, waiting {_connection_retry_time} seconds before reconnecting")
            time.sleep(_connection_retry_time)
        except BadRequest as e:
            log.w(f"Warning, telegram said: {e.message}")
        except Exception as e:
            log.e(str(e))
            traceback.print_tb(e.__traceback__)
            if last_update:
                pprint(last_update)

    def run(self):
        self.running = True
        self.start_time = time.time()
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

    def reply(self, infos: Infos, text: str, quote: bool = True,
              markdown: bool = False, markup: List = None, nolink: bool = False):
        log.d("Replying with a message")
        methods.send_message(self.token, infos.chat.cid, text,
                             reply_to_message_id=infos.message.message_id
                             if quote else None,
                             parse_mode="markdown" if markdown else None,
                             reply_markup=markup,
                             disable_web_page_preview=nolink)

    def execute_reply(self, infos: Infos, reply: str):
        reply, quote, nolink, markdown, markup = reply_parser.parse(reply, infos)
        self.reply(infos, reply, quote=quote, markdown=markdown, markup=markup, nolink=nolink)

    def notify(self, message: str):
        log.d("Sending a notification message to the bot's owner")
        methods.send_message(self.token, _maker_owner_id, message)

    def __iter__(self):
        yield "token", self.token
        yield "owner_id", self.owner_id
        yield "clean_start", self.clean_start
        yield "username", self.username
        yield "automs_enabled", self.automs_enabled
        yield "command_symb", self.custom_command_symb

    def __str__(self):
        return self.token

    def __int__(self):
        return self.bot_id
