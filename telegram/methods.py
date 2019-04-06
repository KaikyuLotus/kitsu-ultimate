import json
from json import JSONDecodeError

import requests
from requests import post

from entities.file import File
from exceptions.conflict import Conflict
from exceptions.bad_request import BadRequest
from exceptions.forbidden import Forbidden
from exceptions.kitsu_exception import KitsuException
from exceptions.not_found import NotFound
from exceptions.telegram_exception import TelegramException
from exceptions.unauthorized import Unauthorized
from logger import log

_base_url = "https://api.telegram.org"


def execute(token: str, method: str, params: dict = None, post_data: dict = None):
    if post_data is not None:
        log.d(f"POST request to {_base_url}/bot???/{method}")
        res = requests.post(f"{_base_url}/bot{token}/{method}", params=params, files=post_data)
    else:
        # log.d(f"GET request to {_base_url}/bot???/{method}")
        res = requests.get(f"{_base_url}/bot{token}/{method}", params=params)

    status_code = res.status_code

    if status_code == 200:
        return res.json()["result"]

    error = f"{status_code} while executing {method}"
    try:
        args = [res.json()["description"],
                error,
                [key for key in params],
                [params[key] for key in params]]
    except JSONDecodeError:
        args = [res.text,
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


def download(token: str, path: str):
    response = requests.get(f"https://api.telegram.org/file/bot{token}/{path}")

    status_code = response.status_code

    args = ["Cannot get file",
            "Unknown error",
            ["token", "path"],
            [token, path]]

    if status_code == 200:
        return response.content

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
                 reply_markup: str = None,
                 disable_web_page_preview: bool = None):
    return execute(token, "sendMessage", {
        "text": text,
        "chat_id": chat_id,
        "reply_to_message_id": reply_to_message_id,
        "parse_mode": parse_mode,
        "reply_markup": reply_markup,
        "disable_web_page_preview": disable_web_page_preview
    })


def send_sticker(token: str,
                 chat_id: int,
                 sticker: str,
                 disable_notification: bool = None,
                 reply_to_message_id: int = None,
                 reply_markup: str = None):
    return execute(token, "sendSticker", {
        "chat_id": chat_id,
        "sticker": sticker,
        "disable_notification": disable_notification,
        "reply_to_message_id": reply_to_message_id,
        "reply_markup": reply_markup
    })


def send_photo(token: str,
               chat_id: int,
               photo: str,
               caption: str = None,
               disable_notification: bool = None,
               reply_to_message_id: int = None,
               reply_markup: str = None):
    return execute(token, "sendPhoto", {
        "chat_id": chat_id,
        "photo": photo,
        "caption": caption,
        "disable_notification": disable_notification,
        "reply_to_message_id": reply_to_message_id,
        "reply_markup": reply_markup
    })


def send_audio(token: str,
               chat_id: int,
               audio: str,
               disable_notification: bool = None,
               reply_to_message_id: int = None,
               reply_markup: str = None):
    return execute(token, "sendAudio", {
        "chat_id": chat_id,
        "audio": audio,
        "disable_notification": disable_notification,
        "reply_to_message_id": reply_to_message_id,
        "reply_markup": reply_markup
    })


def send_voice(token: str,
               chat_id: int,
               voice: str = None,
               disable_notification: bool = None,
               reply_to_message_id: int = None,
               reply_markup: str = None,
               voice_data: bytes = None):
    if not voice and not voice_data:
        raise KitsuException("send_voice needs 'voice' or 'voice_data' to be not null")
    return execute(token, "sendVoice", {
        "chat_id": chat_id,
        "voice": voice,
        "disable_notification": disable_notification,
        "reply_to_message_id": reply_to_message_id,
        "reply_markup": reply_markup
    }, {
        "voice": voice_data
    } if voice_data else None)


def send_doc(token: str,
             chat_id: int,
             document: str,
             disable_notification: bool = None,
             reply_to_message_id: int = None,
             reply_markup: str = None):
    return execute(token, "sendDocument", {
        "chat_id": chat_id,
        "document": document,
        "disable_notification": disable_notification,
        "reply_to_message_id": reply_to_message_id,
        "reply_markup": reply_markup
    })


def send_chat_action(token: str,
                     chat_id: int,
                     action: str):
    return execute(token, "sendChatAction", {
        "chat_id": chat_id,
        "action": action,
    })


def answer_callback_query(token: str,
                          callback_query_id: str,
                          text: str = None,
                          show_alert: bool = None,
                          url: str = None,
                          cache_time: int = None):
    return execute(token, "answerCallbackQuery", {
        "callback_query_id": callback_query_id,
        "text": text,
        "show_alert": show_alert,
        "url": url,
        "cache_time": cache_time
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
        "text": text,
        "chat_id": chat_id,
        "message_id": message_id,
        "inline_message_id": inline_message_id,
        "parse_mode": parse_mode,
        "disable_web_page_preview": disable_web_page_preview,
        "reply_markup": reply_markup
    })


def delete_message(token: str, chat_id: int, message_id: int):
    return execute(token, "deleteMessage", {
        "message_id": message_id,
        "chat_id": chat_id
    })


def get_file(token: str, file_id: str):
    return File.from_json(execute(token, "getFile", {
        "file_id": file_id
    }))


def kick_chat_member(token: str, chat_id: int, user_id: int, until_date: int) -> File:
    return execute(token, "kickChatMember", {
        "chat_id": chat_id,
        "user_id": user_id,
        "until_date": until_date
    })


# Inline kb utils
def button(text: str, data: str):
    return {"text": text, "callback_data": data}


def link_button(text: str, link: str):
    return {"text": text, "url": link}


def inline_keyboard(btns):
    return json.dumps({"inline_keyboard": btns})


# Aliases
getUpdates = get_updates
getMe = get_me
sendMessage = send_message
answerCallbackQuery = answer_callback_query
