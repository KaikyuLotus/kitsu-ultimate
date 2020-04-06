from core import manager
from core.lowlevel import mongo_interface
from entities.infos import Infos
from utils import bot_utils


def newbot(infos: Infos):

    bot_count = manager.get_user_bots_count(infos.user.uid)

    if len(infos.message.args) == 1:
        if infos.message.args[0] == "bypass":
            bot_count = 0

    if bot_count == 1:
        return infos.reply(f"You already have a bot..")
    if bot_count > 1:
        return infos.reply(f"You already have {bot_count} bot(s)")

    if not bot_utils.is_bot_token(infos.message.args[0]):
        return infos.reply("{user.name} i think that this isn't a valid token...")

    infos.reply("Creating a new bot with this token...")
    ok = mongo_interface.register_bot(infos.message.text, infos.user.uid)
    if ok:
        infos.reply("Valid token! Your bot should be online now!")
    else:
        infos.reply("Something went wrong while registering the new bot...")


def myid(infos: Infos):
    infos.reply("Your ID is: {uid}")
