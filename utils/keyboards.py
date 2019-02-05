from telegram import methods


def trigger_type():
    btn1 = methods.button("Interaction", "interaction")
    btn2 = methods.button("Content", "content")
    btn3 = methods.button("Equal", "equal")
    btn4 = methods.button("Eteraction", "eteraction")
    btn_canc = methods.button("Cancel", "cancel")
    return methods.inline_keyboard([[btn1, btn2],
                                    [btn3, btn4],
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
    back = methods.button("Back", "back")
    return methods.inline_keyboard([[btn1, btn2],
                                    [btn4],
                                    [back]])


def menu():
    btn1 = methods.button("Dialogs", "menu_dialogs")
    btn2 = methods.button("Triggers", "menu_triggers")
    btn3 = methods.button("Sections", "menu_get_sections")
    close = methods.button("Close", "menu_close")
    return methods.inline_keyboard([[btn1, btn2, btn3],
                                    [close]])


def done():
    btn = methods.button("Done", "done")
    return methods.inline_keyboard([[btn]])