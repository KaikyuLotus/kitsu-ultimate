import re


def string_to_regex(string: str):
    for char in "aeiou":
        string = string.replace(char, char + "+")
    return string


# Better return a boolean than a match object
def is_interaction(string: str, bot_name: str):
    return True if re.search(rf"(^{bot_name}\b)|(\b{bot_name}\W*$)",
                             string, flags=re.I) else False


def is_equal(string: str, trigger: str):
    return True if re.search(rf"^{string_to_regex(trigger)}$", string,
                             flags=re.I) else False


def is_content(string: str, trigger: str):
    r_trigger = string_to_regex(trigger)
    if re.search(rf"\b{r_trigger}\b", string, flags=re.I):
        return False if re.search(rf"^{r_trigger}$", string,
                                  flags=re.I) else True


def is_in_message(message: str, trigger: str):
    return True if re.search(rf"\b{string_to_regex(trigger)}\b", message,
                             flags=re.I) else False
