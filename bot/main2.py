import logging
import sqlite3
from random import random, shuffle, sample
from requests import get

from config.tg_token import API_TOKEN
from aiogram import Bot, Dispatcher, executor, types
from keyboards import chose_faction_kb, remove_keyboard, hire_stalker_kb, menu_kb
from aiogram.dispatcher.filters import Text
from aiogram.types.input_file import InputFile

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.schedulers import SchedulerAlreadyRunningError

from pymorphy2 import MorphAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

conn = sqlite3.connect('db/users_info.db')
cur = conn.cursor()

conn2 = sqlite3.connect('../api/db/artifacts.db')
cur2 = conn2.cursor()

sheduler = AsyncIOScheduler()

morph = MorphAnalyzer()
rub = morph.parse('рубль')[0]


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
    return n_stalk, power_f, cost, money


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
    await dp.bot.set_my_commands([
        types.BotCommand("help", "Информация о боте"),
        types.BotCommand("recruitment", "Наем сталкеров"),
        types.BotCommand("art_raid", "Вылазка за артефактом")
    ])
    await message.answer('''Telegram бот-игра "S.T.A.L.K.E.R. Война группировок"
Возглавьте одну из предложенных группировок, 
устраивайте рейды на мутантов, отправляйте сталкеров из своей группировки на поиски артефактов. 
Покупайте и продавайте товары у торговцев. Совершайте атаки на другие группировки.
Доступно меню команд (кнопка слева от поля ввода сообщения)
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
☢Стоимость найма: {} {}
☢Денег: {} {}'''.format(info[0], info[1], info[2], rub.make_agree_with_number(info[2]).word, info[3],
                        rub.make_agree_with_number(info[3]).word), reply_markup=hire_stalker_kb)


async def hired_update_text_and_db(message: types.Message, n_stalk, money, cost, power_f, purchase_is_done):
    if purchase_is_done:
        cur.execute('''UPDATE main
        SET money = ?,
        power_of_faction = ?, 
        n_stalk = ?
        WHERE user_id = ?''', (money, power_f, n_stalk, message.chat.id))  # передается chat.id, а не from_user.id,
        # т.к. в эту функцию передается сообщение не от пользователя, а от callback'a
        conn.commit()
        await message.edit_text('''☢На данный момент сталкеров в группе: {}
☢Мощь группировки: {}
☢Стоимость найма: {} {}
☢Денег: {} {}'''.format(n_stalk, power_f, cost, rub.make_agree_with_number(cost).word, money,
                        rub.make_agree_with_number(money).word), reply_markup=hire_stalker_kb)
    else:
        await message.edit_text('''☢На данный момент сталкеров в группе: {}
☢Мощь группировки: {}
☢Стоимость найма: {} {}
☢Денег: {} {}
Маловато у тебя денег, сталкер'''.format(n_stalk, power_f, cost, rub.make_agree_with_number(cost).word, money,
                                         rub.make_agree_with_number(money).word))


@dp.callback_query_handler(Text('hire'))
async def hire_callback(call: types.CallbackQuery):
    info = get_info_about_user(call.from_user.id)
    money = info[3]
    cost = info[2]
    n_stalk = info[0]
    power_f = info[1]
    if money >= cost:
        new_n_stalk = n_stalk + 1
        power_f = new_n_stalk * 7
        money -= cost
        cost = new_n_stalk * 4 + 5
        await hired_update_text_and_db(call.message, new_n_stalk, money, cost, power_f, True)
    else:
        await hired_update_text_and_db(call.message, n_stalk, money, cost, power_f, False)
    await call.answer()


@dp.message_handler(commands='art_raid')
async def raid_for_artifact(message: types.Message):
    may_send_stalkers = True
    jobs = sheduler.get_jobs()

    for j in jobs:
        if j.name == 'raid':
            may_send_stalkers = False
            break

    if may_send_stalkers:
        arts = get('http://127.0.0.1:5000/arts').json()
        arts = sorted(arts['arts'], key=lambda x: x['chance'])
        chance = random()
        art = None
        photo, caption = None, None
        for i in range(len(arts)):
            if chance <= arts[i]['chance']:
                art = arts[i]
                break
            else:
                continue
        if art:
            photo = InputFile(art['path'])
            caption = art['description']

        trigger = IntervalTrigger(seconds=10)
        sheduler.add_job(raid, args=[message.chat.id, photo, caption, str(art['id'])], trigger=trigger)
        try:
            sheduler.start()
        except SchedulerAlreadyRunningError:
            pass
        await message.answer('Сталкеры отправлены на вылазку. Вернутся через 10 секунд')
    else:
        await message.answer('Сталкеры уже отправлены на вылазку. Дождитесь её окончания')


async def raid(chat_id, photo, caption, art_id):
    if photo:
        arts = cur.execute('''SELECT arts FROM main WHERE user_id = ?''',
                           (chat_id,)).fetchone()[0]
        if arts == 0:
            arts = f'{art_id};'
        else:
            arts = f'{arts}{art_id};'
        cur.execute('''UPDATE main
        SET arts = ?
        WHERE user_id = ?''', (arts, chat_id))
        conn.commit()
        await bot.send_photo(chat_id, photo, caption)
    else:
        await bot.send_message(chat_id, 'Вылазка оказалась безрезультатной, артефактов не найдено')
    jobs = sheduler.get_jobs()
    if not jobs:
        sheduler.pause()
    sheduler.remove_job(jobs[0].id)


@dp.message_handler(commands=['shop'])
async def shop(message: types.Message):
    arts = cur2.execute('''SELECT id, name, price FROM artifacts''').fetchall()
    can_sell = sample(arts, k=3)
    await message.answer(f'''Торговец: Сидорович
Покупает:
    {can_sell[0][1]}. Цена: {can_sell[0][2]} {rub.make_agree_with_number(can_sell[0][2]).word}
    {can_sell[1][1]}. Цена: {can_sell[1][2]} {rub.make_agree_with_number(can_sell[1][2]).word}
    {can_sell[2][1]}. Цена: {can_sell[2][2]} {rub.make_agree_with_number(can_sell[2][2]).word}''')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
