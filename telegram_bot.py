import asyncio
import logging
import sqlite3
import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from apscheduler.schedulers.background import BackgroundScheduler
from config import vtv_plantas, meses, database_path, TELEGRAM_BOT_API_KEY

logger = logging.getLogger(__name__)


def initialize_db():
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS turnos (
            id INTEGER PRIMARY KEY,
            plant TEXT,
            month INTEGER,
            year INTEGER,
            date TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_notifications (
            user_id INTEGER,
            plant TEXT,
            month INTEGER,
            year INTEGER,
            PRIMARY KEY (user_id, plant, month, year)
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS request_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            chat_id INTEGER,
            message TEXT,
            command TEXT,
            plant TEXT,
            timestamp TEXT
        )
    """)
    conn.commit()
    conn.close()


def log_request(update: Update, command: str = None, plant: str = None):
    """Log the request with metadata into the database."""
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()

    user_id = update.effective_user.id
    username = update.effective_user.username
    chat_id = update.effective_chat.id
    message = update.message.text if update.message else None
    timestamp = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO request_logs (user_id, username, chat_id, message, command, plant, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, username, chat_id, message, command, plant, timestamp))

    conn.commit()
    conn.close()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    log_request(update, command="/start")
    keyboard = [[InlineKeyboardButton(name, callback_data='plant-' + code)] for code, name in vtv_plantas.items()]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Elegí tu planta de VTV preferida:', reply_markup=reply_markup)


async def plant_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    plant_code = query.data.split('-')[1]
    context.user_data['plant'] = plant_code
    log_request(update, command="plant_chosen", plant=vtv_plantas.get(plant_code))

    current_month = datetime.now().month
    current_year = datetime.now().year
    months = [(current_month + i) % 12 or 12 for i in range(6)]
    years = [current_year + (current_month + i - 1) // 12 for i in range(6)]

    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    keyboard = []
    for month, year in zip(months, years):
        cursor.execute("SELECT COUNT(*) FROM turnos WHERE plant = ? AND month = ? AND year = ?",
                       (plant_code, month, year))
        count = cursor.fetchone()[0]
        if count > 0:
            button_text = f"{month:02d}-{year} (Disponible)"
            callback_data = f"{month:02d}-{year}"
        else:
            button_text = f"{month:02d}-{year} (Notificame)"
            callback_data = f"notify-{month:02d}-{year}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=callback_data)])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text('Elegí el mes y el año:', reply_markup=reply_markup)


async def month_year_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id
    plant_id = context.user_data.get('plant')
    log_request(update, command="month_year_chosen", plant=vtv_plantas.get(plant_id))
    month, year = map(int, re.search(r'(\d{2})-(\d{4})', data).groups())

    if "notify" in data:
        store_notification_request(user_id, plant_id, month, year)
        message_text = f"Genial! Te notificaré cuando haya turnos disponibles para la planta de \
{vtv_plantas[plant_id]} en {meses[month]}."
    else:
        dates = get_available_dates(plant_id, month, year)
        message_text = f"Hay turnos disponibles en la planta {vtv_plantas[plant_id]} para {meses[month]}:\n\n" \
            + "\n".join(dates) if dates else "No hay turnos disponibles."

    await query.message.reply_text(message_text)


def store_notification_request(user_id, plant, month, year):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO user_notifications (user_id, plant, month, year) VALUES (?, ?, ?, ?)",
                   (user_id, plant, month, year))
    conn.commit()
    conn.close()


def get_available_dates(plant, month, year):
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT date FROM turnos WHERE plant = ? AND month = ? AND year = ?", (plant, month, year))
    return [date[0] for date in cursor.fetchall()]


def check_and_notify():
    conn = sqlite3.connect(database_path)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, plant, month, year FROM user_notifications")
    notifications = cursor.fetchall()

    for user_id, plant, month, year in notifications:
        cursor.execute("SELECT COUNT(*) FROM turnos WHERE plant = ? AND month = ? AND year = ?", (plant, month, year))
        if cursor.fetchone()[0] > 0:
            asyncio.run(send_notification(user_id, plant, month, year))
            cursor.execute("DELETE FROM user_notifications WHERE user_id = ? AND plant = ? AND month = ? AND year = ?",
                           (user_id, plant, month, year))
            conn.commit()
    conn.close()


async def send_notification(user_id, plant, month, year):
    dates = get_available_dates(plant, month, year)
    application = Application.builder().token(TELEGRAM_BOT_API_KEY).build()
    bot = application.bot
    await bot.send_message(chat_id=user_id, text=f"Hay nuevos turnos disponibles en la planta de {vtv_plantas[plant]} \
para {meses[month]}!\n\n" + "\n".join(dates))


def main():
    initialize_db()
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_and_notify, 'interval', minutes=1)
    scheduler.start()
    application = Application.builder().token(TELEGRAM_BOT_API_KEY).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, start))
    application.add_handler(CallbackQueryHandler(plant_chosen, pattern="^plant-"))
    application.add_handler(CallbackQueryHandler(month_year_chosen, pattern=r'^(notify-)?\d{2}-\d{4}$'))
    application.run_polling()


if __name__ == '__main__':
    main()
