import telebot
from telebot import types
import requests
import sqlite3
import threading
import time
from datetime import datetime
from bs4 import BeautifulSoup


API_TOKEN = 'Token'  # Замените на свой токен
bot = telebot.TeleBot(API_TOKEN)
url = "https://yandex.ru/pogoda/nizhny-novgorod"  # Замените на ссылку для своего региона

ADMIN_ID = 6819634216  # ← замени на свой Telegram ID

conn = sqlite3.connect('weather_forecast.db', check_same_thread=False)
cursor = conn.cursor()


cursor.execute('''
CREATE TABLE IF NOT EXISTS forecast (
    date TEXT PRIMARY KEY,
    today_temp INTEGER,
    tomorrow_temp INTEGER
)
''')
cursor.execute('''
CREATE TABLE IF NOT EXISTS subscriptions (
    user_id INTEGER PRIMARY KEY
)
''')
conn.commit()

# Получение погоды
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

def save_forecast(date, today, tomorrow):
    cursor.execute('REPLACE INTO forecast (date, today_temp, tomorrow_temp) VALUES (?, ?, ?)', (date, today, tomorrow))
    conn.commit()

def make_prediction(today, tomorrow):
    if today is None or tomorrow is None:
        return "⚠️ Не удалось получить температуру."
    if tomorrow > today:
        return f"🌤 Завтра потеплеет на {tomorrow - today}°C."
    elif tomorrow < today:
        return f"❄️ Завтра похолодает на {today - tomorrow}°C."
    else:
        return "🌡 Температура останется такой же."

def get_eco_news():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        news_url = "https://ria.ru/ecology/"  # <-- актуальный раздел экологии
        r = requests.get(news_url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')

        news_elements = soup.select('a.list-item__title.color-font-hover-only')[:5]

        news_list = []
        for item in news_elements:
            title = item.get_text(strip=True)
            link = item['href']
            news_list.append(f"📰 {title}\n🔗 {link}")

        return "\n\n".join(news_list) if news_list else "Новости не найдены."
    except Exception as e:
        print("Ошибка при парсинге новостей:", e)
        return "Ошибка при загрузке новостей."

def get_potep_news():
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        news_url = "https://ria.ru/keyword_globalnoe_poteplenie/"  # <-- актуальный раздел экологии
        r = requests.get(news_url, headers=headers, timeout=10)
        soup = BeautifulSoup(r.text, 'html.parser')

        news_elements = soup.select('a.list-item__title.color-font-hover-only')[:5]

        news_list = []
        for item in news_elements:
            title = item.get_text(strip=True)
            link = item['href']
            news_list.append(f"📰 {title}\n🔗 {link}")

        return "\n\n".join(news_list) if news_list else "Новости не найдены."
    except Exception as e:
        print("Ошибка при парсинге новостей:", e)
        return "Ошибка при загрузке новостей."


def global_warming_info():
    return ("🌍 Что такое глобальное потепление?\n"
            "Глобальное потепление — это увеличение средней температуры Земли из-за парниковых газов.\n\n"
            "🌡 Причины:\n"
            "1. Сжигание топлива\n2. Вырубка лесов\n3. Индустриализация\n\n"
            "🌿 Как помочь:\n"
            "1. Снизьте выбросы\n2. Используйте зелёную энергию\n3. Экономьте ресурсы\n4. Поддерживайте природу.")



# Обработка команды /tp
@bot.message_handler(commands=['tp'])
def ask_question(message):
    msg = bot.send_message(message.chat.id, "📝 Напиши свой вопрос, и он будет отправлен администратору.")
    bot.register_next_step_handler(msg, forward_to_admin)

def forward_to_admin(message):
    user = message.from_user
    question = (
        f"📩 Новый вопрос от пользователя:\n\n"
        f"👤 Имя: {user.first_name} {user.last_name or ''}\n"
        f"🔗 Username: @{user.username or '—'}\n"
        f"🆔 ID: {user.id}\n\n"
        f"💬 Вопрос:\n{message.text}"
    )
    bot.send_message(ADMIN_ID, question)
    bot.send_message(message.chat.id, "✅ Вопрос отправлен! Мы скоро свяжемся с вами.")


@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Прогноз в Нижнем", "Предсказание", "Глобальное потепление")
    markup.add("Полезные советы", "Углеродный след", "Эко-новости", 'Новости Глобального потепления')

    bot.send_message(message.chat.id, f"Привет! Я бот про погоду и климат. Выбери действие 👇", reply_markup=markup)
    bot.send_message(message.chat.id, f"Что бы задать вопрос пишите /tp", reply_markup=markup)

# /subscribe и /unsubscribe
@bot.message_handler(commands=['subscribe'])
def subscribe(message):
    cursor.execute('INSERT OR IGNORE INTO subscriptions (user_id) VALUES (?)', (message.chat.id,))
    conn.commit()
    bot.send_message(message.chat.id, "✅ Подписка на ежедневную сводку оформлена!")

@bot.message_handler(commands=['unsubscribe'])
def unsubscribe(message):
    cursor.execute('DELETE FROM subscriptions WHERE user_id = ?', (message.chat.id,))
    conn.commit()
    bot.send_message(message.chat.id, "❌ Подписка отменена.")

# Ежедневная рассылка
def daily_forecast_job():
    while True:
        now = datetime.now()
        if now.hour == 8:
            today, tomorrow = get_temp_from_yandex()
            if today is not None:
                prediction = make_prediction(today, tomorrow)
                cursor.execute('SELECT user_id FROM subscriptions')
                for (user_id,) in cursor.fetchall():
                    bot.send_message(user_id, f"🌅 Доброе утро!\nСегодня: {today}°C\nЗавтра: {tomorrow}°C\n{prediction}\n🌱 Эко-совет дня: попробуйте день без пластика!")
            time.sleep(3600)
        else:
            time.sleep(300)

threading.Thread(target=daily_forecast_job, daemon=True).start()

# Углеродный след
user_carbon_progress = {}

@bot.message_handler(func=lambda message: message.text == "Углеродный след")
def carbon_start(message):
    user_carbon_progress[message.chat.id] = {"step": 1, "score": 0}
    bot.send_message(message.chat.id, "🚗 Вопрос 1: Как часто используете личный транспорт?\n1. Каждый день\n2. Иногда\n3. Никогда")

@bot.message_handler(func=lambda message: message.chat.id in user_carbon_progress)
def carbon_calc(message):
    state = user_carbon_progress[message.chat.id]
    step = state["step"]
    text = message.text.strip()
    if step == 1:
        state["score"] += {"1": 3, "2": 2, "3": 0}.get(text, 0)
        state["step"] = 2
        bot.send_message(message.chat.id, "💡 Вопрос 2: Вы выключаете свет, уходя из комнаты?\n1. Всегда\n2. Иногда\n3. Никогда")
    elif step == 2:
        state["score"] += {"1": 0, "2": 1, "3": 2}.get(text, 0)
        state["step"] = 3
        bot.send_message(message.chat.id, "🍽 Вопрос 3: Как часто вы едите мясо?\n1. Каждый день\n2. Иногда\n3. Редко или никогда")
    elif step == 3:
        state["score"] += {"1": 3, "2": 2, "3": 0}.get(text, 0)
        total = state["score"]
        del user_carbon_progress[message.chat.id]
        if total <= 3:
            msg = "🟢 Ваш углеродный след низкий — вы молодец!"
        elif total <= 6:
            msg = "🟡 Средний след — можно улучшить."
        else:
            msg = "🔴 Высокий углеродный след — подумайте о переменах!"
        bot.send_message(message.chat.id, f"🌍 Ваш результат: {total} баллов\n{msg}")



@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == "Прогноз в Нижнем":
        today, tomorrow = get_temp_from_yandex()
        if today is not None:
            date = datetime.now().strftime('%Y-%m-%d')
            save_forecast(date, today, tomorrow)
            bot.send_message(message.chat.id, f"🌆 Сегодня: {today}°C\n🔮 Завтра: {tomorrow}°C")
        else:
            bot.send_message(message.chat.id, "⚠️ Не получилось получить погоду.")
    elif message.text == "Предсказание":
        today, tomorrow = get_temp_from_yandex()
        prediction = make_prediction(today, tomorrow)
        bot.send_message(message.chat.id, prediction)
    elif message.text == "Глобальное потепление":
        bot.send_message(message.chat.id, global_warming_info())
    elif message.text == "Полезные советы":
        bot.send_message(message.chat.id, "✅ Советы:\n1. Экономьте энергию⚡\n2. Общественный транспорт🚌\n3. Сортировка мусора♻️\n4. Меньше пластика🌍")
    elif message.text == "Эко-новости":
        news = get_eco_news()
        bot.send_message(message.chat.id, news)
    elif message.text == "Новости Глобального потепления":
        news = get_potep_news()
        bot.send_message(message.chat.id, news)

    else:
        bot.send_message(message.chat.id, "❓ Я не понял. Пожалуйста, выбери кнопку или команду.")


bot.polling()
