import os
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
PORT = int(os.environ.get("PORT", 10000))

BASE_URL = "https://telegram-ai-bot-8jc5.onrender.com"
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = BASE_URL + WEBHOOK_PATH


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot is WORKING!")

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"👋 You said:\n\n{update.message.text}"
    )


async def webhook(request):
    app = request.app["tg_app"]
    data = await request.json()
    update = Update.de_json(data, app.bot)
    await app.process_update(update)
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
    tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    app = web.Application()
    app["tg_app"] = tg_app
    app.router.add_post(WEBHOOK_PATH, webhook)
    app.on_startup.append(on_startup)

    web.run_app(app, port=PORT)


if __name__ == "__main__":
    main()
