import os
import telebot
from dotenv import load_dotenv
from flask import Flask
from threading import Thread

# Загрузка переменных окружения
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# Простой веб-сервер на Flask для Render, чтобы бот не засыпал
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

# Обработчик сообщений
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я твой бот, работающий на Gemini.")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    bot.reply_to(message, f"Ты сказал: {message.text}")

if __name__ == "__main__":
    # Запускаем Flask в отдельном потоке
    t = Thread(target=run_flask)
    t.start()
    
    # Запуск бота
    bot.infinity_polling()
