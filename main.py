import telebot
from telebot import types
import requests
import sqlite3
from datetime import datetime, timedelta
from transformers import pipeline

API_TOKEN = 'YOUR_API_TOKEN'
bot = telebot.TeleBot(API_TOKEN)

summarizer = pipeline("summarization")

conn = sqlite3.connect('temperature.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS temperatures (
    date TEXT PRIMARY KEY,
    temperature REAL
)
''')
conn.commit()

def fetch_weather_data(city):
    api_key = 'YOUR_WEATHER_API_KEY'
    url = f'http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=metric'
    response = requests.get(url)
    return response.json()

def save_temperature(date, temperature):
    cursor.execute('INSERT OR REPLACE INTO temperatures (date, temperature) VALUES (?, ?)', (date, temperature))
    conn.commit()

def get_temperature(date):
    cursor.execute('SELECT temperature FROM temperatures WHERE date = ?', (date,))
    result = cursor.fetchone()
    return result[0] if result else None

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Что такое глобальное потепление?")
    btn2 = types.KeyboardButton("Как сдерживать потепление?")
    btn3 = types.KeyboardButton("Полезные советы")
    btn4 = types.KeyboardButton("Сводка с сайта")
    btn5 = types.KeyboardButton("Температура в Кстово")
    markup.add(btn1, btn2, btn3, btn4, btn5)
    bot.send_message(message.chat.id, "Привет! Я бот, который помогает в борьбе с глобальным потеплением. Выберите интересующий вас вопрос:", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    if message.text == "Что такое глобальное потепление?":
        bot.send_message(message.chat.id, "Глобальное потепление — это долгосрочное увеличение средней температуры Земли, вызванное человеческой деятельностью и природными факторами.")
    elif message.text == "Как сдерживать потепление?":
        bot.send_message(message.chat.id, "Можно сдерживать потепление, снижая выбросы парниковых газов, используя возобновляемые источники энергии и уменьшая потребление ресурсов.")
    elif message.text == "Полезные советы":
        bot.send_message(message.chat.id, "1. Экономьте электроэнергию.\n2. Используйте общественный транспорт.\n3. Сортируйте отходы.\n4. Поддерживайте экологические инициативы.")
    elif message.text == "Сводка с сайта":
        url = "https://www.un.org/ru/climatechange/science/causes-effects-climate-change"
        data = fetch_data_from_website(url)
        if data:
            summary = summarizer(data, max_length=130, min_length=30, do_sample=False)
            bot.send_message(message.chat.id, summary[0]['summary_text'])
        else:
            bot.send_message(message.chat.id, "Не удалось получить данные с сайта.")
    elif message.text == "Температура в Кстово":
        city = "Kstovo"
        weather_data = fetch_weather_data(city)
        if weather_data:
            today = datetime.now().strftime('%Y-%m-%d')
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            year_ago = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')

            today_temp = weather_data['list'][0]['main']['temp']
            tomorrow_temp = weather_data['list'][1]['main']['temp']

            save_temperature(today, today_temp)
            save_temperature(tomorrow, tomorrow_temp)

            yesterday_temp = get_temperature(yesterday)
            year_ago_temp = get_temperature(year_ago)

            bot.send_message(message.chat.id, f"Температура в Кстово:\nСегодня: {today_temp}°C\nЗавтра: {tomorrow_temp}°C\nВчера: {yesterday_temp}°C\nГод назад: {year_ago_temp}°C")
        else:
            bot.send_message(message.chat.id, "Не удалось получить данные о погоде.")
    else:
        bot.send_message(message.chat.id, "Извините, я не понимаю ваш запрос. Пожалуйста, выберите один из предложенных вариантов.")

@bot.message_handler(commands=['help'])
def send_help(message):
    bot.send_message(message.chat.id, "Этот бот помогает узнать больше о глобальном потеплении и способах его сдерживания. Используйте кнопки для навигации.")

bot.polling()
