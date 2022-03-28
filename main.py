from telegram.ext import Updater, MessageHandler, Filters, ConversationHandler
from telegram.ext import CallbackContext, CommandHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove

with open('config/token', 'r', encoding='utf-8') as tokfile:
    TOKEN = tokfile.readline()


def help(update, context):
    update.message.reply_text('''Telegram бот-игра "S.T.A.L.K.E.R. Война группировок"
Вы являеетесь командиром одной из группировок сталкеров. Выберите одну из предложенных группировок, 
устраивайте рейды на мутантов, отправляйте сталкеров из своей группировки на поиски артефактов. 
Покупайте и продавайте товары у торговцев. Совершайте атаки на другие группировки и многое другое.
''', reply_markup=ReplyKeyboardRemove())


def start(update, context):
    markup = ReplyKeyboardMarkup([['Долг', 'Свобода', 'Монолит'], ['Бандиты', 'Вольные сталкеры']],
                                 one_time_keyboard=True)
    update.message.reply_text('''Ну здравствуй, сталкер!
Не будем тянуть волынку. Просто выбери одну из предложенных группировок''', reply_markup=markup)
    return 1


def stop(update, context):
    pass


def faction_chosen(update, context):
    faction = update.message.text
    print(faction)
    return ConversationHandler.END


def main():
    # Создаем апдейтер
    updater = Updater(TOKEN, use_context=True)

    # Получаем из него диспетчер сообщений.
    dp = updater.dispatcher

    chose_faction = ConversationHandler(
        entry_points=[CommandHandler('start', start)],

        states={
            1: [MessageHandler(Filters.text, faction_chosen)]
        },

        # Точка прерывания диалога. В данном случае — команда /stop.
        fallbacks=[CommandHandler('stop', stop)]
    )
    dp.add_handler(chose_faction)

    # Регистрируем обработчик в диспетчере.
    dp.add_handler(CommandHandler('start', start))
    dp.add_handler(CommandHandler('help', help))

    # Запускаем цикл приема и обработки сообщений.
    updater.start_polling()

    # Ждём завершения приложения.
    # (например, получения сигнала SIG_TERM при нажатии клавиш Ctrl+C)
    updater.idle()


# Запускаем функцию main() в случае запуска скрипта.
if __name__ == '__main__':
    main()
