from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, InlineKeyboardMarkup, \
    InlineKeyboardButton

chose_faction_kb = ReplyKeyboardMarkup([[KeyboardButton('Долг'), KeyboardButton('Свобода'), KeyboardButton('Монолит')],
                                        [KeyboardButton('Бандиты'), KeyboardButton('Чистое небо')]],
                                       resize_keyboard=True,
                                       one_time_keyboard=True)
remove_keyboard = ReplyKeyboardRemove()

hire_stalker_kb = InlineKeyboardMarkup(1)
hire_stalker_kb.add(InlineKeyboardButton(text='Нанять 1 сталкера', callback_data='hire'))

merchants_kb = InlineKeyboardMarkup(1)
merchants_kb.add(InlineKeyboardButton(text='Зайти', callback_data='merch'))

buy_kb = InlineKeyboardMarkup(5)
buy_kb.add(InlineKeyboardButton(text='Продать артефакт "Батарейка"', callback_data='art1'))
buy_kb.add(InlineKeyboardButton(text='Продать артефакт "Грави"', callback_data='art2'))
buy_kb.add(InlineKeyboardButton(text='Продать артефакт "Ночная звезда"', callback_data='art3'))
buy_kb.add(InlineKeyboardButton(text='Продать артефакт "Каменный цветок"', callback_data='art4'))
buy_kb.add(InlineKeyboardButton(text='Продать артефакт "Лунный свет"', callback_data='art5'))

sell_arts_kb = None
