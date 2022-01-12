import telebot
from telebot import types
from storage import Medicine

from common_functions import create_custom_keyboard, number_input

class Kit:
    def __init__(self, 
                 bot, 
                 users, 
                 reminders):
        self.bot = bot
        self.users = users
        self.reminders = reminders
        print('Создали кит')
    
    # меню аптечки
    def menu(self, m, callback=None):
        print('kit_menu')

        if callback:
            self.callback = callback


        keyboard = create_custom_keyboard([
                ['Добавить', 'Купить'],
                ['Изменить кол-во', 'Удалить', 'Найти инструкцию'],
                ['Главное меню']
            ])
        if not self.check_users_kit(m):
            keyboard = create_custom_keyboard([
                    ['Добавить'],
                    ['Главное меню']
                ])

        self.bot.send_message(m.chat.id, 
            text='Выберите в меню',
            reply_markup=keyboard)
        self.bot.register_next_step_handler(m, self.menu_handler)

    # проверка есть ли у пользователя сохраненные препараты. 
    # если нет, то другое меню
    def check_users_kit(self, m):
        print('kit_check_users_kit')

        user = self.users.get_user(m.chat.id)
        if not user or len(user.medicines)==0:
            return False
        return True

    # обработка выбора пользователя в меню
    def menu_handler(self, m):
        print('kit_menu_handler')
        
        if m.text == 'Добавить':
            medicine = {}
            self.new_med_0(m, medicine)

        elif m.text == 'Купить':
            self.buy_medicine(m)

        elif m.text == 'Изменить кол-во':
            self.change_amount_keyboard(m)
       
        elif m.text == 'Удалить':
            self.delete_medicine_keyboard(m)

        elif m.text == 'Найти инструкцию':
            self.instructinon(m)

        else:
            if self.callback:
                self.callback(m)
            return

    # вывести список препаратов 
    def list_kit(self, m):
        print('kit_list_kit')
        
        self.bot.send_message(m.chat.id, 'Ваша аптечка')

        user = self.users.get_user(m.chat.id)
        if not user.medicines or len(user.medicines)<1:
            self.bot.send_message(user.ID, 'У Вас нет лекарств в аптечке. ')
            return
        medicines = user.medicines

        i = 1
        for item in medicines.values():
            self.bot.send_message(user.ID, '№{} – {}'.format(i, item.to_string()))
            i += 1

    # добавление препарата
    # вопрос про имя
    def new_med_0(self, m, medicine={}):
        print('kit_new_med_0')

        self.bot.send_message(m.chat.id, 
                text = 'Введите название препарата', 
                reply_markup = types.ReplyKeyboardRemove())
        self.bot.register_next_step_handler(m, self.new_med_1, medicine)

    # имя + вопрос про запасы
    def new_med_1(self, m, medicine):
        print('kit_new_med_1')

        medicine['name'] = m.text
        self.bot.send_message(m.chat.id, 
            text = 'Введите количество таблеток (капсул, миллилитров), которые у Вас в наличии')
        self.bot.register_next_step_handler(m, self.new_med_2, medicine)

    # запасы + вопрос про стандартная дозировка
    def new_med_2(self, m, medicine):
        print('kit_new_med_2')

        balance = number_input(self.bot, m) 
        if balance == False:
            self.bot.register_next_step_handler(m, self.new_med_2, medicine)
            return
        medicine['balance'] = balance

        self.bot.send_message(m.chat.id, 
            text = 'Введите стандартную дозировку')
        self.bot.register_next_step_handler(m, self.new_med_3, medicine)

    # запасы + стандартная дозировка
    def new_med_3(self, m, medicine):
        print('kit_new_med_3')

        dosage = number_input(self.bot, m) 
        if dosage == False:
            self.bot.register_next_step_handler(m, self.new_med_3, medicine)
            return
        medicine['dosage'] = dosage
        medicine['id_remineders'] = ''

        keyboard = create_custom_keyboard(['Сохранить', 'Начать заново'])
        self.bot.send_message(m.chat.id, 
            text=medicine['name'] + ". Оставшихся таблеток: " + str(medicine['balance']) + ". Стандартная дозировка: " + str(medicine['dosage']), 
            reply_markup=keyboard)
        self.bot.register_next_step_handler(m, self.new_med_4, medicine)
    
    # сохранить
    def new_med_4(self, m, medicine):
        print('kit_new_med_4')

        if m.text == 'Сохранить':
            try:
                self.users.add_medicine(m.chat.id, medicine)
            except Exception as e:
                print(e)
            
            self.bot.send_message(m.chat.id, 'Препарат сохранен')
            
            self.list_kit(m)
            self.menu(m) 
        
        elif m.text == 'Начать заново':
            medicine = {}
            self.new_med_0(m, medicine)
        
        else: 
            self.bot.send_message(m.chat.id, 'Выберите действие в меню')
            self.bot.register_next_step_handler(m, self.new_med_3, medicine)

    # функция изменения количества препарата у пользователя
    def change_amount_keyboard(self, m):
        print('kit_change_amount_keyboard')

        markup = types.InlineKeyboardMarkup()
        medicines = self.users.get_user(m.chat.id).medicines;

        for item in medicines.values():
            msg = '{} Кол-во: {}'.format(item.name, item.balance)
            markup.add(telebot.types.InlineKeyboardButton(text= msg, callback_data = 'chg_med'+ str(item.name)))
        markup.add(types.InlineKeyboardButton(text='Назад', callback_data = "back_med"))
        
        self.bot.send_message(m.chat.id, 
            text='Нажмите на препарат, количество которого Вы хотите изменить', 
            reply_markup=types.ReplyKeyboardRemove())
        self.bot.send_message(m.chat.id, text='Список препаратов: ', reply_markup=markup)

    # ввод нового количества
    def change_amount_input_0(self, m, name): 
        print('kit_list change_amount_input_0')

        self.bot.send_message(m.chat.id, 'Введите новое количество')  
        self.bot.register_next_step_handler(m, self.change_amount_input_1, name)

    # проверка + сохранение
    def change_amount_input_1(self, m, name):
        print('kit_change_amount_input_1')

        try:
            if float(m.text) > 0:
                balance = float(m.text)
                try:
                    self.users.update_medicine(m.chat.id, name, 'balance', balance)
                except Exception as e:
                    print(e)
                self.bot.send_message(m.chat.id, 'Данные обновлены')
                    
                self.list_kit(m)
                self.menu(m) 
            else:
                self.bot.send_message(m.chat.id, 'Введите положительное число')
                self.change_amount_input_0(m, name)
        except ValueError:
            self.bot.send_message(m.chat.id, 'Введите число')
            self.change_amount_input_0(m, name)

    # удаление препарата 
    def delete_medicine_keyboard(self, m):
        print('kit_delete_medicine_keyboard')

        markup = types.InlineKeyboardMarkup()
        medicines = self.users.get_user(m.chat.id).medicines

        for item in medicines.values():
            msg = '{} Кол-во: {}'.format(item.name, item.balance)
            markup.add(telebot.types.InlineKeyboardButton(text= msg, callback_data = 'del_med'+ str(item.name)))
        markup.add(types.InlineKeyboardButton(text='Назад', callback_data = "back_med"))
        
        self.bot.send_message(m.chat.id, 
            text='Нажмите на перепарат, который надо удалить:', 
            reply_markup=types.ReplyKeyboardRemove())
        self.bot.send_message(m.chat.id, text='Список препаратов: ', reply_markup=markup)

    # сохранение изменений
    def delete_medicine_0(self, m, medicine_name):
        print('kit_delete_medicine_0')

        ID = m.chat.id
        id_reminders_del = (self.users.data[ID].medicines[medicine_name].id_reminders).split()

        for id_reminder in id_reminders_del:
            try:
                self.reminders.delete_reminder(id_reminder, ID)
            except Exception as e:
                print(e)
        try:
            self.users.delete_medicine(ID, medicine_name)
        except Exception as e:
            print(e)
        
        self.bot.send_message(m.chat.id, 'Препарат удален')
            
        self.list_kit(m)
        self.menu(m)

    def buy_medicine(self, m):
        print('kit_buy_medicine')

        medicines = self.users.get_user(m.chat.id).medicines
        
        markup = types.InlineKeyboardMarkup()
        for item in medicines.values():
            msg = '{} Кол-во: {}'.format(item.name, item.balance)
            markup.add(types.InlineKeyboardButton(text=item.name, url="https://www.eapteka.ru/search/?q={}".format(item.name)))

        markup.add(types.InlineKeyboardButton(text='Другое',url="https://www.eapteka.ru/"))
        markup.add(types.InlineKeyboardButton(text='Назад', callback_data = "back_med"))

        self.bot.send_message(m.chat.id, 
            text='Нажмите на перепарат, который хотите купить', 
            reply_markup=types.ReplyKeyboardRemove())
        self.bot.send_message(m.chat.id, text='Список препаратов: ', reply_markup=markup)
    
    # инструкция в онлайн аптеке
    def instructinon(self, m):
        medicines = self.users.get_user(m.chat.id).medicines
        
        markup = types.InlineKeyboardMarkup()
        for item in medicines.values():
            msg = '{} Кол-во: {}'.format(item.name, item.balance)
            markup.add(types.InlineKeyboardButton(text=item.name, url="https://www.eapteka.ru/search/?q={}".format(item.name)))

        markup.add(types.InlineKeyboardButton(text='Другое',url="https://www.eapteka.ru/"))
        markup.add(types.InlineKeyboardButton(text='Назад', callback_data = "back_med"))

        self.bot.send_message(m.chat.id, 
            text='Нажмите на перепарат, инструкцию к которому хотите посмотреть', 
            reply_markup=types.ReplyKeyboardRemove())
        self.bot.send_message(m.chat.id, text='Список препаратов: ', reply_markup=markup)
