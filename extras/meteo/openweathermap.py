from requests import Session
from configuration.config import config

base_url = "https://api.openweathermap.org/data/2.5/weather"
appid = config["meteo"]["appid"]

session = Session()


class MeteoData:
    def __init__(self, name, desc, main, temp, feels, mint, maxt, humidity):
        self.name = name
        self.description = desc
        self.main = main
        self.current_temp = temp
        self.feel_temp = feels
        self.min = mint
        self.max = maxt
        self.humidity = humidity


def get_meteo(city: str, lang: str):
    return session.get(base_url, params={
        "q": f"{city}",
        "appid": appid,
        "lang": lang,
        "units": "metric"
    })


def extract_data(response) -> MeteoData:
    return MeteoData(response["name"],
                     response["weather"][0]["description"],
                     response["weather"][0]["main"],
                     response["main"]["temp"],
                     response["main"]["feels_like"],
                     response["main"]["temp_min"],
                     response["main"]["temp_max"],
                     response["main"]["humidity"])
