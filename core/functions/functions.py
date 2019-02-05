from core.functions.menu import menus
from entities.infos import Infos


def menu(infos: Infos):
    # if not infos.chat.is_private:
    #    return infos.reply("Please use /menu only in private, master.")

    infos.bot.cancel_wait()
    infos.bot._callback = menus.menu(infos)


def bid(infos: Infos):
    infos.reply("My ID is {bid}")


def start(infos: Infos):
    infos.reply("Hello {name}!")


def uid(infos: Infos):
    infos.reply("Your user ID is `{uid}`")
