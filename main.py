import os
import json
import requests
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.ext.webhookhandler import WebhookHandler
from aiohttp import web

# Load env
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_PATH = f"/webhook/{TELEGRAM_TOKEN}"
WEBHOOK_URL = f"https://telegram-ai-bot-8jc5.onrender.com{WEBHOOK_PATH}"

# ───────── Handlers ─────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! I'm your AI bot (Webhook mode).")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_input = update.message.text

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "meta-llama/llama-4-scout:free",
        "messages": [{"role": "user", "content": user_input}],
        "max_tokens": 500,
    }

    try:
        r = requests.post(url, headers=headers, json=data, timeout=60)
        reply = r.json()["choices"][0]["message"]["content"]
        await update.message.reply_text(reply.strip())
    except Exception as e:
        print(e)
        await update.message.reply_text("⚠️ Error occurred.")

# ───────── Webhook App ─────────

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    await app.initialize()
    await app.bot.set_webhook(WEBHOOK_URL)

    webhook_handler = WebhookHandler(app)
    aio_app = web.Application()
    aio_app.router.add_post(WEBHOOK_PATH, webhook_handler.handle)

    return aio_app

if __name__ == "__main__":
    web.run_app(main(), port=PORT)
