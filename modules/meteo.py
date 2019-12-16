import re

from entities.infos import Infos
from configuration.config import config

from extras.meteo import openweathermap


def meteo_reg(infos: Infos):
    res = re.search(".*meteo (?:per|for) (.+)", infos.message.text, re.I)
    if res:
        city = res.group(1).capitalize()
        if openweathermap.get_meteo(city, infos.user.language_code.capitalize()).status_code == 200:
            infos.db.user.extra["city"] = city.capitalize()
            infos.db.update_user()
            return f"'{city}' registrata!"
        else:
            return "Questa città probabilmente non esiste..."
    return "What...?"


def meteo_req(infos: Infos):
    city = infos.db.user.extra.get("city", None)
    if not city:
        return "Dimmi 'meteo per città' per registrare una città!"
    meteo = openweathermap.get_meteo(city, infos.user.language_code.lower())
    if meteo.status_code == 200:
        data = openweathermap.extract_data(meteo.json())
        return f"[md]Meteo per *{city}*:\n" \
               f"Stato: *{data.description}*\n" \
               f"Temperatura: *{data.current_temp}*\n" \
               f"Percepita: *{data.feel_temp}*"
    else:
        return f"Qualcosa è andato storto..."


class MeteoModule:
    def load_dummies(self) -> dict:
        if not config["modules"]["meteo"]["enabled"]:
            return {}
        return {
            "<meteo>": meteo_reg,
            "<meteo_req>": meteo_req
        }
