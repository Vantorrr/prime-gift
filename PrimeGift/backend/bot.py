import logging
import sys
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from sqlalchemy import func

# Добавляем путь к приложению, чтобы видеть базу данных
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app import models

# --- КОНФИГ ---
TOKEN = "8060581855:AAFuo9YTbgQnki1zseuaqbIESR-ahH5yCSs"

ADMIN_IDS = [2053914171, 8141463258]
WEBAPP_URL = "http://localhost:8080" # Для локального теста (в Telegram Desktop откроется, на телефоне нужен HTTPS/ngrok)
CHANNEL_URL = "https://t.me/TGiftPrime"

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- DB HELPERS ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_stats():
    db = SessionLocal()
    try:
        total_users = db.query(models.User).count()
        total_stars = db.query(func.sum(models.User.balance_stars)).scalar() or 0
        total_tickets = db.query(func.sum(models.User.balance_tickets)).scalar() or 0
        return total_users, total_stars, total_tickets
    finally:
        db.close()

def give_balance(user_id: int, amount: int, currency: str):
    db = SessionLocal()
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            return False
        
        if currency == "stars":
            user.balance_stars += amount
        elif currency == "tickets":
            user.balance_tickets += amount
            
        db.commit()
        return True
    finally:
        db.close()

# --- HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Красивое приветствие
    text = (
        f"👋 <b>Привет, {user.first_name}!</b>\n\n"
        f"🎁 Добро пожаловать в <b>Prime Gift</b> — место, где мечты становятся реальностью.\n\n"
        f"🔥 <b>Что тебя ждет?</b>\n"
        f"• Эксклюзивные кейсы с техникой Apple и Tesla\n"
        f"• PvP Арена на Звезды\n"
        f"• Ежедневные бесплатные прокруты\n\n"
        f"👇 <b>Жми кнопку и забирай свой первый дроп!</b>"
    )
    
    # Telegram требует HTTPS для WebApp.
    # Если мы локально (http), то делаем обычную кнопку-ссылку, которая откроет браузер.
    if WEBAPP_URL.startswith("https"):
        play_btn = InlineKeyboardButton("🚀 ИГРАТЬ СЕЙЧАС", web_app=WebAppInfo(url=WEBAPP_URL))
    else:
        # Fallback для локальной разработки (откроется в Safari/Chrome)
        play_btn = InlineKeyboardButton("🚀 ИГРАТЬ (Browser)", url=WEBAPP_URL)

    keyboard = [
        [play_btn],
        [InlineKeyboardButton("📢 Наш Канал", url=CHANNEL_URL)]
    ]
    
    # Если Админ - добавляем кнопку панели
    if user.id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("🔒 Админ Панель", callback_data="admin_panel")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем с фото
    # Используем картинку из фронтенда (локально) или URL
    photo_path = "../frontend/public/NewYearCase.png"
    if os.path.exists(photo_path):
        photo = open(photo_path, "rb")
    else:
        photo = "https://media.istockphoto.com/id/1345334554/photo/3d-render-gift-box-with-gold-ribbon-on-blue-background.jpg?s=612x612&w=0&k=20&c=3-XnZLqXqgVqZqXqXqXqXqXqXqXqXqXqXqXqXqXqXq"

    await update.message.reply_photo(
        photo=photo, 
        caption=text,
        parse_mode="HTML",
        reply_markup=reply_markup
    )

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id not in ADMIN_IDS:
        await query.answer("Доступ запрещен ⛔️", show_alert=True)
        return

    total_users, total_stars, total_tickets = get_stats()
    
    text = (
        f"🔒 <b>ПАНЕЛЬ АДМИНИСТРАТОРА</b>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"👥 Пользователей: <b>{total_users}</b>\n"
        f"⭐️ Всего Звезд: <b>{int(total_stars):,}</b>\n"
        f"🎫 Всего Билетов: <b>{total_tickets}</b>\n\n"
        f"⚡️ <b>Управление:</b>\n"
        f"Для начисления баланса используй команды:\n"
        f"<code>/give_stars ID СУММА</code>\n"
        f"<code>/give_tickets ID СУММА</code>"
    )
    
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить", callback_data="admin_panel")],
        [InlineKeyboardButton("📢 Рассылка (Demo)", callback_data="broadcast_demo")]
    ]
    
    if query.message:
        await query.edit_message_caption(caption=text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await context.bot.send_message(chat_id=user_id, text=text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        return

    # Обработка кнопки панели из команды /admin
    await update.message.reply_text("Открываю панель...", reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("Открыть Панель", callback_data="admin_panel")]
    ]))

async def give_stars_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    
    try:
        # /give_stars 12345 1000
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("❌ Формат: /give_stars ID СУММА")
            return
            
        target_id = int(args[0])
        amount = int(args[1])
        
        success = give_balance(target_id, amount, "stars")
        if success:
            await update.message.reply_text(f"✅ Выдано {amount} ⭐️ пользователю {target_id}")
            try:
                await context.bot.send_message(target_id, f"🎁 <b>Администратор начислил вам {amount} Stars!</b>", parse_mode="HTML")
            except:
                pass # Юзер мог заблочить бота
        else:
            await update.message.reply_text("❌ Пользователь не найден в базе.")
            
    except ValueError:
        await update.message.reply_text("❌ Ошибка в числах.")

async def give_tickets_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS: return
    
    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("❌ Формат: /give_tickets ID СУММА")
            return
            
        target_id = int(args[0])
        amount = int(args[1])
        
        success = give_balance(target_id, amount, "tickets")
        if success:
            await update.message.reply_text(f"✅ Выдано {amount} 🎫 пользователю {target_id}")
            try:
                await context.bot.send_message(target_id, f"🎁 <b>Администратор начислил вам {amount} Tickets!</b>", parse_mode="HTML")
            except:
                pass
        else:
            await update.message.reply_text("❌ Пользователь не найден в базе.")
            
    except ValueError:
        await update.message.reply_text("❌ Ошибка в числах.")

async def broadcast_demo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Рассылка в разработке (нужен State Machine)", show_alert=True)

# --- MAIN ---
if __name__ == '__main__':
    if TOKEN == "YOUR_BOT_TOKEN":
        print("❌ ОШИБКА: Вставь токен бота в файл PrimeGift/backend/bot.py")
        exit()

    app = ApplicationBuilder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_command))
    app.add_handler(CommandHandler("give_stars", give_stars_command))
    app.add_handler(CommandHandler("give_tickets", give_tickets_command))
    
    app.add_handler(CallbackQueryHandler(admin_panel, pattern="^admin_panel$"))
    app.add_handler(CallbackQueryHandler(broadcast_demo, pattern="^broadcast_demo$"))
    
    print("🤖 Бот Prime Gift запущен...")
    app.run_polling()

