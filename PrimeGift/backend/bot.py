import logging
import sys
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo, MenuButtonWebApp
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from sqlalchemy import func

# Добавляем путь к приложению, чтобы видеть базу данных
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app import models

# --- КОНФИГ ---
TOKEN = "8060581855:AAFuo9YTbgQnki1zseuaqbIESR-ahH5yCSs"
ADMIN_IDS = [2053914171, 8141463258]
# Fallback URL (локальный), но на проде будет браться из ENV
WEBAPP_URL = "http://localhost:8080" 
CHANNEL_URL = "https://t.me/TGiftPrime"

# States
(
    ADD_PROMO_STATE,
    GIVE_ID,
    GIVE_AMOUNT,
    BROADCAST_MSG,
    SEARCH_USER
) = range(5)

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- DB HELPERS ---
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
        if not user: return False
        if currency == "stars": user.balance_stars += amount
        elif currency == "tickets": user.balance_tickets += amount
        db.commit()
        return True
    finally:
        db.close()

# --- HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    if user.id in ADMIN_IDS:
        text = (
            f"👑 <b>Приветствую, Создатель!</b>\n\n"
            f"⚠️ <b>Система Prime Gift работает в штатном режиме.</b>\n\n"
            f"👇 Управление доступно через панель администратора."
        )
    else:
        text = (
            f"👋 <b>Привет, {user.first_name}!</b>\n\n"
            f"🎁 Добро пожаловать в <b>Prime Gift</b>.\n"
            f"👇 <b>Жми кнопку и забирай свой первый дроп!</b>"
        )
    
    # Берем URL из ENV (Railway) или дефолтный
    web_app_url = os.getenv("WEBAPP_URL", WEBAPP_URL)
    
    # 1. Устанавливаем кнопку MENU (слева от ввода текста)
    if web_app_url.startswith("https"):
        try:
            await context.bot.set_chat_menu_button(
                chat_id=user.id,
                menu_button=MenuButtonWebApp(text="🚀 ИГРАТЬ", web_app=WebAppInfo(url=web_app_url))
            )
        except Exception as e:
            logging.error(f"Failed to set menu button: {e}")

    # 2. Красивая Inline кнопка
    if web_app_url.startswith("https"):
        play_btn = InlineKeyboardButton("💎 ЗАПУСТИТЬ PRIME GIFT 💎", web_app=WebAppInfo(url=web_app_url))
    else:
        play_btn = InlineKeyboardButton("🚀 ИГРАТЬ (Browser)", url=web_app_url)

    keyboard = [
        [play_btn],
        [InlineKeyboardButton("📢 Наш Канал", url=CHANNEL_URL)]
    ]
    
    if user.id in ADMIN_IDS:
        keyboard.append([InlineKeyboardButton("🔒 Админ Панель", callback_data="admin_panel")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    photo_path = "../frontend/public/NewYearCase.png"
    try:
        if os.path.exists(photo_path):
            await update.message.reply_photo(photo=open(photo_path, "rb"), caption=text, parse_mode="HTML", reply_markup=reply_markup)
        else:
            await update.message.reply_photo(photo="https://via.placeholder.com/600", caption=text, parse_mode="HTML", reply_markup=reply_markup)
    except:
        await update.message.reply_text(text, parse_mode="HTML", reply_markup=reply_markup)

# --- ADMIN PANEL ---

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Если это не callback (например, вызван из ConversationHandler), update.callback_query может быть None
    if update.callback_query:
        query = update.callback_query
        user_id = query.from_user.id
        try: await query.answer() 
        except: pass
    else:
        # Если вызвано как fallback
        query = update.message
        user_id = query.from_user.id
    
    if user_id not in ADMIN_IDS:
        return

    try:
        total_users, total_stars, total_tickets = get_stats()
    except Exception as e:
        logging.error(f"DB Error: {e}")
        total_users, total_stars, total_tickets = 0, 0, 0
    
    text = (
        f"🔒 <b>ПАНЕЛЬ АДМИНИСТРАТОРА</b>\n"
        f"➖➖➖➖➖➖➖➖➖➖\n"
        f"📊 <b>Статистика:</b>\n"
        f"👥 Юзеров: <b>{total_users}</b>\n"
        f"⭐️ Звезд: <b>{int(total_stars):,}</b>\n"
        f"🎫 Купонов: <b>{total_tickets}</b>"
    )
    
    keyboard = [
        [InlineKeyboardButton("💰 Выдать Баланс", callback_data="give_menu"), InlineKeyboardButton("🎫 Промокоды", callback_data="promo_menu")],
        [InlineKeyboardButton("📢 Рассылка", callback_data="broadcast_start"), InlineKeyboardButton("🔎 Поиск Юзера", callback_data="search_start")],
        [InlineKeyboardButton("🔄 Обновить", callback_data="admin_panel")]
    ]
    
    if update.callback_query:
        try:
            await query.edit_message_caption(caption=text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        except Exception:
            # Если это не фото, а текст - пробуем редактировать текст
            try:
                await query.edit_message_text(text=text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
            except Exception as e:
                logging.error(f"Edit message error: {e}")
                # Если всё совсем плохо - шлем новое
                await query.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        
        return ConversationHandler.END
    else:
        # Если вызвано как fallback (новым сообщением)
        await query.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END

# --- PROMO MENU ---

async def promo_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = "🎫 <b>Управление Промокодами</b>\nВыберите действие:"
    
    keyboard = [
        [InlineKeyboardButton("➕ Создать Промокод", callback_data="add_promo_start")],
        [InlineKeyboardButton("📋 Список и Удаление", callback_data="list_promos")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]
    ]
    await query.edit_message_caption(caption=text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

async def list_promos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    db = SessionLocal()
    promos = db.query(models.Promocode).all()
    db.close()
    
    if not promos:
        keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data="promo_menu")]]
        await query.edit_message_caption(caption="📭 <b>Список промокодов пуст.</b>", parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    text = "📋 <b>Активные Промокоды:</b>\n\nНажми на ❌ чтобы удалить."
    keyboard = []
    
    for p in promos:
        btn_text = f"❌ {p.code} ({p.current_usages}/{p.max_usages})"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"del_promo_{p.id}")])
        
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="promo_menu")])
    
    await query.edit_message_caption(caption=text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

async def delete_promo_btn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    promo_id = int(query.data.split("_")[-1])
    
    db = SessionLocal()
    promo = db.query(models.Promocode).filter(models.Promocode.id == promo_id).first()
    if promo:
        code_name = promo.code
        db.delete(promo)
        db.commit()
        await query.answer(f"✅ Промокод {code_name} удален!", show_alert=True)
    else:
        await query.answer("❌ Промокод не найден.", show_alert=True)
    db.close()
    
    await list_promos(update, context)

# --- GIVE BALANCE FLOW ---

async def give_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    text = "💰 <b>Что выдаем?</b>"
    keyboard = [
        [InlineKeyboardButton("⭐️ Звезды", callback_data="give_type_stars"), InlineKeyboardButton("🎫 Купоны", callback_data="give_type_tickets")],
        [InlineKeyboardButton("🔙 Назад", callback_data="admin_panel")]
    ]
    await query.edit_message_caption(caption=text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))

async def start_give(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    currency = query.data.split("_")[-1]
    context.user_data['give_currency'] = currency
    
    await query.edit_message_caption(
        f"✍️ Введите <b>ID пользователя</b>, которому выдаем {'⭐️ Звезды' if currency == 'stars' else '🎫 Купоны'}:",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Отмена", callback_data="cancel")]])
    )
    return GIVE_ID

async def handle_give_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = int(update.message.text.strip())
        context.user_data['give_id'] = user_id
        
        db = SessionLocal()
        user = db.query(models.User).filter(models.User.id == user_id).first()
        db.close()
        
        if not user:
            await update.message.reply_text("❌ Пользователь не найден в базе. Попробуй другой ID или нажми /cancel")
            return GIVE_ID
            
        await update.message.reply_text(
            f"✅ Юзер: <b>{user.first_name}</b> (@{user.username})\n"
            f"✍️ Введите <b>СУММУ</b>:", 
            parse_mode="HTML"
        )
        return GIVE_AMOUNT
    except ValueError:
        await update.message.reply_text("❌ Это не число. Введите ID цифрами.")
        return GIVE_ID

async def handle_give_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        amount = int(update.message.text.strip())
        user_id = context.user_data['give_id']
        currency = context.user_data['give_currency']
        
        give_balance(user_id, amount, currency)
        
        currency_icon = "⭐️" if currency == "stars" else "🎫"
        await update.message.reply_text(f"✅ <b>Успешно!</b>\nВыдано: {amount} {currency_icon}\nПользователю: {user_id}", parse_mode="HTML")
        
        try:
            await context.bot.send_message(user_id, f"🎁 <b>Администратор начислил вам {amount} {currency_icon}!</b>", parse_mode="HTML")
        except: pass
        
        text = "Вы вернулись в меню."
        keyboard = [[InlineKeyboardButton("🔒 Админ Панель", callback_data="admin_panel")]]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ Введите число.")
        return GIVE_AMOUNT

# --- BROADCAST FLOW ---

async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_caption(
        "📢 <b>Рассылка</b>\n\nОтправьте <b>сообщение</b> (текст, фото), которое получат ВСЕ пользователи.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Отмена", callback_data="cancel")]])
    )
    return BROADCAST_MSG

async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    
    db = SessionLocal()
    users = db.query(models.User).all()
    db.close()
    
    count = 0
    status_msg = await update.message.reply_text("⏳ Начинаю рассылку...")
    
    for u in users:
        try:
            await msg.copy(chat_id=u.id)
            count += 1
        except: pass
    
    await status_msg.edit_text(f"✅ <b>Рассылка завершена!</b>\nПолучили: {count} из {len(users)}", parse_mode="HTML")
    
    text = "Вы вернулись в меню."
    keyboard = [[InlineKeyboardButton("🔒 Админ Панель", callback_data="admin_panel")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

# --- SEARCH FLOW ---

async def search_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_caption(
        "🔎 <b>Поиск пользователя</b>\nВведите <b>ID</b> или <b>Username</b> (без @):",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Отмена", callback_data="cancel")]])
    )
    return SEARCH_USER

async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query_text = update.message.text.strip()
    db = SessionLocal()
    
    if query_text.isdigit():
        user = db.query(models.User).filter(models.User.id == int(query_text)).first()
    else:
        user = db.query(models.User).filter(models.User.username == query_text.replace("@", "")).first()
        
    if not user:
        await update.message.reply_text("❌ Не найден.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔒 Админ Панель", callback_data="admin_panel")]]))
        db.close()
        return ConversationHandler.END
    
    referrals = db.query(models.User).filter(models.User.referrer_id == user.id).count()
    
    text = (
        f"👤 <b>Профиль:</b> {user.first_name} (@{user.username})\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"⭐️ Баланс: {user.balance_stars}\n"
        f"🎫 Купоны: {user.balance_tickets}\n"
        f"👥 Рефералов: {referrals}\n"
        f"📅 Рег: {user.created_at.strftime('%Y-%m-%d')}"
    )
    
    await update.message.reply_text(text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔒 Админ Панель", callback_data="admin_panel")]]))
    db.close()
    return ConversationHandler.END

# --- ADD PROMO ---

async def start_add_promo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    text = (
        "➕ <b>Создание Промокода</b>\n\n"
        "Введите <b>КОД</b> и <b>ЛИМИТ</b> через пробел.\n"
        "<i>Пример:</i> <code>WELCOME 1000</code>\n"
        "<i>Пример 2:</i> <code>SECRET</code> (лимит 10000)"
    )
    keyboard = [[InlineKeyboardButton("🔙 Отмена", callback_data="cancel_add")]]
    
    await query.edit_message_caption(caption=text, parse_mode="HTML", reply_markup=InlineKeyboardMarkup(keyboard))
    return ADD_PROMO_STATE

async def handle_promo_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text_in = update.message.text.strip().split()
    code = text_in[0].upper()
    limit = int(text_in[1]) if len(text_in) > 1 else 10000
    
    db = SessionLocal()
    exists = db.query(models.Promocode).filter(models.Promocode.code == code).first()
    if exists:
        await update.message.reply_text(f"⚠️ Промокод <b>{code}</b> уже существует! Попробуй другой.")
        db.close()
        return ADD_PROMO_STATE
        
    new_promo = models.Promocode(code=code, max_usages=limit)
    db.add(new_promo)
    db.commit()
    db.close()
    
    await update.message.reply_text(f"✅ <b>Успешно!</b>\nПромокод: <code>{code}</code>\nЛимит: {limit}")
    
    text = "Вы вернулись в меню."
    keyboard = [[InlineKeyboardButton("🎫 К промокодам", callback_data="promo_menu")]]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END

async def cancel_add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Отменено")
    await promo_menu(update, context)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Отменено")
    await admin_panel(update, context)
    return ConversationHandler.END

async def broadcast_demo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("Рассылка в разработке", show_alert=True)

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    
    # FALLBACK for admin panel
    admin_handler = CallbackQueryHandler(admin_panel, pattern="^admin_panel$")

    # CONVERSATION HANDLERS
    add_promo_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_add_promo, pattern="^add_promo_start$")],
        states={ADD_PROMO_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_promo_input)]},
        fallbacks=[CallbackQueryHandler(cancel_add, pattern="^cancel_add$"), admin_handler],
        allow_reentry=True
    )
    
    give_balance_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(start_give, pattern="^give_type_")],
        states={
            GIVE_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_give_id)],
            GIVE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_give_amount)]
        },
        fallbacks=[CallbackQueryHandler(cancel, pattern="^cancel$"), admin_handler],
        allow_reentry=True
    )
    
    broadcast_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(broadcast_start, pattern="^broadcast_start$")],
        states={BROADCAST_MSG: [MessageHandler(filters.ALL & ~filters.COMMAND, handle_broadcast)]},
        fallbacks=[CallbackQueryHandler(cancel, pattern="^cancel$"), admin_handler],
        allow_reentry=True
    )
    
    search_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(search_start, pattern="^search_start$")],
        states={SEARCH_USER: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_search)]},
        fallbacks=[CallbackQueryHandler(cancel, pattern="^cancel$"), admin_handler],
        allow_reentry=True
    )
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(admin_handler) # Глобальный хендлер (приоритетный)
    app.add_handler(add_promo_handler)
    app.add_handler(give_balance_handler)
    app.add_handler(broadcast_handler)
    app.add_handler(search_handler)
    
    # MENU HANDLERS
    app.add_handler(CallbackQueryHandler(give_menu, pattern="^give_menu$"))
    app.add_handler(CallbackQueryHandler(promo_menu, pattern="^promo_menu$"))
    app.add_handler(CallbackQueryHandler(list_promos, pattern="^list_promos$"))
    app.add_handler(CallbackQueryHandler(delete_promo_btn, pattern="^del_promo_"))
    
    print("🤖 Bot Prime Gift Ultimate is running...")
    app.run_polling()