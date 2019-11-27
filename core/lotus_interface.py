import time
from threading import Thread

from core import variables
from core.lowlevel import mongo_interface
from logger import log
from ktelegram import methods


def detach_bot(token: str):
    log.i(f"Detaching bot {token}")
    for bot in variables.attached_bots:
        log.d(bot.token)
        if bot.token != str(token):
            continue
        variables.attached_bots.remove(bot)
        log.i(f"Bot {token} detached")
        return bot.stop()
    log.i(f"Bot {token} not found")


def _init(bot):
    if bot.clean_start:
        methods.clean_updates(bot)
    log.i(f"Bot @{bot.username} ok")


def run_bot(bot):
    _init(bot)
    Thread(target=bot.run, daemon=True).start()


def idle():
    try:
        while variables.running:
            time.sleep(10)
    except KeyboardInterrupt:
        log.w("Keyboard interrupt, stopping...")
        stop()


def stop():
    log.i("Stopping bots")
    [bot.stop() for bot in variables.attached_bots]
    log.i("Stopping mongo ")
    mongo_interface.stop()
    variables.running = False


def attach_bot(bot):
    variables.attached_bots.append(bot)
    log.i(f"Running bot {bot.bot_id}")
    run_bot(bot)
