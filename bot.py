import os
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    if update.message.text:
        await context.bot.send_message(
            chat_id=CHANNEL_ID,
            text=update.message.text
        )

    if update.message.photo:
        photo = update.message.photo[-1].file_id
        await context.bot.send_photo(
            chat_id=CHANNEL_ID,
            photo=photo
        )

app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(MessageHandler(filters.ALL, handle_message))

app.run_polling()
