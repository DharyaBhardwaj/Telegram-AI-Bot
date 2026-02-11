import os
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

load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

PORT = int(os.environ.get("PORT", 10000))

BASE_URL = "https://telegram-ai-bot-8jc5.onrender.com"
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = BASE_URL + WEBHOOK_PATH


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Groq AI Bot is ready!")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not GROQ_API_KEY:
        await update.message.reply_text("❌ GROQ_API_KEY not found in ENV")
        return

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": "llama3-8b-8192",
        "messages": [
            {"role": "user", "content": update.message.text}
        ],
        "max_tokens": 300,
    }

    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60,
    )

    print("STATUS:", r.status_code)
    print("BODY:", r.text)

    if r.status_code == 200:
        reply = r.json()["choices"][0]["message"]["content"]
        await update.message.reply_text(reply)
    else:
        await update.message.reply_text(
            f"❌ Groq error {r.status_code}\nCheck Render logs"
        )


async def webhook(request):
    tg_app = request.app["tg_app"]
    data = await request.json()
    update = Update.de_json(data, tg_app.bot)
    await tg_app.process_update(update)
    return web.Response(text="ok")


async def on_startup(app):
    tg_app = app["tg_app"]
    await tg_app.initialize()
    await tg_app.bot.delete_webhook(drop_pending_updates=True)
    await tg_app.bot.set_webhook(WEBHOOK_URL)
    print("Webhook set")


def main():
    tg_app = ApplicationBuilder().token(BOT_TOKEN).build()
    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app = web.Application()
    app["tg_app"] = tg_app
    app.router.add_post(WEBHOOK_PATH, webhook)
    app.on_startup.append(on_startup)

    web.run_app(app, port=PORT)


if __name__ == "__main__":
    main()
