import logging
import telebot
from openpyxl import Workbook
import requests
import json
import os
from datetime import datetime

# Конфигурация
BOT_TOKEN = '7551388193:AAGz0PeOFbbdnapmzQOHJUEWifZgWYITYUY'  # Ваш токен телеграм бота
YANDEX_DISK_API_URL = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
YANDEX_DISK_OAUTH_TOKEN = 'y0_AgAAAAADJMV6AADLWwAAAAEZ7GZ4AADWaHv7nMlFUpGTejYyi1q8TD9P0g'  # Ваш токен Яндекс.Диска
YANDEX_DISK_FOLDER_PATH = '/Stress/'  # Папка на Яндекс.Диске

bot = telebot.TeleBot(BOT_TOKEN)

user_data = {}
current_question = 0

def create_keyboard(buttons):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*buttons)
    return keyboard

questions = [
    ("Каков ваш возраст? (УКАЖИТЕ ЧИСЛО)", "int", telebot.types.ReplyKeyboardRemove()),
    ("Каков ваш пол?", "text", create_keyboard(["Мужской", "Женский"])),
    ("Какова ваша форма обучения?", "text", create_keyboard(["Очная", "Заочная", "Дистанционная"])),
    ("На каком курсе вы обучаетесь?", "int", create_keyboard(["1", "2", "3", "4", "5", "6"])),
    (
    "Оцените, пожалуйста, свой уровень стресса за последние 4 недели по шкале от 0 до 4, где 0 — это \"никогда\", а 4 — \"очень часто\": Я чувствовал(а) себя нервным(ой) или \"на грани\"",
    "int", create_keyboard(["0", "1", "2", "3", "4"])),
    (
    "Оцените, пожалуйста, свой уровень стресса за последние 4 недели по шкале от 0 до 4, где 0 — это \"никогда\", а 4 — \"очень часто\": Я чувствовал(а) себя неспособным(ой) контролировать важные вещи в своей жизни.",
    "int", create_keyboard(["0", "1", "2", "3", "4"])),
    (
    "Оцените, пожалуйста, свой уровень стресса за последние 4 недели по шкале от 0 до 4, где 0 — это \"никогда\", а 4 — \"очень часто\": Я чувствовал(а) себя подавленным(ой).",
    "int", create_keyboard(["0", "1", "2", "3", "4"])),
    (
    "Оцените, пожалуйста, свой уровень стресса за последние 4 недели по шкале от 0 до 4, где 0 — это \"никогда\", а 4 — \"очень часто\": Я испытывал(а) трудности с расслаблением.",
    "int", create_keyboard(["0", "1", "2", "3", "4"])),
    ("Сталкивались ли вы с конфликтами в семье?", "text", create_keyboard(["Да", "Нет"])),
    ("Сталкивались ли вы с конфликтами с друзьями?", "text", create_keyboard(["Да", "Нет"])),
    ("Испытываете ли вы финансовые проблемы?", "text", create_keyboard(["Да", "Нет"])),
    ("У вас есть достаточно времени для отдыха?", "text", create_keyboard(["Да", "Нет"])),
    ("Какие другие факторы, по вашему мнению, способствуют вашему стрессу? (НАПИШИТЕ ВАШ ВАРИАНТ)", "text",
     telebot.types.ReplyKeyboardRemove()),
    ("У вас есть хобби?)", "text", create_keyboard(["Да", "Нет"])),
    ("Занимаетесь ли вы регулярными физическими упражнениями?", "text", create_keyboard(["Да", "Нет"])),
    ("Получаете ли вы поддержку от родных и близких?", "text", create_keyboard(["Да", "Нет"])),
    ("Как вы обычно справляетесь со стрессом? (НАПИШИТЕ ВАШ ВАРИАНТ)", "text", telebot.types.ReplyKeyboardRemove()),
    ("Какие другие факторы, по вашему мнению, способствуют снижению вашего стресса? (НАПИШИТЕ ВАШ ВАРИАНТ)", "text",
     telebot.types.ReplyKeyboardRemove()),
]

def handle_answer(message):
    global current_question, user_data
    try:
        question, answer_type, keyboard = questions[current_question]
        if answer_type == "int":
            answer = int(message.text)
        elif answer_type == "text":
            answer = message.text
        else:
            raise ValueError("Неизвестный тип ответа")

        user_data[question] = answer
        current_question += 1

        if current_question < len(questions):
            ask_question(message)
        else:
            finish_survey(message)
    except ValueError as e:
        bot.reply_to(message, f"Ошибка: {e}. Пожалуйста, повторите попытку.")
        ask_question(message)  # Повторить вопрос при ошибке

def ask_question(message):
    global current_question
    if current_question < len(questions):
        question, answer_type, keyboard = questions[current_question]
        bot.send_message(message.chat.id, question, reply_markup=keyboard)
        bot.register_next_step_handler(message, handle_answer)

# --- Обработка и сохранение результатов ---
def process_survey_results(user_data):
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Вопрос", "Ответ"])

    for question, answer in user_data.items():
        sheet.append([question, answer])

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{timestamp}_survey_results.xlsx"
    workbook.save(filename)
    upload_to_yandex_disk(filename)

# --- Загрузка на Яндекс.Диск ---
def upload_to_yandex_disk(filepath):
    headers = {
        'Authorization': f'OAuth {YANDEX_DISK_OAUTH_TOKEN}'
    }
    url = f'{YANDEX_DISK_API_URL}?path={YANDEX_DISK_FOLDER_PATH}{os.path.basename(filepath)}&overwrite=true'

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        upload_url = response.json()['href']

        with open(filepath, 'rb') as f:
            response = requests.put(upload_url, data=f)
            response.raise_for_status()
            print(f"Файл '{filepath}' успешно загружен на Яндекс.Диск.")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при работе с Яндекс.Диском: {e}")
    except json.JSONDecodeError as e:
        print(f"Ошибка при обработке JSON-ответа от Яндекс.Диска: {e}")
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")

def finish_survey(message):
    process_survey_results(user_data)  # Обработка результатов перед отправкой
    result_message = "Спасибо за участие! Ваши ответы:\n\n"
    for question, answer in user_data.items():
        result_message += f"{question}: {answer}\n"

    bot.send_message(message.chat.id, result_message)  # Отправляем результаты

    final_message = """
Благодарю за прохождение опроса! В благодарность, перейдя по ссылке, Вы сможете ознакомиться с книгами по преодолению стресса.
https://disk.yandex.ru/d/7fySSnPUS_Gxbw
"""
    bot.send_message(message.chat.id, final_message)  # Отправляем благодарность и ссылку

# Кнопка "Начать опрос"
start_button = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
start_button.add("Начать опрос")

@bot.message_handler(commands=['start'])
def start_message(message):
    welcome_message = """Привет! Я бот, который поможет собрать информацию о стрессе и способах его управления у студентов. 
Ваши ответы анонимны и будут использованы только для исследовательских целей. Давайте начнем!
!!!ВНИМАНИЕ, некоторые вопросы не имеют кнопки варианта, а требуют текстового ввода!!!
"""
    bot.send_message(message.chat.id, welcome_message, reply_markup=start_button)
    bot.register_next_step_handler(message, start_survey)

# --- Обработчик кнопки "Начать опрос" ---
def start_survey(message):
    if message.text == "Начать опрос":
        global current_question
        current_question = 0
        user_data.clear()  # Сброс данных пользователя
        ask_question(message)
    else:
        bot.send_message(message.chat.id, "Пожалуйста, нажмите кнопку \"Начать опрос\".", reply_markup=start_button)

# Запуск бота
bot.infinity_polling()
