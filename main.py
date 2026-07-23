import os
import telebot
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
from google import genai

load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

bot = telebot.TeleBot(TOKEN)
client = genai.Client(api_key=GEMINI_API_KEY)

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я твой бот на базе Gemini. Задай мне любой вопрос!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=message.text,
        )
        bot.reply_to(message, response.text)
    except Exception as e:
        bot.reply_to(message, f"Произошла ошибка при обращении к нейросети: {e}")

if __name__ == "__main__":
    # Принудительно сбрасываем старый вебхук перед стартом
    try:
        bot.remove_webhook()
    except Exception:
        pass
        
    t = Thread(target=run_flask)
    t.start()
    bot.infinity_polling()
