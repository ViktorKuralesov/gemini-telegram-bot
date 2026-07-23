import os
import base64
import aiohttp
import asyncio
import telebot
from dotenv import load_dotenv
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# 1. Веб-сервер для проверки статуса на Render (чтобы хостинг не усыплял бота)
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_health_check():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

Thread(target=run_health_check, daemon=True).start()

# 2. Переменные окружения и инициализация бота
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
API_KEY = os.getenv('GEMINI_API_KEY') or os.getenv('API_KEY')

bot = telebot.TeleBot(TOKEN)

# 3. Запрос к Gemini API
async def ask_gemini(prompt, image_bytes=None):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"
    parts = []
    if image_bytes:
        encoded_image = base64.b64encode(image_bytes).decode('utf-8')
        parts.append({
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": encoded_image
            }
        })
    parts.append({"text": prompt})

    payload = {"contents": [{"parts": parts}]}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                try:
                    return data['candidates'][0]['content']['parts'][0]['text']
                except (KeyError, IndexError):
                    return "Не удалось обработать ответ от модели."
            else:
                return f"Ошибка API: {response.status}"

# 4. Обработчики сообщений Telegram
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я бот на базе Gemini. Напиши мне что-нибудь или отправь картинку.")

@bot.message_handler(content_types=['text'])
def handle_text(message):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    response_text = loop.run_until_complete(ask_gemini(message.text))
    bot.reply_to(message, response_text)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    bot.reply_to(message, "Обрабатываю картинку...")
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)
    
    caption = message.caption or "Опиши эту картинку"
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    response_text = loop.run_until_complete(ask_gemini(caption, downloaded_file))
    bot.reply_to(message, response_text)

if __name__ == '__main__':
    bot.infinity_polling()
