import time
import lotus

from core.lowlevel import mongo_interface
from entities.bot import Bot
from entities.trigger import Trigger
from configuration.config import config
from ktelegram import methods
from logger import log


class TriggerHelperModule:
    def on_trigger_change(self, trigger: Trigger):
        mod_config = config["modules"]["trigger-helper"]
        if not mod_config["enabled"]:
            return

        bot: Bot = None
        for att_bot in lotus.get_attached_bots():
            if att_bot.bot_id == trigger.bot_id:
                bot = att_bot

        if not bot:
            log.w("Bot not found!")
            return

        triggers = {
            "Interactions": mongo_interface.get_triggers_of_type(bot.bot_id, "interaction"),
            "Eteractions": mongo_interface.get_triggers_of_type(bot.bot_id, "eteraction"),
            "Equals": mongo_interface.get_triggers_of_type(bot.bot_id, "equal"),
            "Contents": mongo_interface.get_triggers_of_type(bot.bot_id, "content")
        }

        msg = ""
        for t_type in triggers:
            msg += f"*{t_type}*:\n"
            for trigger in triggers[t_type]:
                msg += f"- `{trigger.trigger}` *{trigger.usages}* usages\n"
            msg += "\n"

        chid = mod_config["channel-id"]
        msgid = mod_config["msg-id"]
        methods.edit_message_text(bot.token, msg, chat_id=chid, message_id=msgid, parse_mode="Markdown")
        log.i("Edited")
