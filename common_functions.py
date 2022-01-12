from datetime import datetime, timezone
from telebot import types
import re
from zoneinfo import ZoneInfo

def create_custom_keyboard(options):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if isinstance(options[0], list):
        for row in options:
            keyboard.add(*[types.KeyboardButton(button_text) for button_text in row])
    else:
        keyboard.add(*[types.KeyboardButton(button_text) for button_text in options])
    return keyboard

def number_input(bot, m, allow_zero=False):
    try:
        if float(m.text) > 0 or (allow_zero and float(m.text) == 0):
            return float(m.text)
        else:
            bot.send_message(m.chat.id, 'Введите положительное число')
            return False
    except ValueError:
        bot.send_message(m.chat.id, 'Вводите цифрами')  
    return False


def times_input(bot, m):
    times = m.text
    if ", " in times:
        times = times.split(', ')
    elif ',' in times:
        times = times.split(',')
    elif ' ' in times:
        times = times.split(' ')

    if not isinstance(times, list):
        times  = [times]

    def check_time(time):
        pattern = re.compile("^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")
        if not pattern.match(time):
            return False
        return True

    for i in range(0, len(times)):
        if not check_time(times[i]):
            bot.send_message(m.chat.id, "Введите время в формате hh:mm цифрами через запятую" )
            return False
        if len(times[i]) == 4:
            times[i] = '0' + times[i]      
    #times = times.sort(key=lambda x: int(x.split(':')[0])*60+int(x.split(':')[1]))
    return times

def times_output(times):
    return ", ".join(times)

def get_current_time():
    time =datetime.now(ZoneInfo('Europe/Moscow')).time().strftime('%H:%M')
    return time