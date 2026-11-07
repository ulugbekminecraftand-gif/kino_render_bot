import os
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, filters, ContextTypes
)

TOKEN = os.getenv("BOT_TOKEN", "8760830688:AAGs9MsOUMrYxyAPKIh_miYCwewln2kAJK0")
ADMIN_ID = int(os.getenv("ADMIN_ID", "8763018871"))
CHANNEL = "@yangikinoolami2"  # kanal username'i

db = sqlite3.connect("kino.db", check_same_thread=False)
db.execute("""
CREATE TABLE IF NOT EXISTS kino (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_id TEXT,
    caption TEXT
)
""")
db.commit()


async def is_subscribed(user_id, context):
    try:
        member = await context.bot.get_chat_member(CHANNEL, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False


def subscribe_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Kanalga obuna bo'lish",
                              url=f"https://t.me/{CHANNEL.lstrip('@')}")],
        [InlineKeyboardButton("✅ Tekshirish", callback_data="check")],
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom! 🎬 Kino kodini yuboring.")


async def save_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    msg = update.message
    cur = db.execute(
        "INSERT INTO kino (file_id, caption) VALUES (?, ?)",
        (msg.video.file_id, msg.caption or ""),
    )
    db.commit()
    await msg.reply_text(f"✅ Kino saqlandi!\n🔢 Kodi: {cur.lastrowid}")


async def get_movie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    # Obunani tekshirish
    if not await is_subscribed(user_id, context):
        await update.message.reply_text(
            "❗ Botdan foydalanish uchun avval kanalimizga obuna bo'ling:",
            reply_markup=subscribe_keyboard(),
        )
        return

    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("Iltimos, faqat kino kodini (raqam) yozing.")
        return

    row = db.execute(
        "SELECT file_id, caption FROM kino WHERE id = ?", (int(text),)
    ).fetchone()
    if row:
        await update.message.reply_video(
            row[0], caption=f"🎬 Kod: {text}\n{row[1]}"
        )
    else:
        await update.message.reply_text("❌ Bunday kodli kino topilmadi.")


async def check_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if await is_subscribed(query.from_user.id, context):
        await query.answer("Rahmat! ✅")
        await query.message.edit_text("✅ Obuna tasdiqlandi! Endi kino kodini yuboring.")
    else:
        await query.answer("Siz hali obuna bo'lmagansiz ❌", show_alert=True)


app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(check_callback, pattern="^check$"))
app.add_handler(MessageHandler(filters.VIDEO, save_video))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_movie))

print("Bot ishga tushdi...")
app.run_polling()