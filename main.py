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

# ================== ENV ==================
load_dotenv()

BOT_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

PORT = int(os.environ.get("PORT", 10000))

# ⚠️ YAHAN APNA RENDER URL DAALO
BASE_URL = "https://telegram-ai-bot-8jc5.onrender.com"

WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = BASE_URL + WEBHOOK_PATH


# ================== BOT HANDLERS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hi! I am your AI bot 🙂")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        # ✅ WORKING FREE MODEL
        "model": "meta-llama/llama-3.1-8b-instruct:free",
        "messages": [
            {"role": "user", "content": user_text}
        ],
        "max_tokens": 300,
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)

        if response.status_code == 200:
            reply = response.json()["choices"][0]["message"]["content"]
            await update.message.reply_text(reply.strip())
        else:
            print("OpenRouter error:", response.status_code, response.text)
            await update.message.reply_text("⚠️ AI error. Please try again.")

    except Exception as e:
        print("Exception:", e)
        await update.message.reply_text("⚠️ Server error.")


# ================== WEBHOOK ==================
async def webhook(request):
    telegram_app = request.app["telegram_app"]
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return web.Response(text="ok")


async def on_startup(app):
    telegram_app = app["telegram_app"]
    await telegram_app.initialize()
    await telegram_app.bot.delete_webhook(drop_pending_updates=True)
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

    app = web.Application()
    app["telegram_app"] = telegram_app

    app.router.add_post(WEBHOOK_PATH, webhook)
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    web.run_app(app, port=PORT)


if __name__ == "__main__":
    main()
