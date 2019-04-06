import random

from telegram import methods


def trigger_type():
    btn1 = methods.button("Interaction", "interaction")
    btn2 = methods.button("Content", "content")
    btn3 = methods.button("Equal", "equal")
    btn4 = methods.button("Eteraction", "eteraction")
    btn5 = methods.button("Command", "command")
    btn_canc = methods.button("Cancel", "cancel")
    return methods.inline_keyboard([[btn1, btn2],
                                    [btn3, btn4],
                                    [btn5],
                                    [btn_canc]])


def menu_dialogs():
    btn1 = methods.button("Add Dialog", "add_dialog")
    btn2 = methods.button("Del. Dialog", "del_dialog")
    btn4 = methods.button("List Dialogs", "list_dialogs")
    back = methods.button("Back", "menu_back")
    return methods.inline_keyboard([[btn1, btn2],
                                    [btn4],
                                    [back]])


def menu_triggers():
    btn1 = methods.button("Add Trigger", "add_trigger")
    btn2 = methods.button("Del. Trigger", "del_trigger")
    btn4 = methods.button("List Triggers", "list_triggers")
    back = methods.button("Back", "menu_back")
    return methods.inline_keyboard([[btn1, btn2],
                                    [btn4],
                                    [back]])


def menu_sections():
    btn1 = methods.button("Del Section", "del_section")
    btn2 = methods.button("List Sections", "list_sections")
    back = methods.button("Back", "menu_back")
    return methods.inline_keyboard([[btn1],
                                    [btn2],
                                    [back]])


def menu_options(bot):
    symb = "ON" if bot.automs_enabled else "OFF"
    c_symb = bot.custom_command_symb
    btn1 = methods.button(f"Automatic Messages: {symb}", "options_autom")
    btn2 = methods.button(f"Command Symbol: {c_symb}", "options_comm_symbol")
    btn3 = methods.button("Delete bot", "options_delete_bot")
    back = methods.button("Back", "options_back")
    return methods.inline_keyboard([[btn1],
                                    [btn2],
                                    [btn3],
                                    [back]])


def menu():
    btn1 = methods.button("Dialogs", "menu_dialogs")
    btn2 = methods.button("Triggers", "menu_triggers")
    btn3 = methods.button("Sections", "menu_sections")
    btn4 = methods.button("Options", "menu_options")
    close = methods.button("Close", "menu_close")
    return methods.inline_keyboard([[btn1, btn2, btn3],
                                    [btn4],
                                    [close]])


def delete_bot():
    row1 = [methods.button("Yes", "delete_bot_yes")]
    row2 = [methods.button("No", "delete_bot_no")]
    row3 = [methods.button("No", "delete_bot_no")]
    rows = [row1, row2, row3]
    random.shuffle(rows)
    return methods.inline_keyboard(rows)


def done():
    btn = methods.button("Done", "done")
    return methods.inline_keyboard([[btn]])


def cancel():
    btn = methods.button("Cancel", "cancel")
    return methods.inline_keyboard([[btn]])
