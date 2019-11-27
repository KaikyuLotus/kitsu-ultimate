import re
from typing import Optional

from logger import log

_multi_frag = "\\b[\\w\\s]*\\b"
_multi_frag_symbol = "\\&"


def string_to_regex(string: str):
    for char in "aeiou":
        string = string.replace(char, char + "+")
    return string


def is_command(string: str, symbol: str, command: str):
    return True if re.search(rf"{re.escape(symbol)}{re.escape(command)}( .+)?", string, flags=re.I) else False


# Better return a boolean than a match object
def is_interaction(string: str, bot_name: str):
    return True if re.search(rf"(^{bot_name}\b)|(\b{bot_name}\W*$)",
                             string, flags=re.I) else False


def is_equal(string: str, trigger: str):
    return True if re.search(rf"^{trigger}$", string,
                             flags=re.I) else False


def is_content(string: str, trigger: str):
    if _multi_frag_symbol not in trigger and re.search(rf"^{trigger}$", string, flags=re.I):
        return False  # This is an equal so not valid

    return is_in_message(string, trigger)


def is_in_message(message: str, trigger: str):
    return True if re.search(rf"\b{trigger.replace(_multi_frag_symbol, _multi_frag)}\b", message, flags=re.I) else False


def get_dialog_probability(message: str) -> [Optional[int], str]:
    match = re.search(r"^{(\d{1,3})%}", message)
    prob: Optional[int] = None
    if match:
        prob = int(match.group(1))
        if prob < 1:
            prob = 1
        elif prob > 99:
            prob = 100
        message = message.replace(match.group(0), "")
        log.d(f"Found probability in string: {prob}")
    return prob, message
