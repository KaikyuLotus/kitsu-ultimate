def assembly_dialogs_message(dialogs):
    message: str = ""
    counter: int = 1

    for dialog in dialogs:
        reply = dialog.reply
        if len(reply) > 50:
            reply = reply[:50] + "..."
        message += f"{counter}) `{reply}`\n"
        counter += 1

    return message
