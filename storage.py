import pickle
from random import randrange
from datetime import datetime
import os

from pyrebase.pyrebase import Storage

import firestore as FS

PRODUCTION = os.environ.get("PRODUCTION", False) == "True"

class Reminder:
    def __init__(self,
                 ID,
                 user_ID,
                 medicine_name,
                 time,
                 dosage,
                 **kwargs):
        self.ID = ID
        self.user_ID = user_ID
        self.medicine_name = medicine_name
        self.time = time
        self.dosage = dosage

    def to_string(self):
        return '{2} - {0} (дозировка: {1})'.format( 
                        self.medicine_name,
                        self.dosage, 
                        self.time)

    def to_dict(self):
        return vars(self)

class Reminders_storage:
    data = {}

    def __init__(self):
        # filling with data from backup on the storage initization
        try:
            self.load_data()
        except Exception as e:
            print("Ошибка загрузки данных Reminders_storage")
            print(e)
            pass

    # accessing all data from storage
    def get_reminders(self):
        return self.data

    def get_reminder(self, ID):
        return self.data[ID]

    def get_users_reminders(self, user_ID):
        return {key: value for key, value in self.data.items() if value.user_ID==user_ID}

    def get_users_reminders_sorted_values(self, user_ID):
        reminders = self.get_users_reminders(user_ID)
        reminders = sorted(reminders.values(), key=lambda item: int(item.time.split(':')[0])*60+int(item.time.split(':')[1]))
        return reminders

    def get_users_medicine_consumption(self, user_ID, medicine_name):
        res = 0
        for item in self.data.values():
            if item.user_ID == user_ID and item.medicine_name == medicine_name:
                res += item.dosage
        return res

    def get_reminders_by_time(self, time):
        return [value for value in self.data.values() if value.time==time]

    def add_reminder(self, reminder):
        start_ID = len(self.data)

        def get_id(i):
            if len(self.data) == 0:
                return 'id0'
            return 'id' + str(int(list(self.data)[-1][2:])+1)

        for i in range(len(reminder['times'])):
            _reminder = Reminder(
                ID = get_id(i), 
                user_ID = reminder['user_ID'],
                medicine_name = reminder['medicine_name'],
                time = reminder['times'][i],
                dosage = reminder['dosage'])
            self.data[get_id(i)] = _reminder
            FS.add_reminder(_reminder.to_dict())

        self.save_data()
        return self.get_users_reminders(reminder['user_ID'])

    def delete_reminder(self, ID, user_ID):
        if not (ID in self.data):
            raise Exception('Remidner does not exist.')
        if not (user_ID == self.data[ID].user_ID):
            raise Exception('You do not have rights to edit this reminder.')

        del self.data[ID]
        FS.delete_reminder(ID)
        self.save_data()

    def update_reminder(self, reminder):
        if not (self.data['ID'] in self.data):
            raise Exception('Remidner does not exist.')

        reminder = Reminder(**reminder)
        self.data[reminder.ID] = reminder
        
        FS.add_reminder(reminder.to_dict())
        self.save_data()

    # loading data from backup
    def load_data(self):
        if PRODUCTION:
            all_reminders = FS.load_reminders()
            result = {}
            for reminder in all_reminders.each():
                result[reminder.key()]=Reminder(**reminder.val())
            self.data = result
            return

        try:
            with open('reminders_backup', 'rb') as f:
                data_form_file = pickle.load(f)
                self.data.update(data_form_file)
        except Exception as e:
            raise Exception('File with data does not exist')

    # creating backup
    def save_data(self):
        with open('reminders_backup', 'wb') as f:
            pickle.dump(self.data, f)


# chat id
# medicines 
#   name    string
#   balance int
#   dosage  string


class Medicine:
    def __init__(self,
                 name,
                 balance = 0,
                 dosage = 0,
                 id_reminders = '',
                 **kwargs):

        self.name = name
        self.balance = balance
        self.dosage = dosage
        self.id_reminders = id_reminders

    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, value):
        value = str(value)
        if not value:
            raise ValueError("Название не может быть пустым.")
        self._name = value

    @property
    def balance(self):
        return self._balance
    
    @balance.setter
    def balance(self, value):
        if (not isinstance(value, float)) and (not isinstance(value, int)):
            raise ValueError("Запас должен быть числом.")
        self._balance = value

    @property
    def dosage(self):
        return self._dosage
    
    @dosage.setter
    def dosage(self, value):
        if (not isinstance(value, float)) and (not isinstance(value, int)):
            raise ValueError("Запас должен быть числом.")
        self._dosage = value
    
    @property
    def id_reminders(self):
        return self._id_reminders
    
    @id_reminders.setter
    def id_reminders(self, value):
        value = str(value)
        self._id_reminders = value

    def to_string(self):
        return '{0}. Оставшихся таблеток: {1}. Стандартная дозировка {2}'.format( 
                        self.name,
                        self.balance, 
                        self.dosage)

    def to_dict(self):
        res = {}
        for key, value in vars(self).items():
            if key[0] == '_':
                res[key[1:]] = value
            else:
                res[key] = value
        return res

class User:
    def __init__(self,
                 ID,
                 medicines = {},
                 last_request = datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                 phone_number = '',
                 **kwargs):
        self.ID = ID
        self.medicines = medicines
        self.last_request = last_request
        self.phone_number = phone_number

    def check_medicines(self):
        if not self.medicines or len(self.medicines)<1:
            return False

        return True

    def to_dict(self):
        user = vars(self).copy()
        if self.medicines and len(self.medicines):
            medicines = {}
            for key, value in self.medicines.items():
                medicines[key] = value.to_dict()
            user['medicines'] = medicines
        return user


class Users_storage:
    data = {}

    def __init__(self):
        # filling with data from backup on the storage initization
        try:
            self.load_data()
        except Exception as e:
            print("Ошибка загрузки данных Users_storage")
            print(e)
            pass

        print('Создали хранилище пользователей')

    # accessing all data from storage
    def get_users(self):
        return self.data

    def get_user(self, ID):
        if not (ID in self.data):
            raise Exception('Пользователя не существует.')

        return self.data[ID]

    def add_user(self, user):
        if user['ID'] in self.data:
            return self.data[user['ID']]

        user = User(**user)
        self.data[user.ID] = user
        
        FS.add_user(user.to_dict())
        self.save_data()

        return user
        
    def update_user(self, user):
        if not (user.ID in self.data):
            raise Exception('Пользователя не существует.')

        if isinstance(user, User):
            self.data[user.ID] = user
        else:
            self.data[user.ID] = User(**user)
        user = self.data[user.ID]

        FS.add_user(user.to_dict())
        self.save_data()

        return user

    def delete_user(self, ID):
        if not (ID in self.data):
            raise Exception('Пользователя не существует.')

        FS.delete_user(ID)
        self.save_data()

        del self.data[ID]

    def get_users_medicine_by_name(self, ID, medicine_name):
        if not (ID in self.data):
            raise Exception('Пользователя не существует.')
        user = self.data[ID]

        if not medicine_name in user.medicines:
            raise Exception('Данное лекарство не существует.')
        
        return user.medicines[medicine_name]

    def add_medicine(self, ID, medicine):
        if not (ID in self.data):
            raise Exception('Пользователя не существует.')
        user = self.data[ID]

        if medicine['name'] in user.medicines:
            raise Exception('Данное лекарство уже существует.')
        medicine = Medicine(**medicine)
        user.medicines[medicine.name] = medicine

        FS.add_medicine(user.ID, medicine.to_dict())
        self.save_data()

        return user
    #без id
    def update_medicine(self, ID, medicine_name, field, value):
        if not (ID in self.data):
            raise Exception('Пользователя не существует.')
        user = self.data[ID]

        if not (medicine_name in user.medicines):
            raise Exception('Данное лекарство не существует.')

        setattr(user.medicines[medicine_name], field, value)

        FS.update_medicine(user.ID, medicine_name, field, value)
        self.save_data()

        return user

    def update_medicine_id_reminders(self, ID, medicine_name, value):
        if not (ID in self.data):
            raise Exception('Пользователя не существует.')
        user = self.data[ID]

        if not (medicine_name in user.medicines):
            raise Exception('Данное лекарство не существует.')

        old_value = self.data[ID].medicines[medicine_name].id_reminders
        if len(old_value) > 0:
            value= old_value + ' ' + value
        setattr(user.medicines[medicine_name],'id_reminders' , value)
        FS.update_medicine(user.ID, medicine_name, 'id_reminders', value)
        self.save_data()

        return user

    def reduce_medicine_id_reminders(self, ID, medicine_name, id_reminder):
        if not (ID in self.data):
            raise Exception('Пользователя не существует.')
        user = self.data[ID]

        if not (medicine_name in user.medicines):
            raise Exception('Данное лекарство не существует.')

        value = (self.data[ID].medicines[medicine_name].id_reminders).split()
        try:
            value.remove(id_reminder)
            if len(value) < 1:
                value = ''
            else:
                value = ' '.join([i for i in value])
        except Exception as e:
            value = ''
            print(e)
        setattr(user.medicines[medicine_name], 'id_reminders', value)
        FS.update_medicine(user.ID, medicine_name, 'id_reminders', value)
        self.save_data()

        return user

    def reduce_medicine(self, ID, medicine_name, value):
        if not (ID in self.data):
            raise Exception('Пользователя не существует.')
        user = self.data[ID]

        if not (medicine_name in user.medicines):
            raise Exception('Данное лекарство не существует.')
        
        user.medicines[medicine_name].balance -= value
        
        self.save_data()
        FS.update_medicine(user.ID, 
            medicine_name, 
            'balance', 
            user.medicines[medicine_name].balance)

        return user

    def delete_medicine(self, ID, medicine_name):
        if not (ID in self.data):
            raise Exception('Пользователя не существует.')
        user = self.data[ID]

        if not (medicine_name in user.medicines):
            raise Exception('Данное лекарство не существует.')
        
        del user.medicines[medicine_name]

        self.save_data()
        FS.delete_medicine(user.ID, medicine_name)

        return user

    def medicines_to_sting(self, ID):
        if not (ID in self.data):
            raise Exception('Пользователя не существует.')
        user = self.data[ID]

        if not user.check_medicines:
            return "У вас нет лекарств в аптечке"

        res = []
        i = 1
        for name, item in user.medicines.items():
            res.append("№{} - {} \n".format(i, item.to_string()))
            i+=1

        return res

    # loading data from backup
    def load_data(self):
        if PRODUCTION:
            all_users = FS.load_users()
            result = {}
            for item in all_users.each():
                user = item.val()
                try:
                    if user['medicines'] and len(user['medicines']):
                        medicines = {}
                        for key, value in user['medicines'].items():
                            medicines[key] = Medicine(**value)
                        user['medicines'] = medicines
                except Exception as e:
                    print(e)
                result[user['ID']]=User(**user)
            self.data = result
            return

        try:
            with open('users_backup', 'rb') as f:
                data_form_file = pickle.load(f)
                self.data.update(data_form_file)
        except Exception as e:
            raise Exception('File with data does not exist')

    # creating backup
    def save_data(self):
        with open('users_backup', 'wb') as f:
            pickle.dump(self.data, f)