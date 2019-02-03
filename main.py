from logger import log
from core import core

logger = log.get_logger("main")

logger.info("Starting Kitsu Ultimate")

core.run()
