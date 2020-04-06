import re

from entities.infos import Infos
from configuration.config import config

gex = re.compile("meteo city: (.+)", re.I)


def meteo_reg(infos: Infos):
    msg: str = infos.message.text
    msg = msg.replace(infos.bot.name.split()[0], "").strip()
    res = re.search(gex, msg)
    if res:
        city = res.group(1)
        infos.db.user.extra["city"] = city
        infos.db.update_user()
        return f"Registered '{city}' as meteo city!"
    return "What...?"


def meteo_req(infos: Infos):
    city = infos.db.user.extra.get("city", None)
    if not city:
        return "Use 'meteo: city' to register!"
    return f"Meteo for '{city}':\nVai su Google e vedi no?!!-"


class MeteoModule:
    def load_dummies(self) -> dict:
        if not config["modules"]["meteo"]["enabled"]:
            return {}
        return {
            "<meteo>": meteo_reg,
            "<meteo_req>": meteo_req
        }
