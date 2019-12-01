import importlib
import traceback

from typing import Type, List

from configuration.config import config
from core import manager, variables
from core import lotus_interface
from core.lowlevel import mongo_interface
from entities.bot import Bot
from entities.module_function import ModuleFunction
from exceptions.configuration_error import ConfigurationError
from exceptions.kitsu_exception import KitsuException
from exceptions.telegram_exception import TelegramException
from exceptions.unauthorized import Unauthorized
from logger import log
from utils.bot_utils import is_bot_token


_main_bot = None

_overrideable_module_function = [
    ModuleFunction("load_dummies", dict, True),
    ModuleFunction("on_new_trigger", bool, True),
    ModuleFunction("on_trigger_change", bool, True)
]


def get_maker_bot():
    global _main_bot
    if _main_bot:
        return _main_bot

    for bot in variables.attached_bots:
        if bot.is_maker:
            _main_bot = bot

    if _main_bot:
        return _main_bot

    raise KitsuException("Main bot not found!")


def run(threaded: bool = True, idle: bool = True, auto_attach: bool = True):

    log.i(f"Starting Kitsu Ultimate version {config['lotus']['version']}")

    _load_modules()

    if config["startup"]["drop"]["dialogs"]:
        log.i("Dropping dialogs")
        mongo_interface.drop_dialogs()

    if config["startup"]["drop"]["triggers"]:
        log.i("Dropping triggers")
        mongo_interface.drop_triggers()

    if config["startup"]["drop"]["bots"]:
        log.i("Dropping bots")
        mongo_interface.drop_bots()

    if config["startup"]["drop"]["groups"]:
        log.i("Dropping groups")
        mongo_interface.drop_groups()

    if config["startup"]["drop"]["users"]:
        log.i("Dropping users")
        mongo_interface.drop_users()

    if not threaded:
        log.i("Running in webhook mode")
        raise NotImplementedError()

    if auto_attach:
        log.d("Auto attaching bots from mongo")
        attach_bots_from_manager()

    log.i("Running attached bots")
    [lotus_interface.run_bot(bot) for bot in variables.attached_bots]

    variables.running = True
    if idle:
        lotus_interface.idle()


def attach_bot_by_token(token: str):
    try:
        log.d(f"Attaching bot {token}")
        b = Bot(token)
        variables.attached_bots.append(b)
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
    tokens = manager.get_tokens()
    if not tokens:
        log.i("Not bots found on database, adding default bot")
        maker_token = config["defaults"]["maker"]["token"]
        owner_id = config["defaults"]["owner"]["id"]
        if not maker_token or not owner_id:
            raise ConfigurationError("No bots on database and configuration file has no default token nor owner id")
        if not mongo_interface.register_bot(maker_token, owner_id):
            log.e("Could not even register default bot, interrupting execution abruptly")
            exit(1)
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


def get_attached_bots() -> List[Bot]:
    return variables.attached_bots


# noinspection PyPep8Naming
def _load_modules():
    for module in config["modules"]["classes"]:
        try:
            if "." in module:
                class_name = module.split(".")[-1]
                module = ".".join(module.split(".")[:-1])
                LoadedModule = getattr(importlib.import_module(module), class_name)
                log.d(f"Loading module: {module} with class {LoadedModule}")
                load_module(LoadedModule)
        except Exception as err:
            log.e(err)
            traceback.print_exc()


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

    if function.name == "on_new_trigger":
        variables.on_new_trigger_functions.append(real_function)
        log.i("Registered callback")
        return True
    if function.name == "on_trigger_change":
        variables.on_trigger_change_functions.append(real_function)
        log.i("Registered callback")
        return True

    return_value = real_function()
    if type(return_value) is not function.type:
        log.w(f"{Module.__name__}.{function.name} returns '{type(return_value).__name__}',"
              f" '{type(function.type).__name__}' is required")
        return False

    log_string = function.elaborate_data(return_value)
    log.i(f"Module: {log_string}")
    return True


if __name__ == "__main__":
    run()
