from core.lowlevel import mongo_interface
# from entities.bot import Bot
from entities.infos import Infos
from utils import bot_utils


def token_callback(infos: Infos):
    if infos.message.is_command:
        if infos.message.command == "cancel":
            infos.reply("Operation cancelled!")
            return infos.bot.cancel_wait()

    if not infos.message.is_text:
        return infos.reply("{user.name} i'm waiting for a token...")

    if not bot_utils.is_bot_token(infos.message.text):
        return infos.reply("{user.name} i think that this isn't a valid token...")

    infos.reply("Creating a new bot with this token...")
    infos.bot.cancel_wait()
    mongo_interface.register_bot(infos.message.text, infos.user.uid)

    #if not lotus.attach_bot_by_token(infos.message.text):
    #    return infos.reply("Something went wrong while creating "
    #                       "the bot, please check your token...")

    infos.reply("Valid token! Your bot should be online now!")


def newbot(infos: Infos):
    infos.reply("Nope.")
    return

    bot_count = manager.get_user_bots_count(infos.user)

    if len(infos.message.args) == 1:
        if infos.message.args[0] == "bypass":
            bot_count = 0

    if bot_count == 1:
        return infos.reply(f"You already have a bot..")
    if bot_count > 1:
        return infos.reply(f"You already have {bot_count} bot(s)")

    infos.reply("Please send now your bot token...")
    infos.bot.set_wait("text", infos.user.uid, token_callback)


def myid(infos: Infos):
    infos.reply("Your ID is: {uid}")
