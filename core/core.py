import time
from typing import Type

from core import manager
from core.lowlevel import mongo_interface
from entities.bot import Bot
from entities.module_function import ModuleFunction
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

_overrideable_module_function = [
    ModuleFunction("load_dummies", dict, True)
    # ModuleFunction("load_dummies", dict, False)
]


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
    log.i(f"Bot @{bot.username} ok")


def _run_bot(bot: Bot):
    _init(bot)
    Thread(target=bot.run, daemon=True).start()


def run(threaded: bool = True, idle: bool = True, auto_attach: bool = True):
    global _running
    if not threaded:
        log.i("Running in webhook mode")
        raise NotImplementedError()

    if auto_attach:
        log.d("Auto attaching bots from mongo")
        attach_bots(manager.get_tokens())

    log.i("Running attached bots")
    [_run_bot(bot) for bot in _attached_bots]

    _running = True
    if idle:
        _idle()


def _idle():
    try:
        while _running:
            time.sleep(10)
    except KeyboardInterrupt:
        log.w("Keyboard interrupt, stopping...")
        stop()


def stop():
    global _running
    log.i("Stopping bots")
    [bot.stop() for bot in _attached_bots]
    log.i("Stopping mongo ")
    mongo_interface.stop()
    _running = False


def detach_bot(token: str):
    log.i(f"Detaching bot {token}")
    for bot in _attached_bots:
        if bot.token != token:
            continue
        _attached_bots.remove(bot)
        log.i(f"Bot {token} detached")
        return bot.stop()
    log.i(f"Bot {token} not found")


def attach_bot(bot: Bot):
    _attached_bots.append(bot)
    log.i(f"Running bot {bot.bot_id}")
    _run_bot(bot)


def attach_bot_by_token(token: str):
    try:
        log.d(f"Attaching bot {token}")
        b = Bot(token)
        _attached_bots.append(b)
        log.d(f"Bot {b.bot_id} attached successfully")
        return True
    except Unauthorized:
        log.w(f"Wrong bot token: {token}")
    except TelegramException as error:
        error_name = error.__class__.__name__
        log.e(f"Exception '{error_name}' "
              f"while initializing the bot: {error}")
    return False


def attach_bots_from_manager():
    attach_bots(manager.get_tokens())


def attach_bots(tokens: list):
    log.d(f"Attaching {len(tokens)} bots")
    if not isinstance(tokens, list):
        log.w("You must pass a list to attach_bots,"
              " operation cancelled.")
    else:
        for token in tokens:
            if is_bot_token(token):
                attach_bot_by_token(token)
            else:
                log.w(f"Invalid token {token} skipping.")


def get_attached_bots():
    return _attached_bots


# noinspection PyPep8Naming
def load_module(Module: Type):
    module = Module()
    for function in _overrideable_module_function:
        if not _elab_module_fun(function, module, Module):
            log.w(f"Incompatible module, stopping load of {Module.__name__}")
            break


def _elab_module_fun(function, instance, Module):
    if not hasattr(instance, function.name):
        if not function.optional:
            log.w(f"{Module.__name__} has no function {function.name}")
        return function.optional

    real_function = getattr(instance, function.name)
    if not callable(real_function):
        if not function.optional:
            log.w(f"{Module.__name__}.{function.name} is not a function")
        return function.optional

    return_value = real_function()
    if type(return_value) is not function.type:
        log.w(f"{Module.__name__}.{function.name} returns '{type(return_value).__name__}',"
              f" '{type(function.type).__name__}' is required")
        return False

    log_string = function.elaborate_data(return_value)
    log.i(f"Module: {log_string}")
    return True
