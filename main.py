import logging
import telebot
from openpyxl import Workbook
import requests
import os
from datetime import datetime
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove

# Конфигурация
BOT_TOKEN = '7551388193:AAGz0PeOFbbdnapmzQOHJUEWifZgWYITYUY'  # Замените на ваш токен телеграм бота
YANDEX_DISK_API_URL = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
YANDEX_DISK_OAUTH_TOKEN = 'y0_AgAAAAADJMV6AADLWwAAAAEZ7GZ4AADWaHv7nMlFUpGTejYyi1q8TD9P0g'  # Замените на ваш токен Яндекс.Диска
YANDEX_DISK_FOLDER_PATH = '/Economica/'  # Папка на Яндекс.Диске

bot = telebot.TeleBot(BOT_TOKEN)

# Переменные для первого опроса
user_data_1 = {}
current_question_1 = 0

questions_1 = [
    ("Каков ваш возраст? (УКАЖИТЕ ЧИСЛО)", "int", ReplyKeyboardRemove()),
    ("Каков ваш пол?", "text", telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add("Мужской", "Женский")),
    ("Какова ваша форма обучения?", "text", telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add("Очная", "Заочная", "Дистанционная")),
    ("На каком курсе вы обучаетесь?", "int", telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add("1", "2", "3", "4", "5", "6")),
    ("Оцените, пожалуйста, свой уровень стресса за последние 4 недели по шкале от 0 до 4, где 0 — это \"никогда\", а 4 — \"очень часто\": Я чувствовал(а) себя нервным(ой) или \"на грани\"", "int", telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add("0", "1", "2", "3", "4")),
    ("Оцените, пожалуйста, свой уровень стресса за последние 4 недели по шкале от 0 до 4, где 0 — это \"никогда\", а 4 — \"очень часто\": Я чувствовал(а) себя неспособным(ой) контролировать важные вещи в своей жизни.", "int", telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add("0", "1", "2", "3", "4")),
    ("Оцените, пожалуйста, свой уровень стресса за последние 4 недели по шкале от 0 до 4, где 0 — это \"никогда\", а 4 — \"очень часто\": Я чувствовал(а) себя подавленным(ой).", "int", telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add("0", "1", "2", "3", "4")),
    ("Оцените, пожалуйста, свой уровень стресса за последние 4 недели по шкале от 0 до 4, где 0 — это \"никогда\", а 4 — \"очень часто\": Я испытывал(а) трудности с расслаблением.", "int", telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add("0", "1", "2", "3", "4")),
    ("Сталкивались ли вы с конфликтами в семье?", "text", telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add("Да", "Нет")),
    ("Сталкивались ли вы с конфликтами с друзьями?", "text", telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add("Да", "Нет")),
    ("Испытываете ли вы финансовые проблемы?", "text", telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add("Да", "Нет")),
    ("У вас есть достаточно времени для отдыха?", "text", telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add("Да", "Нет")),
    ("Какие другие факторы, по вашему мнению, способствуют вашему стрессу? (НАПИШИТЕ ВАШ ВАРИАНТ)", "text", ReplyKeyboardRemove()),
    ("У вас есть хобби?", "text", telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add("Да", "Нет")),
    ("Занимаетесь ли вы регулярными физическими упражнениями?", "text", telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add("Да", "Нет")),
    ("Получаете ли вы поддержку от родных и близких?", "text", telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add("Да", "Нет")),
    ("Как вы обычно справляетесь со стрессом? (НАПИШИТЕ ВАШ ВАРИАНТ)", "text", ReplyKeyboardRemove()),
    ("Какие другие факторы, по вашему мнению, способствуют снижению вашего стресса? (НАПИШИТЕ ВАШ ВАРИАНТ)", "text", ReplyKeyboardRemove()),
]

# Переменные для второго опроса
user_data_2 = {}
current_question_2 = 0

questions_2 = {
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

questions_2_list = list(questions_2.keys())

def handle_answer_1(message):
    """Обрабатывает ответ пользователя на вопрос 1."""
    global current_question_1, user_data_1
    try:
        question, answer_type, keyboard = questions_1[current_question_1]
        answer = int(message.text) if answer_type == "int" else message.text
        user_data_1[question] = answer
        current_question_1 += 1

        if current_question_1 < len(questions_1):
            ask_question_1(message)
        else:
            finish_survey_1(message)
    except ValueError as e:
        bot.reply_to(message, f"Ошибка: {e}. Пожалуйста, повторите попытку.")
        ask_question_1(message)

def ask_question_1(message):
    """Задает вопрос 1 пользователю."""
    global current_question_1
    if current_question_1 < len(questions_1):
        question, answer_type, keyboard = questions_1[current_question_1]
        bot.send_message(message.chat.id, question, reply_markup=keyboard)
        bot.register_next_step_handler(message, handle_answer_1)

def finish_survey_1(message):
    """Завершает опрос 1 и обрабатывает результаты."""
    process_survey_results(user_data_1, 1)
    result_message = "Спасибо за участие! Ваши ответы:\n\n" + "\n".join([f"{q}: {a}" for q, a in user_data_1.items()])
    bot.send_message(message.chat.id, result_message, reply_markup=telebot.types.ReplyKeyboardRemove())

    # Кнопка для перехода на Яндекс Диск
    final_keyboard = InlineKeyboardMarkup()
    link_button = InlineKeyboardButton("Перейти к книгам по преодолению стресса", url="https://disk.yandex.ru/d/7fySSnPUS_Gxbw")
    restart_button = InlineKeyboardButton("Перезапустить бота", callback_data="restart")
    final_keyboard.add(link_button, restart_button)

    final_message = "Благодарю за прохождение опроса!"
    bot.send_message(message.chat.id, final_message, reply_markup=final_keyboard)

def handle_answer_2(message):
    """Обрабатывает ответ пользователя на вопрос 2."""
    global current_question_2, user_data_2
    answer = message.text
    question = questions_2_list[current_question_2]
    user_data_2[question] = answer
    current_question_2 += 1

    if current_question_2 < len(questions_2_list):
        ask_question_2(message)
    else:
        finish_survey_2(message)

def ask_question_2(message):
    """Задает вопрос 2 пользователю."""
    global current_question_2
    if current_question_2 < len(questions_2_list):
        question = questions_2_list[current_question_2]
        variants = questions_2[question]["variants"]
        answer_text = "\n".join([f"{v}) {questions_2[question][v]}" for v in variants])
        full_message = f"{question}\n\n{answer_text}"

        keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True).add(*variants)
        bot.send_message(message.chat.id, full_message, reply_markup=keyboard)
        bot.register_next_step_handler(message, handle_answer_2)

def finish_survey_2(message):
    """Завершает опрос 2 и обрабатывает результаты."""
    process_survey_results(user_data_2, 2)
    result_message = "Спасибо за участие! Ваши ответы:\n\n" + "\n".join([f"{q}: {a}" for q, a in user_data_2.items()])
    bot.send_message(message.chat.id, result_message, reply_markup=telebot.types.ReplyKeyboardRemove())

    # Кнопка для перехода на Яндекс Диск
    final_keyboard = InlineKeyboardMarkup()
    link_button = InlineKeyboardButton("Перейти к книгам по экономической психологии", url="https://disk.yandex.ru/d/i01ibMMiin9xTg")
    restart_button = InlineKeyboardButton("Перезапустить бота", callback_data="restart")
    final_keyboard.add(link_button, restart_button)

    final_message = "Благодарю за прохождение опроса!"
    bot.send_message(message.chat.id, final_message, reply_markup=final_keyboard)

def process_survey_results(user_data, survey_number):
    """Обрабатывает результаты опроса и сохраняет их в Excel файл."""
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["Вопрос", "Ответ"])

    for question, answer in user_data.items():
        sheet.append([question, answer])

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{timestamp}_survey_results_{survey_number}.xlsx"
    workbook.save(filename)

    # Определяем папку в зависимости от номера опроса
    upload_folder_path = '/Stress/' if survey_number == 1 else '/Economica/'
    upload_to_yandex_disk(filename, upload_folder_path)

def upload_to_yandex_disk(filepath, upload_folder_path):
    """Загружает файл на Яндекс.Диск."""
    headers = {
        'Authorization': f'OAuth {YANDEX_DISK_OAUTH_TOKEN}'
    }
    url = f'{YANDEX_DISK_API_URL}?path={upload_folder_path}{os.path.basename(filepath)}&overwrite=true'

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

# Кнопка "Начать опрос"
start_button = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
start_button.add("Опрос о стрессе", "Опрос по экономической психологии")

@bot.message_handler(commands=['start'])
def start_message(message):
    """Отправляет приветственное сообщение и предлагает начать опрос."""
    welcome_message = """Привет! Я бот, который поможет собрать информацию. Выберите, какой опрос вы хотите пройти:
1. Опрос о стрессе
2. Опрос по экономической психологии
"""
    bot.send_message(message.chat.id, welcome_message, reply_markup=start_button)

@bot.message_handler(func=lambda message: message.text == "Опрос о стрессе")
def start_survey_1(message):
    """Запускает опрос о стрессе."""
    global current_question_1
    current_question_1 = 0
    user_data_1.clear()  # Сброс данных пользователя
    ask_question_1(message)

@bot.message_handler(func=lambda message: message.text == "Опрос по социальной психологии")
def start_survey_2(message):
    """Запускает опрос по социальной психологии."""
    global current_question_2
    current_question_2 = 0
    user_data_2.clear()  # Сброс данных пользователя
    ask_question_2(message)

@bot.callback_query_handler(func=lambda call: call.data == "restart")
def restart_bot(call):
    """Перезапускает бота."""
    start_message(call.message)

# Запуск бота
bot.infinity_polling()
