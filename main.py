import logging
import telebot
from openpyxl import Workbook
import requests
import json
import os
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove

# Конфигурация
BOT_TOKEN = '7551388193:AAGz0PeOFbbdnapmzQOHJUEWifZgWYITYUY'  # Ваш токен телеграм бота
YANDEX_DISK_API_URL = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
YANDEX_DISK_OAUTH_TOKEN = 'y0_AgAAAAADJMV6AADLWwAAAAEZ7GZ4AADWaHv7nMlFUpGTejYyi1q8TD9P0g'  # Ваш токен Яндекс.Диска
YANDEX_DISK_FOLDER_PATH = '/Economica/'  # Папка на Яндекс.Диске

bot = telebot.TeleBot(BOT_TOKEN)

user_data = {}
current_question = 0

def create_keyboard(buttons):
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(*buttons)
    return keyboard

questions_with_variants = {
    "Считаете ли Вы, что государство, решая задачи экономической политики, должно придерживаться определенных правил?": {
        "type": "text",
        "variants": ["a", "b", "c"],
        "a": "Решать экономические задачи в основном поочередно",
        "b": "Достигать целей одновременно",
        "c": "Правил придерживаться не следует, важно лишь оперативно реагировать на обстановку"
    },
    "Что Вы считаете более предпочтительным в проведении экономической политики?": {
        "type": "text",
        "variants": ["a", "b", "c"],
        "a": "Бороться с инфляцией, т.е. ростом цен, и допускать, если это неизбежно, определенное увеличение безработицы",
        "b": "Бороться с безработицей и допускать, если это неизбежно, рост цен, т. е. усиление инфляции",
        "c": "Искать новые пути решения двух указанных проблем"
    },
    "О чем, по Вашему мнению, должен заботиться каждый россиянин в период сложной экономической ситуации?": {
        "type": "text",
        "variants": ["a", "b", "c", "d", "e"],
        "a": "Быть более активным",
        "b": "Заботиться прежде всего о себе",
        "c": "Ориентироваться на то, что значительные экономические трудности - своего рода школа обучения и стимул к более быстрому решению накопившихся и застарелых проблем",
        "d": "Думать о нуждах всей страны",
        "e": "Искать источники помощи извне"
    },
    "Влияние каких внешних факторов ощущаете Вы как субъект экономической (профессиональной) сферы деятельности?": {
        "type": "text",
        "variants": ["a", "b", "c", "d", "e", "f"],
        "a": "Условия развития всей экономики страны",
        "b": "Экономическая политика государства",
        "c": "Конъюнктура развития отрасли, в которой находится предприятие",
        "d": "Коррупция",
        "e": "Криминальные структуры",
        "f": "Практически никакого влияния не ощущаю"
    },
    "Хотите ли Вы, будучи деловой личностью, бизнесменом (или желая стать им), оказывать встречное влияние на государство, на его экономическую политику?": {
        "type": "text",
        "variants": ["a", "b", "c", "d", "e"],
        "a": "Хотел бы путем влияния на государственных лиц (метод лобби)",
        "b": "Хотел бы через систему выборов",
        "c": "Встречного влияния оказывать не хочу. Каждый идет своей дорогой, делая свое дело.",
        "d": "Хотел бы через стиль своего постоянного поведения (проведения «своей линии»)",
        "e": "Хотел бы через организацию политического движения"
    },
    "Если Вы стремитесь избежать налогообложения, на что похожи подобные действия?": {
        "type": "text",
        "variants": ["a", "b", "c", "d", "e"],
        "a": "Стараюсь не избегать налогообложения и быть законопослушным",
        "b": "Уход от налогов - форма сохранения у себя средств, которые государство может нерационально использовать",
        "c": "Уход от налогов - проявление природной (и потому закономерной) изворотливости всех субъектов экономики, каждый из которых имеет свои личные цели",
        "d": "Уход от налогов - способ поддержания своего относительного материального достатка",
        "e": "Уход от налогов - способ воровства финансовых средств у государства"
    }
}

questions = list(questions_with_variants.keys())

def handle_answer(message):
    global current_question, user_data
    try:
        answer = message.text
        question = questions[current_question]
        user_data[question] = answer
        current_question += 1

        if current_question < len(questions):
            ask_question(message)
        else:
            finish_survey(message)
    except Exception as e:
        bot.reply_to(message, f"Ошибка: {e}. Пожалуйста, повторите попытку.")
        ask_question(message)  # Повторить вопрос при ошибке

def ask_question(message):
    global current_question
    if current_question < len(questions):
        question = questions[current_question]
        variants = questions_with_variants[question]["variants"]

        # Формируем текст с вопросом и вариантами ответов
        answer_text = "\n".join([f"{v}) {questions_with_variants[question][v]}" for v in variants])
        full_message = f"{question}\n\n{answer_text}"

        # Создаем клавиатуру с кнопками, соответствующими буквам вариантов
        keyboard = create_keyboard(variants)  # variants уже содержит буквы

        bot.send_message(message.chat.id, full_message, reply_markup=keyboard)
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

    bot.send_message(message.chat.id, result_message, reply_markup=telebot.types.ReplyKeyboardRemove())

    # Создаем кнопку для перехода по ссылке
    final_keyboard = InlineKeyboardMarkup()
    link_button = InlineKeyboardButton("Перейти к книгам по экономической психологии", url="https://disk.yandex.ru/d/i01ibMMiin9xTg")
    final_keyboard.add(link_button)

    final_message = "Благодарю за прохождение опроса!"
    bot.send_message(message.chat.id, final_message, reply_markup=final_keyboard)  # Отправляем сообщение с кнопкой

# Кнопка "Начать опрос"
start_button = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
start_button.add("Начать опрос")

@bot.message_handler(commands=['start'])
def start_message(message):
    welcome_message = """Привет! Я бот, который поможет собрать информацию по экономической психологии. 
Ваши ответы анонимны и будут использованы только для исследовательских целей. Давайте начнем!
!!!ВНИМАНИЕ, для ответов на вопросы выберите соответствующую вашему варианту КНОПКУ СНИЗУ!!!
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
