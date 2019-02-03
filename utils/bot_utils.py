_token_length = 45


def is_bot_token(token: str):
    return isinstance(token, str) and len(token) == _token_length
