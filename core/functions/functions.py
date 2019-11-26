from core.functions.menu import menus
from entities.infos import Infos


def menu(infos: Infos):
    infos.bot.cancel_wait()
    infos.bot._callback = menus.menu(infos)
