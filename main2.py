import logging
import sqlite3

from aiogram import Bot, Dispatcher, executor, types
from config.tg_token import API_TOKEN
from keyboards import chose_faction_kb, remove_keyboard, hire_stalker_kb, menu_kb
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


def get_info_about_user(user_id):
    n_stalk = cur.execute('''SELECT n_stalk FROM main WHERE user_id = ?''',
                          (user_id,)).fetchone()[0]
    cost = n_stalk * 4 + 5
    power_f = n_stalk * 7
    money = cur.execute('''SELECT money FROM main WHERE user_id = ?''',
                        (user_id,)).fetchone()[0]
    return (n_stalk, power_f, cost, money)


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    if not user_is_registered(message):
        cur.execute('''INSERT INTO main(user_id, money, power_of_faction, n_stalk) VALUES (?, 10, 0, 0)''',
                    (message.from_user.id,))
        conn.commit()
        await message.answer('''[В разработке]
Ну, здравствуй, сталкер!
Вижу, ты тут впервые. Выбери, командиром какой из предложенных группировок ты станешь.
Подробнее о боте можешь узнать, отправив команду /help
[В разработке]''', reply_markup=chose_faction_kb)
    else:
        await message.answer('''Удачной дороги, сталкер!''')


@dp.message_handler(commands=['help'])
async def help_info(message: types.Message):
    await message.answer('''Telegram бот-игра "S.T.A.L.K.E.R. Война группировок"
Возглавьте одну из предложенных группировок, 
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
                             reply_markup=menu_kb)
    else:
        await message.answer('Я тебя не понимаю. Используй /help для получения информации о боте', reply_markup=menu_kb)


@dp.message_handler(commands=['recruitment'])
async def recruitment(message: types.Message):
    info = get_info_about_user(message.from_user.id)
    await message.answer('''☢На данный момент сталкеров в группе: {}
☢Мощь группировки: {}
☢Стоимость найма: {}
☢Рублей: {}'''.format(info[0], info[1], info[2], info[3]), reply_markup=hire_stalker_kb)


async def hired_update_text_and_db(message: types.Message, n_stalk, money, cost, power_f, purchase_is_done):
    if purchase_is_done:
        cur.execute('''UPDATE main
        SET money = ?,
        power_of_faction = ?, 
        n_stalk = ?
        WHERE user_id = ?''', (money, power_f, n_stalk, message.chat.id))  # передется chat.id, а не from_user.id,
        # т.к. в эту функцию передается сообщение не от пользователя, а от callback'a
        conn.commit()
        await message.edit_text('''☢На данный момент сталкеров в группе: {}
☢Мощь группировки: {}
☢Стоимость найма: {}
☢Рублей: {}'''.format(n_stalk, power_f, cost, money), reply_markup=hire_stalker_kb)
    else:
        await message.edit_text('''☢На данный момент сталкеров в группе: {}
☢Мощь группировки: {}
☢Стоимость найма: {}
☢Рублей: {}
Маловато у тебя денег, сталкер'''.format(n_stalk, power_f, cost, money))


@dp.callback_query_handler(Text('hire'))
async def hire_callback(call: types.CallbackQuery):
    info = get_info_about_user(call.from_user.id)
    money = int(info[3])
    cost = int(info[2])
    n_stalk = int(info[0])
    power_f = int(info[1])
    if money >= cost:
        new_n_stalk = n_stalk + 1
        power_f = new_n_stalk * 7
        money -= cost
        cost = new_n_stalk * 4 + 5
        await hired_update_text_and_db(call.message, new_n_stalk, money, cost, power_f, True)
    else:
        await hired_update_text_and_db(call.message, n_stalk, money, cost, power_f, False)
    await call.answer()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
