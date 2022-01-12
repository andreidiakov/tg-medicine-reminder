# строннние библиотеки
import os
from dotenv import load_dotenv
load_dotenv() # считать переменные окружения

from time import sleep
import telebot
from telebot import types
from threading import Thread

# внутренние модули
from storage import Users_storage, Reminders_storage
from kit import Kit
from reminders import Reminders
from notifications import Notifications
from common_functions import create_custom_keyboard

bot = telebot.TeleBot(os.environ.get("TG_TOKEN")) # инициализируем бота
PRODUCTION = os.environ.get("PRODUCTION", False) == "True"

users = Users_storage()
reminders = Reminders_storage()
kit_controller = Kit(bot, users, reminders)
reminders_controller = Reminders(bot, users, reminders)
notifications_controller = Notifications(bot, users, reminders)

# старт
@bot.message_handler(commands=["start", "main"])
def start(m):
    print('main_start')

    users.add_user({'ID': m.chat.id})        
    bot.send_message(m.chat.id, "Вас приветствует Бот")
    keyboard = create_custom_keyboard(['Моя аптечка', 'Напоминания о приеме лекарств'])
    bot.send_message(m.chat.id, 
        text='Выберите в меню что вам интересно!',
        reply_markup=keyboard)
    bot.register_next_step_handler(m, main_menu_handler)

#  главное меню  команд
def main_menu_handler(m):
    print('main_main_menu_handler')

    if m.text == 'Напоминания о приеме лекарств':
        reminders_controller.list_reminders(m)
        reminders_controller.menu(m, callback=start)
    
    elif m.text == 'Моя аптечка':
        kit_controller.list_kit(m)
        kit_controller.menu(m, callback=start)
    
    else:
        bot.send_message(m.chat.id, 'Выберите действие в меню')
        bot.register_next_step_handler(m, main_menu_handler)

# прием сообщений со встроенной клавиатуры (кнопка в чате), так как у нее тип сообщения call
@bot.callback_query_handler(func=lambda call: True)
def InlineKeyboard_(call):
    bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id) #Убрать кнопки
    
    if 'chg_med' in call.data:
        kit_controller.change_amount_input_0(call.message, call.data[len('chg_med'):])

    elif 'del_med' in call.data:
        kit_controller.delete_medicine_0(call.message, call.data[len('chg_med'):])

    elif call.data == 'back_med':
        kit_controller.list_kit(call.message)
        kit_controller.menu(call.message)

    elif 'crt_rem'in call.data:
        reminders_controller.create_reminder_1(call.message, call.data[len('crt_rem'):])

    elif 'del_rem'in call.data:
        reminders_controller.delete_reminder_1(call.message, call.data[len('del_rem'):])

    elif call.data == 'back_rem':
        reminders_controller.list_reminders(call.message)
        reminders_controller.menu(call.message)

    elif 'ntf_suc' in call.data:
        notifications_controller.medicine_reminder_success(call.message, call.data[len('ntf_suc'):])

    else:
        bot.edit_message_text(call.message.chat.id, 
            message_id=call.message.message_id,
            text='Вы вернулись в главное меню', 
            reply_markup=start())

# вызов функции проверки наличия уведомлений в данный момент времени
def sending_notifications():
    while True:
        notifications_controller.send_medicine_reminders()
        sleep(60)

notifications_thread = {}

# Обработчик сообщений, если бот был перезапущен
@bot.message_handler(content_types=['text'])
def response(m):
    print(m.text)
    if (m.text in ['Напоминания о приеме лекарств', 'Моя аптечка']):
        main_menu_handler(m)
    else:
        start(m)

if __name__ == '__main__':  # Ожидать входящие сообщения
    notifications_thread = Thread(target=sending_notifications)
    notifications_thread.start() 
   
    bot.polling()
    
