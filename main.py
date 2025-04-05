import telebot
from telebot import types
import requests
import sqlite3
from datetime import datetime

API_TOKEN = 'Token бота'
bot = telebot.TeleBot(API_TOKEN)
url = "https://yandex.ru/pogoda/nizhny-novgorod" #Зайдите на яндек погода (https://yandex.ru/pogoda) и выберите свой регион, после чего скопируйте ссылку и замениите

# База данных
conn = sqlite3.connect('weather_forecast.db', check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS forecast (
    date TEXT PRIMARY KEY,
    today_temp INTEGER,
    tomorrow_temp INTEGER
)
''')
conn.commit()


def get_temp_from_yandex():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        
        r = requests.get(url, headers=headers, timeout=10)
        html = r.text

        temps = []
        start = 0
        while True:
            start = html.find('temp__value', start)
            if start == -1:
                break
            temp_start = html.find('>', start) + 1
            temp_end = html.find('<', temp_start)
            temp_str = html[temp_start:temp_end].strip().replace('−', '-')
            try:
                temps.append(int(temp_str))
            except ValueError:
                pass
            start = temp_end

        return (temps[0], temps[1]) if len(temps) >= 2 else (None, None)
    except Exception as e:
        print("Ошибка при парсинге:", e)
        return (None, None)

# Сохранение в базу
def save_forecast(date, today, tomorrow):
    cursor.execute('REPLACE INTO forecast (date, today_temp, tomorrow_temp) VALUES (?, ?, ?)', (date, today, tomorrow))
    conn.commit()

# Предсказание
def make_prediction(today, tomorrow):
    if today is None or tomorrow is None:
        return "⚠️ Не удалось получить температуру."

    if tomorrow > today:
        return f"🌤 Завтра потеплеет на {tomorrow - today}°C."
    elif tomorrow < today:
        return f"❄️ Завтра похолодает на {today - tomorrow}°C."
    else:
        return "🌡 Температура останется такой же."

# Информация о глобальном потеплении
def global_warming_info():
    return ("🌍 Что такое глобальное потепление?\n"
            "Глобальное потепление — это процесс увеличения средней температуры Земли. "
            "Это явление вызвано увеличением концентрации парниковых газов, таких как углекислый газ (CO2), метан (CH4) и другие.\n\n"
            "🌡 Причины глобального потепления:\n"
            "1. Выбросы углекислого газа от сжигания ископаемого топлива.\n"
            "2. Вырубка лесов, которые поглощают углекислый газ.\n"
            "3. Индустриализация и другие человеческие деятельности.\n\n"
            "🌿 Как сдерживать глобальное потепление?\n"
            "1. Снижение выбросов парниковых газов.\n"
            "2. Использование возобновляемых источников энергии.\n"
            "3. Уменьшение потребления энергии и ресурсов.\n"
            "4. Сохранение и восстановление экосистем.\n\n"
            "💡 Полезные советы:\n"
            "1. Экономьте электроэнергию и используйте энергоэффективные устройства.\n"
            "2. Сортируйте отходы и перерабатывайте материалы.\n"
            "3. Используйте общественный транспорт или ходите пешком.\n"
            "4. Поддерживайте экологические инициативы и проекты.")

# Команда /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Прогноз в Нижнем", "Предсказание", "Глобальное потепление", "Полезные советы")
    bot.send_message(message.chat.id, "Привет! Я бот, который умеет смотреть прогноз погоды и рассказывать о глобальном потеплении. Жми кнопку 👇", reply_markup=markup)

# Обработка кнопок
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == "Прогноз в Нижнем":
        today, tomorrow = get_temp_from_yandex()
        if today is not None:
            date = datetime.now().strftime('%Y-%m-%d')
            save_forecast(date, today, tomorrow)
            bot.send_message(message.chat.id, f"🌆 Сегодня в Н. Новгороде: {today}°C\n🔮 Завтра: {tomorrow}°C")
        else:
            bot.send_message(message.chat.id, "⚠️ Не получилось получить данные о погоде.")
    elif message.text == "Предсказание":
        today, tomorrow = get_temp_from_yandex()
        prediction = make_prediction(today, tomorrow)
        bot.send_message(message.chat.id, prediction)
    elif message.text == "Глобальное потепление":
        info = global_warming_info()
        bot.send_message(message.chat.id, info)
    elif message.text == "Полезные советы":
        bot.send_message(message.chat.id, "1. Экономьте электроэнергию.⚡\n2. Используйте общественный транспорт.🚌\n3. Сортируйте отходы.🚮\n4. Поддерживайте экологические инициативы.🌳")
    else:
        bot.send_message(message.chat.id, "Выбери кнопку снизу 👇")

# Запуск
bot.polling()
