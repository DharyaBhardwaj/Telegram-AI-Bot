import os
import json
import requests
from dotenv import load_dotenv
from aiohttp import web
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ───────── ENV ─────────
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

PORT = int(os.environ.get("PORT", 10000))
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"

# ⚠️ CHANGE THIS to your Render URL
BASE_URL = "https://telegram-ai-bot-8jc5.onrender.com"
WEBHOOK_URL = BASE_URL + WEBHOOK_PATH


# ───────── BOT HANDLERS ─────────
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
        print("OpenRouter error:", e)
        await update.message.reply_text("⚠️ AI error.")


# ───────── WEBHOOK SERVER ─────────
async def webhook(request):
    app = request.app["telegram_app"]
    data = await request.json()
    update = Update.de_json(data, app.bot)
    await app.process_update(update)
    return web.Response(text="ok")


async def on_startup(app):
    telegram_app = app["telegram_app"]
    await telegram_app.initialize()
    await telegram_app.bot.set_webhook(WEBHOOK_URL)
    print("✅ Webhook set:", WEBHOOK_URL)


async def on_cleanup(app):
    telegram_app = app["telegram_app"]
    await telegram_app.shutdown()


def main():
    telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    web_app = web.Application()
    web_app["telegram_app"] = telegram_app

    web_app.router.add_post(WEBHOOK_PATH, webhook)
    web_app.on_startup.append(on_startup)
    web_app.on_cleanup.append(on_cleanup)

    web.run_app(web_app, port=PORT)


if __name__ == "__main__":
    main()
