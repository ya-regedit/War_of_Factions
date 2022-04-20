import logging
import sqlite3
from random import random, sample, uniform, randint
from collections import Counter
from requests import get

from config.tg_token import API_TOKEN
from aiogram import Bot, Dispatcher, executor, types
from keyboards import chose_faction_kb, remove_keyboard, hire_stalker_kb, merchants_kb, buy_kb
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
sht = morph.parse('штука')[0]

can_sell_global = []


def user_is_registered(msg):
    if not cur.execute('''SELECT * FROM main WHERE user_id = ?''', (msg.from_user.id,)).fetchone():
        return False
    return True


def get_info_about_user(user_id):
    n_stalk = cur.execute('''SELECT n_stalk FROM main WHERE user_id = ?''',
                          (user_id,)).fetchone()[0]
    cost = 2 ** n_stalk
    power_f = n_stalk * 7
    money = cur.execute('''SELECT money FROM main WHERE user_id = ?''',
                        (user_id,)).fetchone()[0]
    faction = cur.execute('''SELECT name FROM factions
    WHERE id = (SELECT faction FROM main WHERE user_id = ?)''', (user_id,)).fetchone()[0]
    mutants = cur.execute('''SELECT mutants FROM main WHERE user_id = ?''', (user_id,)).fetchone()[0]
    return {'n_stalk': n_stalk, 'power_f': power_f, 'cost': cost, 'money': money, 'faction': faction,
            'mutants': mutants}


def get_info_about_arts(user_id):
    money = get_info_about_user(user_id)['money']
    arts = cur2.execute('''SELECT id, name, price FROM artifacts''').fetchall()
    arts_dict = {}
    for a in arts:
        arts_dict[str(a[0])] = a[1], a[2]
    res = cur.execute('''SELECT arts FROM main WHERE user_id = ?''',
                      (user_id,)).fetchone()[0]
    if res == '0' or not res:
        answer_str = 'Тут пусто'
        arts_on_hand_l = ['0']
        arts_on_hand_d = Counter(['0'])
    else:
        if isinstance(res, int):
            arts_on_hand_l = [str(res)]
            arts_on_hand_d = Counter([str(res)])
        else:
            arts_on_hand_l = sorted(res.split(';'))
            arts_on_hand_d = Counter(sorted(res.split(';')))
        answer_str = '\n'.join(
            '☢Артефакт: {}. {} {}'.format(arts_dict[str(art_id)][0], num,
                                          sht.make_agree_with_number(num).word) for
            art_id, num in arts_on_hand_d.items())
    return {'arts': arts, 'money': money, 'answer_str': answer_str, 'arts_on_hand_d': arts_on_hand_d,
            'art_dict': arts_dict, 'arts_on_hand_l': arts_on_hand_l}


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    if not user_is_registered(message):
        await dp.bot.set_my_commands([
            types.BotCommand("help", "Информация о боте"),
            types.BotCommand("recruitment", "Наем сталкеров"),
            types.BotCommand("art_raid", "Вылазка за артефактом"),
            types.BotCommand('shop', 'Сбыт артефактов'),
            types.BotCommand('info', 'Информация о группировке'),
            types.BotCommand('attack', 'Атака на сталкеров другой группировки')
        ])
        await message.answer('''Ну, здравствуй, сталкер!
Вижу, ты тут впервые. Выбери, командиром какой из предложенных группировок ты станешь.
Подробнее о боте можешь узнать, отправив команду /help''', reply_markup=chose_faction_kb)
    else:
        await message.answer('''Удачной дороги, сталкер!''')


@dp.message_handler(commands=['help'])
async def help_info(message: types.Message):
    await message.answer('''Telegram бот-игра "S.T.A.L.K.E.R. Война группировок"
Вы возглавляете сталкерскую группировку.
Отправляйте сталкеров из своей группировки на поиски артефактов. 
Покупайте и продавайте товары у торговцев. Совершайте атаки на другие группировки.
Изучите меню команд (кнопка слева от поля ввода сообщения)
''')


@dp.message_handler(Text(equals=['Монолит', 'Свобода', 'Долг', 'Чистое небо', 'Бандиты']))
async def chose_faction(message: types.Message):
    if not user_is_registered(message):
        cur.execute('''INSERT INTO main(user_id, money, power_of_faction, n_stalk) VALUES (?, 10, 0, 0)''',
                    (message.from_user.id,))
        cur.execute('''UPDATE main
        SET faction = (SELECT id FROM factions WHERE name = ?)
        WHERE user_id = ?''', (message.text, message.from_user.id))
        conn.commit()
        await message.answer("""Привествуем тебя в рядах группировки \"{}\"!
В целях ознакомления с ботом, введи команду /help""".format(message.text), reply_markup=remove_keyboard)
    else:
        await message.answer('Я тебя не понимаю. Используй /help для получения информации о боте')


@dp.message_handler(commands=['recruitment'])
async def recruitment(message: types.Message):
    info = get_info_about_user(message.from_user.id)
    await message.answer('''☢На данный момент сталкеров в группе: {}
☢Мощь группировки: {}
☢Стоимость найма: {} {}
☢Денег: {} {}'''.format(info['n_stalk'], info['power_f'], info['cost'], rub.make_agree_with_number(info['cost']).word,
                        info['money'],
                        rub.make_agree_with_number(info['money']).word), reply_markup=hire_stalker_kb)


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
    money = info['money']
    cost = info['cost']
    n_stalk = info['n_stalk']
    power_f = info['power_f']
    if money >= cost:
        new_n_stalk = n_stalk + 1
        power_f = new_n_stalk * 7
        money -= cost
        cost = 2 ** new_n_stalk
        await hired_update_text_and_db(call.message, new_n_stalk, money, cost, power_f, True)
    else:
        await hired_update_text_and_db(call.message, n_stalk, money, cost, power_f, False)
    await call.answer()


@dp.message_handler(commands='art_raid')
async def raid_for_artifact(message: types.Message):
    info = get_info_about_user(message.from_user.id)
    print(info['mutants'])
    if info['mutants'] > 5:
        trigger = IntervalTrigger(seconds=10)
        sheduler.add_job(attack,
                         args=[message.chat.id, info['n_stalk'], info['money'], info['power_f'], True, info['mutants']],
                         trigger=trigger)
        try:
            sheduler.start()
        except SchedulerAlreadyRunningError:
            pass
        await message.answer('''Внимание, обнаружено крупное скопление мутантов около нашей базы!!!
Потребуется какое-то время, чтобы их уничтожить, затем снова отправьте сталкеров на поиск артефактов''')
    else:
        may_send_stalkers = True
        jobs = sheduler.get_jobs()

        for j in jobs:
            if j.name in ('raid', 'attack'):
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
                art_id = str(art['id'])
            else:
                art_id = None

            trigger = IntervalTrigger(seconds=10)
            sheduler.add_job(raid, args=[message.chat.id, photo, caption, art_id, info['mutants']], trigger=trigger)
            try:
                sheduler.start()
            except SchedulerAlreadyRunningError:
                pass
            await message.answer('Сталкеры отправлены на вылазку. Вернутся через 10 секунд')
        else:
            await message.answer('Сталкеры уже задействованы. Дождитесь их возвращения на базу')


async def raid(chat_id, photo, caption, art_id, mut):
    if photo:
        arts = cur.execute('''SELECT arts FROM main WHERE user_id = ?''',
                           (chat_id,)).fetchone()[0]
        if arts == 0:
            arts = f'{art_id}'
        else:
            arts = f'{arts};{art_id}'
        cur.execute('''UPDATE main
        SET arts = ?,
        mutants = ?
        WHERE user_id = ?''', (arts, mut + 1, chat_id))
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
    await message.answer('''Тут распологается наш бессменный торговец - Сидорович''', reply_markup=merchants_kb)


async def shop_update_text_and_db(message: types.Message, can_sell, money, answer_str):
    await message.edit_text(f'''Торговец: Сидорович
    
Покупает:
{can_sell[0][1]}. Цена: {can_sell[0][2]} {rub.make_agree_with_number(can_sell[0][2]).word}
{can_sell[1][1]}. Цена: {can_sell[1][2]} {rub.make_agree_with_number(can_sell[1][2]).word}
{can_sell[2][1]}. Цена: {can_sell[2][2]} {rub.make_agree_with_number(can_sell[2][2]).word}

Ваш инвентарь: 
{answer_str}

Денег на счету: {money} {rub.make_agree_with_number(money).word}''', reply_markup=buy_kb)


@dp.callback_query_handler(Text('merch'))
async def shop_callback(call: types.CallbackQuery):
    global can_sell_global
    info = get_info_about_arts(call.from_user.id)
    can_sell_global = sample(info['arts'], k=3)
    await shop_update_text_and_db(call.message, can_sell_global, info['money'], info['answer_str'])
    await call.answer()


@dp.callback_query_handler(Text(equals=['art1', 'art2', 'art3', 'art4', 'art5']))
async def art_purchase_callback(call: types.CallbackQuery):
    info = get_info_about_arts(call.from_user.id)
    user_info = get_info_about_user(call.from_user.id)

    arts = info['art_dict']

    if call.data[-1] in info['arts_on_hand_l']:
        if arts[call.data[-1]][0] in [e[1] for e in can_sell_global]:
            money = user_info['money'] + arts[call.data[-1]][1]
            info['arts_on_hand_l'].remove(call.data[-1])
            if info['arts_on_hand_l']:
                new_art_str = ';'.join(info['arts_on_hand_l'])
            else:
                new_art_str = '0'

            cur.execute('''UPDATE main
            SET money = ?,
            arts = ?
            WHERE user_id = ?''', (money, new_art_str, call.from_user.id))
            conn.commit()
            info = get_info_about_arts(call.from_user.id)

            await shop_update_text_and_db(call.message, can_sell_global, info['money'],
                                          info['answer_str'])
        else:
            await shop_update_text_and_db(call.message, can_sell_global, info['money'],
                                          info['answer_str'] + '\n\nСейчас мне это не нужно, зайди попозже')
    await call.answer()


@dp.message_handler(commands=['info'])
async def progress_info(message: types.Message):
    info = get_info_about_user(message.from_user.id)
    info2 = get_info_about_arts(message.from_user.id)
    faction = info['faction']

    photo = InputFile(f'C:/Users/Invertor/PycharmProjects/pythonProject/War_of_Factions/api/data/img/{faction}.png')
    caption = f"""Группировка: {faction}
Мощь группировки: {info['power_f']}
Средств на счету: {info['money']} {rub.make_agree_with_number(info['money']).word}

Инвентарь:
{info2['answer_str']}"""
    await bot.send_photo(message.from_user.id, photo, caption)


@dp.message_handler(commands=['attack'])
async def attack_other_faction(message: types.Message):
    may_send_stalkers = True
    jobs = sheduler.get_jobs()
    info = get_info_about_user(message.from_user.id)
    if info['n_stalk'] >= 5:
        for j in jobs:
            if j.name in ('attack', 'raid'):
                may_send_stalkers = False
                break

        if may_send_stalkers:
            trigger = IntervalTrigger(seconds=10)
            sheduler.add_job(attack, args=[message.chat.id, info['n_stalk'], info['money'], info['power_f'], False,
                                           info['mutants']],
                             trigger=trigger)
            try:
                sheduler.start()
            except SchedulerAlreadyRunningError:
                pass
            await message.answer('Атака началась! Сталкеры вернутся через 10 секунд')
        else:
            await message.answer('Сталкеры уже задействованы. Дождитесь их возвращения на базу')
    else:
        await message.answer('Твой отряд еще недостаточно силен для совершения нападений')


async def attack(chat_id, n_stalk, money, power_f, mutant_attack, mut):
    if not mutant_attack:
        if power_f < 100:
            percent = uniform(0.0, 0.7)
        elif 100 < power_f < 300:
            percent = uniform(0.0, 0.5)
        elif 300 < power_f < 500:
            percent = uniform(0.0, 0.3)
        else:
            percent = uniform(0.0, 0.2)
        new_n_stalk = round(n_stalk * (1 - percent))
        stalk_lost = n_stalk - new_n_stalk
        profit = randint(1, n_stalk) * 14
        cur.execute('''UPDATE main
        SET n_stalk = ?,
        money = ?,
        mutants = ?
        WHERE user_id = ?''', (new_n_stalk, money + profit, mut + 1, chat_id))
        conn.commit()
        await bot.send_message(chat_id, f'''Атака завершена
Потеряно сталкеров: {stalk_lost}
Захвачено средств: {profit} {rub.make_agree_with_number(profit).word}''')
    else:
        cur.execute('''UPDATE main
        SET mutants = ?
        WHERE user_id = ?''', (0, chat_id))
        conn.commit()
        await bot.send_message(chat_id, 'Атака мутантов отбита')
    jobs = sheduler.get_jobs()
    if not jobs:
        sheduler.pause()
    sheduler.remove_job(jobs[0].id)


@dp.message_handler()
async def sink_msg(message: types.Message):
    if user_is_registered(message):
        await message.answer('Команда не распознана')
    else:
        await message.answer('''Приветствую, телеграмм пользователь! 
Ты попал в чат небольшим ботом-игрой про отряд сталкеров
Напиши /start чтобы начать''')


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
