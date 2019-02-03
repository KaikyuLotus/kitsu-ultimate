import time

from core import manager
from core.lowlevel import mongo_interface
from entities.bot import Bot
from exceptions.kitsu_exception import KitsuException
from exceptions.telegram_exception import TelegramException
from exceptions.unauthorized import Unauthorized
from logger import log
from telegram import methods
from utils.bot_utils import is_bot_token
from threading import Thread

_attached_bots = []
_main_bot = None
_running = False

_logger = log.get_logger("core")


def get_maker_bot():
    global _main_bot
    if _main_bot:
        return _main_bot

    for bot in _attached_bots:
        if bot.is_maker:
            _main_bot = bot

    if _main_bot:
        return _main_bot

    raise KitsuException("Main bot not found!")


def _init(bot):
    if bot.clean_start:
        methods.clean_updates(bot)
    _logger.info(f"Bot @{bot.username} ok")


def _run_bot(bot: Bot):
    _init(bot)
    Thread(target=bot.run, daemon=True).start()


def run(threaded: bool = True, idle: bool = True, auto_attach: bool = True):
    global _running
    if not threaded:
        _logger.info("Running in webhook mode")
        raise NotImplementedError()

    if auto_attach:
        _logger.debug("Auto attaching bots from mongo")
        attach_bots(manager.get_tokens())

    _logger.info("Running attached bots")
    [_run_bot(bot) for bot in _attached_bots]

    _running = True
    if idle:
        _idle()


def _idle():
    try:
        while _running:
            time.sleep(10)
    except KeyboardInterrupt:
        _logger.info("Keyboard interrupt, stopping...")
        stop()


def stop():
    global _running
    _logger.info("Stopping bots")
    [bot.stop() for bot in _attached_bots]
    _logger.info("Stopping mongo ")
    mongo_interface.stop()
    _running = False


def detach_bot(token: str):
    _logger.info(f"Detaching bot {token}")
    for bot in _attached_bots:
        if bot.token != token:
            continue
        _attached_bots.remove(bot)
        _logger.info(f"Bot {token} detached")
        return bot.stop()
    _logger.info(f"Bot {token} not found")


def attach_bot(bot: Bot):
    _attached_bots.append(bot)
    _logger.debug(f"Running bot {bot.bot_id}")
    _run_bot(bot)


def attach_bot_by_token(token: str):
    try:
        _logger.debug(f"Attaching bot {token}")
        b = Bot(token)
        _attached_bots.append(b)
        _logger.debug(f"Bot {b.bot_id} attached successfully")
        return True
    except Unauthorized:
        _logger.warn(f"Wrong bot token: {token}")
    except TelegramException as error:
        error_name = error.__class__.__name__
        _logger.error(f"Exception '{error_name}' "
                      f"while initializing the bot: {error}")
    return False


def attach_bots_from_manager():
    attach_bots(manager.get_tokens())


def attach_bots(tokens: list):
    _logger.debug(f"Attaching {len(tokens)} bots")
    if not isinstance(tokens, list):
        _logger.error("You must pass a list to attach_bots,"
                      " operation cancelled.")
    else:
        for token in tokens:
            if is_bot_token(token):
                attach_bot_by_token(token)
            else:
                _logger.warn(f"Invalid token {token} skipping.")


def get_attached_bots():
    return _attached_bots
