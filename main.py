import os
import base64
import aiohttp
import asyncio
import telebot
from dotenv import load_dotenv
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler

# 1. Веб-сервер для проверки статуса на Render (Health Check)
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_check():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

Thread(target=run_health_check, daemon=True).start()

# 2. Инициализация переменных окружения
load_dotenv()
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
API_KEY = os.getenv('GEMINI_API_KEY') or os.getenv('API_KEY')

bot = telebot.TeleBot(TOKEN)

# 3. Прямое обращение к Google Gemini API
async def ask_gemini(prompt, image_bytes=None):
url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"    
    
    parts = []
    if image_bytes:
        encoded_image = base64.b64encode(image_bytes).decode('utf-8')
        parts.append({
            "inline_data": {
                "mime_type": "image/jpeg",
                "data": encoded_image
            }
        })
    
    parts.append({"text": prompt or "Что изображено на этом фото?"})

    payload = {"contents": [{"parts": parts}]}

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                try:
                    return data['candidates'][0]['content']['parts'][0]['text']
                except (KeyError, IndexError):
                    return "Ошибка: не удалось прочитать ответ от Gemini."
            else:
                err = await resp.text()
                return f"Ошибка Gemini API ({resp.status}). Проверьте ваш API-ключ."

# 4. Обработка входящих сообщений Telegram
@bot.message_handler(content_types=['text', 'photo'])
def handle_message(message):
    bot.send_chat_action(message.chat.id, 'typing')
    
    prompt = message.caption if message.content_type == 'photo' else message.text
    image_bytes = None

    if message.content_type == 'photo':
        file_info = bot.get_file(message.photo[-1].file_id)
        image_bytes = bot.download_file(file_info.file_path)

    async def process():
        response_text = await ask_gemini(prompt, image_bytes)
        
        # Отправка ответа пользователю с поддержкой длинных сообщений
        for chunk in [response_text[i:i+4000] for i in range(0, len(response_text), 4000)]:
            try:
                bot.send_message(message.chat.id, chunk, parse_mode='Markdown')
            except Exception:
                bot.send_message(message.chat.id, chunk)

    asyncio.run(process())

if __name__ == '__main__':
    print("Bot started")
    bot.polling(none_stop=True)
