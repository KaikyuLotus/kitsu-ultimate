import json

import requests

from exceptions.conflict import Conflict
from exceptions.bad_request import BadRequest
from exceptions.forbidden import Forbidden
from exceptions.not_found import NotFound
from exceptions.telegram_exception import TelegramException
from exceptions.unauthorized import Unauthorized

_base_url = "https://api.telegram.org"


def execute(token: str, method: str, params: dict = None):
    res = requests.get(f"{_base_url}/bot{token}/{method}", params=params)
    status_code, _json = res.status_code, res.json()

    if status_code == 200:
        return _json["result"]

    error = f"{status_code} while executing {method}"
    args = [_json["description"],
            error,
            [key for key in params],
            [params[key] for key in params]]

    if status_code == 409:
        raise Conflict(*args)

    if status_code == 404:
        raise NotFound(*args)

    if status_code == 403:
        raise Forbidden(*args)

    if status_code == 401:
        raise Unauthorized(*args)

    if status_code == 400:
        raise BadRequest(*args)

    raise TelegramException(*args)


def clean_updates(token: str):
    updates = get_updates(token, offset=-1)
    return updates[-1]["update_id"] + 1 if updates else 0


def get_updates(token: str, offset: int = 0, timeout: int = 0):
    return execute(token, "getUpdates",
                   {"offset": offset, "timeout": timeout})


def get_me(token: str):
    return execute(token, "getMe")


def send_message(token: str,
                 chat_id: int,
                 text: str,
                 reply_to_message_id: int = None,
                 parse_mode: str = None,
                 reply_markup: str = None):
    return execute(token, "sendMessage", {
        "text":                text,
        "chat_id":             chat_id,
        "reply_to_message_id": reply_to_message_id,
        "parse_mode":          parse_mode,
        "reply_markup":        reply_markup
    })


def answer_callback_query(token: str,
                          callback_query_id: str,
                          text: str = None,
                          show_alert: bool = None,
                          url: str = None,
                          cache_time: int = None):
    return execute(token, "answerCallbackQuery", {
        "callback_query_id": callback_query_id,
        "text":              text,
        "show_alert":        show_alert,
        "url":               url,
        "cache_time":        cache_time
    })


def edit_message_text(token: str,
                      text: str,
                      chat_id: int = None,
                      inline_message_id: str = None,
                      message_id: int = None,
                      parse_mode: str = None,
                      disable_web_page_preview: bool = None,
                      reply_markup: str = None):
    return execute(token, "editMessageText", {
        "text":                     text,
        "chat_id":                  chat_id,
        "message_id":               message_id,
        "inline_message_id":        inline_message_id,
        "parse_mode":               parse_mode,
        "disable_web_page_preview": disable_web_page_preview,
        "reply_markup":             reply_markup
    })


def delete_message(token: str, chat_id: int, message_id: int):
    return execute(token, "deleteMessage", {
        "message_id": message_id,
        "chat_id":    chat_id
    })


# Inline kb utils
def button(text: str, data: str):
    return {"text": text, "callback_data": data}


def inline_keyboard(btns):
    return json.dumps({"inline_keyboard": btns})


# Aliases
getUpdates = get_updates
getMe = get_me
sendMessage = send_message
answerCallbackQuery = answer_callback_query
