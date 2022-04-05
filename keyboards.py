from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton

chose_faction_kb = ReplyKeyboardMarkup([[KeyboardButton('Долг'), KeyboardButton('Свобода'), KeyboardButton('Монолит')],
                                        [KeyboardButton('Бандиты'), KeyboardButton('Вольные сталкеры')]],
                                       resize_keyboard=True,
                                       one_time_keyboard=True)
remove_keyboard = ReplyKeyboardRemove()