from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, InlineKeyboardMarkup, \
    InlineKeyboardButton

chose_faction_kb = ReplyKeyboardMarkup([[KeyboardButton('Долг'), KeyboardButton('Свобода'), KeyboardButton('Монолит')],
                                        [KeyboardButton('Бандиты'), KeyboardButton('Вольные сталкеры')]],
                                       resize_keyboard=True,
                                       one_time_keyboard=True)
remove_keyboard = ReplyKeyboardRemove()

hire_stalker_kb = InlineKeyboardMarkup(1)
hire_stalker_kb.add(InlineKeyboardButton(text='Нанять 1 сталкера', callback_data='hire'))
menu_kb = ReplyKeyboardMarkup([[KeyboardButton('/recruitment')]], resize_keyboard=True)
