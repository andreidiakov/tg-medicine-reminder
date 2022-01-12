import telebot
from telebot import types

from common_functions import create_custom_keyboard, number_input, times_input, times_output
from storage import Users_storage

class Reminders:
    def __init__(self, 
                 bot, 
                 users, 
                 reminders):
        self.bot = bot
        self.users = users
        self.reminders = reminders
        print('Создали напоминания')

    # главное меню уведомлений 
    def menu(self, m, callback=None):
        print('rmd_menu')

        if callback:
            self.callback = callback

        if not self.users.data[m.chat.id].phone_number:
            keyboard = types.ReplyKeyboardMarkup( resize_keyboard=True)
            button_phone = types.KeyboardButton(text='Поделиться номером телефона', request_contact=True) 
            back = types.KeyboardButton(text='Назад')
            keyboard.add(button_phone)
            keyboard.add(back)
            message = 'Поделитесь Вашим номером телефона, чтобы настроить уведомления'
        else:
            keyboard = create_custom_keyboard([
                    ['Создать напоминания'], 
                    ['Удалить напоминание'], 
                    ['Назад']
                ])
            message = 'Выберите в меню'
        self.bot.send_message(m.chat.id, 
            text= message,
            reply_markup= keyboard)
        self.bot.register_next_step_handler(m, self.menu_handler)

    # проверка наличия у пользователя уведомлений
    def check_users_reminders(self, m):
        print('rmd_check_users_reminders')

        reminders = self.reminders.get_users_reminders(m.chat.id)
        if not reminders or len(reminders)==0:
            self.bot.send_message(m.chat.id, 
                'У вас нет напоминаний. Чтобы добавить, нажмините "Создать напоминания"')
            self.bot.register_next_step_handler(m, self.menu_handler)
            return False
        return True

    # обработка выбора пользователя в меню
    def menu_handler(self, m):
        print('rmd_menu_handler')

        if m.text == 'Создать напоминания':
            self.create_reminder_0(m)

        elif m.text == 'Удалить напоминание':
            if self.check_users_reminders(m):
                self.delete_reminder_0(m)
        
        elif m.content_type == 'contact':
            phone_number = m.contact.phone_number
            self.users.data[m.chat.id].phone_number = phone_number
            self.users.update_user(self.users.data[m.chat.id])
            self.menu(m)
        
        else:
            if self.callback:
                self.callback(m)
            return

    # вывод всех уведомлений
    def list_reminders(self, m):
        print('rmd_list_reminders')

        self.bot.send_message(m.chat.id, 'Ваши уведомления')

        reminders = self.reminders.get_users_reminders_sorted_values(m.chat.id)
        if not reminders or len(reminders) < 1:
            self.bot.send_message(m.chat.id, "У вас нет настроенных уведомлений")
            return

        i = 1
        for reminder in reminders:
            self.bot.send_message(m.chat.id, "№{} - {}".format(i, reminder.to_string()))
            i+=1

    # создание новых уведомлений
    def create_reminder_0(self, m):
        print('rmd_create_reminder_0')
        
        user_medicines = self.users.get_user(m.chat.id).medicines

        if not user_medicines or len(user_medicines) == 0:
            self.bot.send_message(m.chat.id, 
                'У Вас нет лекарств в аптечке. Добавьте их, чтобы настроить напоминания.', reply_markup=types.ReplyKeyboardRemove())
            self.menu(m)
            return

        markup = types.InlineKeyboardMarkup()
        for key, item in user_medicines.items():
            msg = item.to_string()
            markup.add(telebot.types.InlineKeyboardButton(text = msg, callback_data = 'crt_rem'+ str(key)))
        markup.add(types.InlineKeyboardButton(text='Назад', callback_data = "back_rem"))

        self.bot.send_message(m.chat.id, 
            text='Нажмите на препарат, для которого Вы хотите добавить напоминания.', 
            reply_markup=types.ReplyKeyboardRemove())
        self.bot.send_message(m.chat.id, text='Список препаратов: ', reply_markup=markup)

    # обработка выбора
    def create_reminder_1(self, m, name):
        print('rmd_create_reminder_1')
        
        reminder = {'user_ID': m.chat.id, 'medicine_name': name}
        medicine = self.users.get_user(m.chat.id).medicines[name]

        self.bot.send_message(m.chat.id, "Выбранный препарат:\n"+ medicine.to_string())
        self.bot.send_message(m.chat.id, 
            'Введите дозировку (кол-во таблеток, капсул, миллилитров), которые надо принять за один раз.\nВведите 0 для выбора стандартной дозировки.')

        self.bot.register_next_step_handler(m, self.create_reminder_2, reminder)

    # обработка дозировки 
    def create_reminder_2(self, m, reminder):
        print('rmd_create_reminder_2')
        
        dosage = number_input(self.bot, m, True)

        if isinstance(dosage, bool) and dosage == False:
            self.bot.register_next_step_handler(m, self.create_reminder_2, reminder)
            return

        if dosage == 0.0:
            user = self.users.get_user(m.chat.id)
            reminder['dosage'] = user.medicines[reminder['medicine_name']].dosage
        else:
            reminder['dosage'] =  dosage

        self.bot.send_message(m.chat.id, 
            'Введите время или несколько времен (через пробел или запятую), в которые вам надо напомнить о приеме препарата')

        self.bot.register_next_step_handler(m, self.create_reminder_3, reminder)

    # подтверждение сохранения
    def create_reminder_3(self, m, reminder):
        print('rmd_create_reminder_3')
        
        times = times_input(self.bot, m)
        if times == False:
            self.bot.register_next_step_handler(m, self.create_reminder_3, reminder)
            return
        
        reminder['times'] = times

        keyboard = create_custom_keyboard(['Сохранить', 'Начать заново'])
        self.bot.send_message(m.chat.id, 
            text="{}, дозировка: {}, время напоминаний: {}".format(
                reminder['medicine_name'],
                reminder['dosage'],
                times_output(reminder['times'])), 
            reply_markup=keyboard)
        self.bot.register_next_step_handler(m, self.create_reminder_4, reminder)

    # сохранение
    def create_reminder_4(self, m, reminder):
        print('rmd_create_reminder_4')

        if m.text == 'Сохранить':
            try:
                self.reminders.add_reminder(reminder)
                n = len(reminder['times'])
                id_reminders = ''
                for i in range(-1, -n-1,-1):
                    id_reminders += 'id' + str(int(list(self.reminders.data)[i][2:])) + ' '
                self.users.update_medicine_id_reminders(reminder['user_ID'], reminder['medicine_name'], id_reminders.rstrip())
            except Exception as e:
                print(e)
            self.bot.send_message(m.chat.id, 'Напоминания сохранены')
            
            self.list_reminders(m)
            self.menu(m) 

        elif m.text == 'Начать заново':
            self.create_reminder_0(m)

        else: 
            self.bot.send_message(m.chat.id, 'Выберите действие в меню')
            self.bot.register_next_step_handler(m, self.create_reminder_3, reminder)

    # удаление
    def delete_reminder_0(self, m):
        print('rmd_delete_reminder_0')

        markup = types.InlineKeyboardMarkup()
        reminders = self.reminders.get_users_reminders_sorted_values(m.chat.id)

        for item in reminders:
            msg = '{0} – {1}, дозировка {2}'.format(
                item.time, 
                item.medicine_name, 
                item.dosage)
            markup.add(telebot.types.InlineKeyboardButton(text= msg, callback_data = 'del_rem'+ str(item.ID)))
        markup.add(types.InlineKeyboardButton(text='Назад', callback_data = "back_rem"))
        
        self.bot.send_message(m.chat.id, 
            text='Нажмите на уведомление, которое нужно удалить:', 
            reply_markup=types.ReplyKeyboardRemove())
        self.bot.send_message(m.chat.id, text='Уведомления: ', reply_markup=markup)

    # обработка выбора удаления + сохранение изменений
    def delete_reminder_1(self, m, name):
        print('rmd_delete_reminder_1')
        try:
            self.users.reduce_medicine_id_reminders( m.chat.id, self.reminders.data[name].medicine_name, name)
        except Exception as e:
            print(e)

        try:
            self.reminders.delete_reminder(name, m.chat.id)
        except Exception as e:
            print(e)
        
        self.bot.send_message(m.chat.id, 'Уведомление удалено')
            
        self.list_reminders(m)
        self.menu(m) 
