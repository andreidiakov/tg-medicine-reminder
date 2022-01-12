import telebot
from telebot import types
import threading
from time import sleep
import os

from storage import Reminder
from common_functions import create_custom_keyboard, get_current_time
from calls import make_call

TIME_BETWEEN_REMINDERS = int(os.environ.get("TIME_BETWEEN_REMINDERS", 60))
MAXIMUM_REREAT_REMINDER = int(os.environ.get("MAXIMUM_REREAT_REMINDER", 3))

class Notifications:
    def __init__(self, 
                 bot, 
                 users, 
                 reminders):
        self.bot = bot
        self.users = users
        self.reminders = reminders
        self.queue = {}
        # self.time = False

        print('Создали нотификации')

    def send_medicine_reminders(self):
        print('send_medicine_reminders')

        reminders = self.reminders.get_reminders_by_time(get_current_time())

        # код для отладки уведомлений
        # if self.time:
        #     reminders = self.reminders.get_reminders_by_time("12:34")
        # self.time = False

        for item in reminders:
            if not item.ID in self.queue:
                thread = threading.Thread(target=self.send_first_reminder, name=item.ID, args=(item, ))
                thread.start()
                self.queue[item.ID] = thread

    def send_first_reminder(self, item):
        print('send_first_reminder')

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text='✅ Я принял лекарство', callback_data = "ntf_suc"+item.ID))
        message_id = self.bot.send_message(item.user_ID,
            text="Примите препарат - {}, дозировка {}".format(item.medicine_name, item.dosage),
            reply_markup=markup)
        sleep(TIME_BETWEEN_REMINDERS)
        self.send_second_reminder(item, message_id)

    def send_second_reminder(self, item, message_id):
        print('send_second_reminder')

        t = threading.currentThread()
        i = 1
        while getattr(t, "do_run", True):
            i += 1
            if i > MAXIMUM_REREAT_REMINDER:
                self.queue[t.name].do_run = False
                del self.queue[t.name]
                break

            message_id = self.bot.send_message(item.user_ID,
                text="Повторно напоминаем. Примите препарат - {}, дозировка {}. \n Подтвердите принятие препарата нажатием на кнопку ✅ Я принял лекарство"
                .format(item.medicine_name, item.dosage))
            
            if (i == 3):
                phone_number = self.users.get_user(item.user_ID).phone_number
                if (phone_number):
                    self.programm_call(item.medicine_name, item.dosage, phone_number)
            
            sleep(TIME_BETWEEN_REMINDERS)
            self.bot.delete_message(item.user_ID, message_id.message_id)

    def medicine_reminder_success(self, m, ID, callback=None):
        print('medicine_reminder_success')

        reminder = self.reminders.get_reminder(ID)
        user = self.users.reduce_medicine(reminder.user_ID, reminder.medicine_name, reminder.dosage)
        try:
            self.queue[ID].do_run = False
            del self.queue[ID]
        except Exception as e:
            print(e)

        self.bot.send_message(reminder.user_ID, "Вы - молодец! Данные в аптечке обновлены.")

        balance = user.medicines[reminder.medicine_name].balance
        consumption = self.reminders.get_users_medicine_consumption(reminder.user_ID, reminder.medicine_name)

        if (balance/consumption<4):
            def format_days_left(num):
                if num < 0:
                    num = 0
                
                answers = {
                    0: 'сегодня',
                    1: 'завтра',
                    2: 'через день',
                    3: 'через два дня'
                }

                return answers[int(num)]

            keyboard = types.InlineKeyboardMarkup()
            url_button = types.InlineKeyboardButton(text="Заказать онлайн", url="https://www.eapteka.ru/search/?q={}".format(reminder.medicine_name))
            keyboard.add(url_button)

            self.bot.send_message(reminder.user_ID, 
                text="Внимание! Данное лекарство закончится {}. Не забудьте купить его заранее!".format(format_days_left(balance/consumption)),
                reply_markup=keyboard)

        if callback:
            callback(m)

    def programm_call(self, medicine_name, dosage, phone_number):
        print('programm_call')

        make_call(phone_number, f'Напоминаем Вам принять препарат {medicine_name}. Его дозиравка {dosage}.\
            Подтвердите принятие препарата в чате с ботом нажатием кнопки Я принял лекарство.')