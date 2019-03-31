import re
from typing import Optional

from logger import log


def string_to_regex(string: str):
    for char in "aeiou":
        string = string.replace(char, char + "+")
    return string


# Better return a boolean than a match object
def is_interaction(string: str, bot_name: str):
    return True if re.search(rf"(^{bot_name}\b)|(\b{bot_name}\W*$)",
                             string, flags=re.I) else False


def is_equal(string: str, trigger: str):
    return True if re.search(rf"^{trigger}$", string,
                             flags=re.I) else False


def is_content(string: str, trigger: str):
    if re.search(rf"\b{trigger}\b", string, flags=re.I):
        return False if re.search(rf"^{trigger}$", string,
                                  flags=re.I) else True


def is_in_message(message: str, trigger: str):
    return True if re.search(rf"\b{trigger}\b", message,
                             flags=re.I) else False


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
