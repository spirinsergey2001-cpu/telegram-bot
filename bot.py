import os
import asyncio
import sqlite3
from datetime import datetime
from telegram import Bot, Update, InputMediaPhoto
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = Bot(token=BOT_TOKEN)

conn = sqlite3.connect("posts.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    media TEXT,
    caption TEXT,
    published INTEGER DEFAULT 0
)
""")
conn.commit()

albums = {}

async def handle_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    if not msg.photo:
        return

    media_group_id = msg.media_group_id

    if media_group_id:
        albums.setdefault(media_group_id, []).append(msg.photo[-1].file_id)

        await asyncio.sleep(2)

        if len(albums[media_group_id]) >= 3:
            photos = albums.pop(media_group_id)

            caption = await generate_caption()

            cursor.execute(
                "INSERT INTO posts (media, caption) VALUES (?, ?)",
                (",".join(photos), caption)
            )
            conn.commit()

async def generate_caption():
    prompt = """
Ты байер премиум вещей.

Сделай короткий пост:

BRAND

Модель: MODEL NAME

📦 Эксклюзивная копия премиум-качества  
📩 Для консультации: @blackrare
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content

async def scheduler():
    while True:
        now = datetime.now().strftime("%H:%M")

        if now in ["09:00", "13:00", "19:00"]:
            cursor.execute("SELECT * FROM posts WHERE published=0 LIMIT 1")
            row = cursor.fetchone()

            if row:
                media_ids = row[1].split(",")
                caption = row[2]

                media = [
                    InputMediaPhoto(media_ids[0], caption=caption)
                ] + [
                    InputMediaPhoto(m) for m in media_ids[1:]
                ]

                await bot.send_media_group(chat_id=CHANNEL_ID, media=media)

                cursor.execute("UPDATE posts SET published=1 WHERE id=?", (row[0],))
                conn.commit()

        await asyncio.sleep(60)

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(MessageHandler(filters.PHOTO, handle_photos))

async def main():
    asyncio.create_task(scheduler())
    await app.run_polling()

asyncio.run(main())
