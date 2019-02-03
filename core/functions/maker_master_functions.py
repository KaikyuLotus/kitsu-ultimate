from core import core
from entities.infos import Infos


def stop(infos: Infos):
    core.stop()
    infos.reply("Stopped...")
