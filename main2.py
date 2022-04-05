import logging
import sqlite3

from aiogram import Bot, Dispatcher, executor, types
from config.tg_token import API_TOKEN
from keyboards import chose_faction_kb, remove_keyboard
from aiogram.dispatcher.filters import Text

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

conn = sqlite3.connect('db/users_info.db')
cur = conn.cursor()


def user_is_registered(msg):
    if not cur.execute('''SELECT * FROM main WHERE user_id = ?''', (msg.from_user.id,)).fetchone():
        return False
    return True


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    if not user_is_registered(message):
        cur.execute('''INSERT INTO main(user_id, money) VALUES (?, 0)''', (message.from_user.id,))
        conn.commit()
        await message.answer('''Ну здравствуй, сталкер!
Вижу, ты тут впервые. Выбери одну из предложенных группировок.
Подробнее о боте можешь узнать, отправив команду /help ''', reply_markup=chose_faction_kb)
    else:
        await message.answer('''Ну, удачной охоты, сталкер''')


@dp.message_handler(commands=['help'])
async def help_info(message: types.Message):
    await message.answer('''Telegram бот-игра "S.T.A.L.K.E.R. Война группировок"
Вы являеетесь командиром одной из группировок сталкеров. Выберите одну из предложенных группировок, 
устраивайте рейды на мутантов, отправляйте сталкеров из своей группировки на поиски артефактов. 
Покупайте и продавайте товары у торговцев. Совершайте атаки на другие группировки и многое другое.
''')


@dp.message_handler(Text(equals=['Монолит', 'Свобода', 'Долг', 'Вольные сталкеры', 'Бандиты']))
async def chose_faction(message: types.Message):
    if not cur.execute('''SELECT faction FROM main WHERE user_id = ?''', (message.from_user.id,)).fetchone()[0]:
        cur.execute('''UPDATE main
        SET faction = (SELECT id FROM factions WHERE name = ?)
        WHERE user_id = ?''', (message.text, message.from_user.id))
        conn.commit()
        await message.answer("Привествуем тебя в рядах группировки \"{}\"!".format(message.text),
                             reply_markup=remove_keyboard)
    else:
        'Я тебя не понимаю. Используй /help для получения информации о боте'


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
