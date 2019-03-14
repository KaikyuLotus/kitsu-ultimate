# from core.lowlevel import mongo_interface
from core.lowlevel import mongo_interface
from modules.meteo import MeteoModule
from logger import log
from core import core


log.i("Starting Kitsu Ultimate")
core.load_module(MeteoModule)

mongo_interface.drop_users()
mongo_interface.drop_groups()
# mongo_interface.drop_triggers()
# mongo_interface.drop_dialogs()

core.run()
