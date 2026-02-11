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

# ========= ENV =========
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

PORT = int(os.environ.get("PORT", 10000))

BASE_URL = "https://telegram-ai-bot-8jc5.onrender.com"
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = BASE_URL + WEBHOOK_PATH


# ========= BOT =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! I am your AI bot 🙂")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-pro:generateContent?key={GEMINI_API_KEY}"
    )

    payload = {
        "contents": [
            {"parts": [{"text": user_text}]}
        ]
    }

    try:
        r = requests.post(url, json=payload, timeout=60)

        if r.status_code == 200:
            reply = r.json()["candidates"][0]["content"]["parts"][0]["text"]
            await update.message.reply_text(reply)
        else:
            print("Gemini error:", r.text)
            await update.message.reply_text("⚠️ AI error. Try again later.")

    except Exception as e:
        print("Exception:", e)
        await update.message.reply_text("⚠️ Server error.")


# ========= WEBHOOK =========
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


async def on_cleanup(app):
    await app["tg_app"].shutdown()


def main():
    tg_app = ApplicationBuilder().token(BOT_TOKEN).build()

    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app = web.Application()
    app["tg_app"] = tg_app
    app.router.add_post(WEBHOOK_PATH, webhook)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    web.run_app(app, port=PORT)


if __name__ == "__main__":
    main()
