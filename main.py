import sys

from core.lowlevel import mongo_interface
from logger import log
from core import core

logger = log.get_logger("main")

logger.info("Starting Kitsu Ultimate")

if len(sys.argv) == 3:
    token = sys.argv[1]
    owner_id = sys.argv[2]
    mongo_interface.register_bot(token, owner_id)
    logger.info("Maker created")
    sys.exit()

core.run()
