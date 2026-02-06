import asyncio
import logging
import re
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from config import cfg
from database import db

logging.basicConfig(level=logging.INFO)

bot = Bot(token=cfg.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# === ЛОКАЛИЗАЦИЯ ===
TEXTS = {
    "ru": {
        "welcome": "👋 Добро пожаловать в P2E Keys Shop!\n\n🔑 Здесь вы можете купить ключи для Play-to-Earn игр\n💰 Оплата принимается в USDT (TRC20)\n\nВыберите действие:",
        "choose_language": "🌍 Выберите язык / Choose language:",
        "language_set": "✅ Язык установлен: Русский",
        "sellers": "🛒 Продавцы",
        "reviews": "⭐ Отзывы",
        "support": "🆘 ТехПоддержка",
        "settings": "⚙️ Настройки",
        "admin_panel": "🔐 Админ панель",
        "back": "🔙 Назад",
        "select_seller": "🛒 Выберите продавца:\n\n",
        "no_sellers": "❌ Нет доступных продавцов!",
        "price": "💵 Цена",
        "keys_available": "📦 Ключей в наличии",
        "how_many": "❓ Сколько ключей хотите купить?",
        "available": "📦 Доступно",
        "order": "🛒 Заказ",
        "quantity": "📦 Количество",
        "total": "💵 Сумма к оплате",
        "payment_details": "📋 Реквизиты для оплаты USDT (TRC20):",
        "payment_id": "🆔 ID платежа",
        "after_payment": "⚠️ После оплаты нажмите кнопку ниже.\nАдминистратор проверит платеж и вышлет ключи.",
        "i_paid": "✅ Я оплатил",
        "payment_not_found": "❌ Платеж не найден!",
        "new_payment": "💰 Новая оплата!",
        "user": "👤 Пользователь",
        "seller": "🛒 Продавец",
        "amount": "💵 Сумма",
        "waiting_confirm": "⏳ Ожидаем подтверждения администратора...",
        "admin_notified": "✅ Администратор уведомлен!",
        "no_reviews": "⭐ Пока нет отзывов. Будьте первым!",
        "latest_reviews": "⭐ Последние отзывы:",
        "edited": "(изменено)",
        "support_title": "🆘 Техническая поддержка",
        "support_desc": "Опишите вашу проблему или вопрос одним сообщением.\nМы ответим вам как можно скорее!",
        "ticket_created": "✅ Ваше обращение #{ticket_id} принято!\nМы ответим вам в ближайшее время.",
        "new_ticket": "📩 Новый тикет #{ticket_id}",
        "from_user": "От",
        "reply_cmd": "Для ответа",
        "close_cmd": "Для закрытия",
        "settings_title": "⚙️ Ваши настройки",
        "your_id": "🆔 ID",
        "username": "👤 Username",
        "purchases": "🛒 Покупок",
        "wallet": "💰 Кошелек для выплат",
        "not_set": "Не установлен",
        "main_menu": "Главное меню:",
        "invalid_seller": "❌ Некорректный ID продавца!",
        "seller_not_found": "❌ Продавец не найден!",
        "out_of_stock": "❌ Ключи закончились!",
        "invalid_price": "❌ Цена должна быть больше 0!",
        "enter_number": "❌ Введите число!",
        "seller_added": "✅ Продавец добавлен!",
        "seller_deleted": "✅ Продавец удален!",
        "review_added": "✅ Отзыв #{review_id} добавлен!",
        "review_updated": "✅ Отзыв #{review_id} обновлен!",
        "review_deleted": "✅ Отзыв #{review_id} удален!",
        "keys_generated": "✅ Сгенерировано {count} ключей!",
        "no_tickets": "📩 Нет открытых тикетов.",
        "open_tickets": "📩 Открытые тикеты:",
        "no_pending": "✅ Нет ожидающих платежей.",
        "pending_payments": "⏳ Ожидают подтверждения:",
        "payment_confirmed": "✅ Оплата подтверждена!",
        "your_keys": "🔑 Ваши ключи ({count} шт.):",
        "save_keys": "💾 Сохраните их! Покажите это сообщение при входе в игру.",
        "keys_sent": "✅ Ключи отправлены пользователю {user_id}",
        "reply_sent": "✅ Ответ отправлен пользователю {user_id}",
        "ticket_closed": "✅ Тикет #{ticket_id} закрыт",
        "enter_seller_id": "Шаг 1/3: Введите ID продавца (только латинские буквы, цифры и _)\nНапример: seller_vip, super_keys, megashop",
        "enter_seller_name": "Шаг 2/3: Введите название продавца (с эмодзи):",
        "enter_price": "Шаг 3/3: Введите цену за ключ (число, например 2.5):",
        "enter_review_user": "Шаг 1/2: Введите ID пользователя (или @username):",
        "enter_review_text": "Шаг 2/2: Введите текст отзыва:",
        "select_review_edit": "✏️ Выберите отзыв для редактирования:",
        "select_review_delete": "🗑️ Выберите отзыв для удаления:",
        "enter_new_text": "Введите новый текст:",
        "how_many_keys": "🔢 Сколько ключей сгенерировать? (введите число от 1 до 100):",
        "select_seller_gen": "🔑 Выберите продавца для генерации ключей:",
        "stats": "📊 Статистика бота",
        "users_count": "👥 Пользователей",
        "total_keys": "🔑 Всего ключей",
        "confirm_usage": "Для подтверждения отправьте:\n/confirm [PAYMENT_ID]",
        "reply_usage": "Использование: /reply [TICKET_ID] [текст]",
        "close_usage": "Использование: /close [TICKET_ID]",
        "confirm_usage_cmd": "Использование: /confirm [PAYMENT_ID]",
        "already_paid": "❌ Платеж не найден или уже подтвержден!",
        "not_enough_keys": "❌ Недостаточно ключей! Нужно {need}, есть {have}",
        "key_error": "❌ Ошибка при выдаче ключей!",
        "ticket_not_found": "Тикет не найден!",
        "error_sending": "⚠️ Ошибка отправки",
        "id_empty": "❌ ID не может быть пустым! Используйте только латинские буквы и цифры.",
        "id_short": "❌ ID слишком короткий (минимум 3 символа)!",
        "id_exists": "❌ Такой ID уже существует! Введите другой:",
        "no_sellers_delete": "Нет продавцов для удаления!",
        "no_reviews_edit": "Нет отзывов для редактирования!",
        "no_reviews_delete": "Нет отзывов для удаления!",
        "review_not_found": "Отзыв не найден!",
        "update_error": "❌ Ошибка при обновлении!",
        "invalid_range": "❌ Введите число от 1 до 100!",
        "select_seller_delete": "➖ Выберите продавца для удаления:",
        "admin_panel_title": "🔐 Административная панель",
        "reviews_management": "📝 Управление отзывами",
        "choose_action": "Выберите действие:",
        "add_review": "➕ Добавить отзыв",
        "edit_review": "✏️ Редактировать отзыв",
        "delete_review": "🗑️ Удалить отзыв",
        "back_to_admin": "🔙 Назад в админку",
        "stats_btn": "📊 Статистика",
        "add_seller_btn": "➕ Добавить продавца",
        "delete_seller_btn": "➖ Удалить продавца",
        "reviews_btn": "📝 Управление отзывами",
        "tickets_btn": "📩 Тикеты поддержки",
        "gen_keys_btn": "🔑 Генерировать ключи",
        "confirm_btn": "✅ Подтвердить оплату",
        "cancel": "🔙 Отмена",
        "piece": "шт.",
        "for": "за",
        "pcs": "шт."
    },
    "en": {
        "welcome": "👋 Welcome to P2E Keys Shop!\n\n🔑 Here you can buy keys for Play-to-Earn games\n💰 Payment accepted in USDT (TRC20)\n\nChoose an action:",
        "choose_language": "🌍 Choose language / Выберите язык:",
        "language_set": "✅ Language set: English",
        "sellers": "🛒 Sellers",
        "reviews": "⭐ Reviews",
        "support": "🆘 Support",
        "settings": "⚙️ Settings",
        "admin_panel": "🔐 Admin Panel",
        "back": "🔙 Back",
        "select_seller": "🛒 Select a seller:\n\n",
        "no_sellers": "❌ No sellers available!",
        "price": "💵 Price",
        "keys_available": "📦 Keys available",
        "how_many": "❓ How many keys do you want to buy?",
        "available": "📦 Available",
        "order": "🛒 Order",
        "quantity": "📦 Quantity",
        "total": "💵 Total to pay",
        "payment_details": "📋 Payment details for USDT (TRC20):",
        "payment_id": "🆔 Payment ID",
        "after_payment": "⚠️ After payment, click the button below.\nAdministrator will verify and send the keys.",
        "i_paid": "✅ I paid",
        "payment_not_found": "❌ Payment not found!",
        "new_payment": "💰 New payment!",
        "user": "👤 User",
        "seller": "🛒 Seller",
        "amount": "💵 Amount",
        "waiting_confirm": "⏳ Waiting for administrator confirmation...",
        "admin_notified": "✅ Administrator notified!",
        "no_reviews": "⭐ No reviews yet. Be the first!",
        "latest_reviews": "⭐ Latest reviews:",
        "edited": "(edited)",
        "support_title": "🆘 Technical Support",
        "support_desc": "Describe your problem or question in one message.\nWe will reply as soon as possible!",
        "ticket_created": "✅ Your ticket #{ticket_id} has been received!\nWe will reply soon.",
        "new_ticket": "📩 New ticket #{ticket_id}",
        "from_user": "From",
        "reply_cmd": "To reply",
        "close_cmd": "To close",
        "settings_title": "⚙️ Your Settings",
        "your_id": "🆔 ID",
        "username": "👤 Username",
        "purchases": "🛒 Purchases",
        "wallet": "💰 Payout wallet",
        "not_set": "Not set",
        "main_menu": "Main menu:",
        "invalid_seller": "❌ Invalid seller ID!",
        "seller_not_found": "❌ Seller not found!",
        "out_of_stock": "❌ Out of stock!",
        "invalid_price": "❌ Price must be greater than 0!",
        "enter_number": "❌ Please enter a number!",
        "seller_added": "✅ Seller added!",
        "seller_deleted": "✅ Seller deleted!",
        "review_added": "✅ Review #{review_id} added!",
        "review_updated": "✅ Review #{review_id} updated!",
        "review_deleted": "✅ Review #{review_id} deleted!",
        "keys_generated": "✅ Generated {count} keys!",
        "no_tickets": "📩 No open tickets.",
        "open_tickets": "📩 Open tickets:",
        "no_pending": "✅ No pending payments.",
        "pending_payments": "⏳ Pending confirmation:",
        "payment_confirmed": "✅ Payment confirmed!",
        "your_keys": "🔑 Your keys ({count} pcs.):",
        "save_keys": "💾 Save them! Show this message when entering the game.",
        "keys_sent": "✅ Keys sent to user {user_id}",
        "reply_sent": "✅ Reply sent to user {user_id}",
        "ticket_closed": "✅ Ticket #{ticket_id} closed",
        "enter_seller_id": "Step 1/3: Enter seller ID (latin letters, numbers and _ only)\nExample: seller_vip, super_keys, megashop",
        "enter_seller_name": "Step 2/3: Enter seller name (with emoji):",
        "enter_price": "Step 3/3: Enter price per key (number, e.g. 2.5):",
        "enter_review_user": "Step 1/2: Enter user ID (or @username):",
        "enter_review_text": "Step 2/2: Enter review text:",
        "select_review_edit": "✏️ Select review to edit:",
        "select_review_delete": "🗑️ Select review to delete:",
        "enter_new_text": "Enter new text:",
        "how_many_keys": "🔢 How many keys to generate? (enter number from 1 to 100):",
        "select_seller_gen": "🔑 Select seller to generate keys for:",
        "stats": "📊 Bot Statistics",
        "users_count": "👥 Users",
        "total_keys": "🔑 Total keys",
        "confirm_usage": "To confirm send:\n/confirm [PAYMENT_ID]",
        "reply_usage": "Usage: /reply [TICKET_ID] [text]",
        "close_usage": "Usage: /close [TICKET_ID]",
        "confirm_usage_cmd": "Usage: /confirm [PAYMENT_ID]",
        "already_paid": "❌ Payment not found or already confirmed!",
        "not_enough_keys": "❌ Not enough keys! Need {need}, have {have}",
        "key_error": "❌ Error issuing keys!",
        "ticket_not_found": "Ticket not found!",
        "error_sending": "⚠️ Error sending",
        "id_empty": "❌ ID cannot be empty! Use latin letters and numbers only.",
        "id_short": "❌ ID too short (minimum 3 characters)!",
        "id_exists": "❌ This ID already exists! Enter another:",
        "no_sellers_delete": "No sellers to delete!",
        "no_reviews_edit": "No reviews to edit!",
        "no_reviews_delete": "No reviews to delete!",
        "review_not_found": "Review not found!",
        "update_error": "❌ Error updating!",
        "invalid_range": "❌ Enter a number from 1 to 100!",
        "select_seller_delete": "➖ Select seller to delete:",
        "admin_panel_title": "🔐 Administrative Panel",
        "reviews_management": "📝 Reviews Management",
        "choose_action": "Choose action:",
        "add_review": "➕ Add Review",
        "edit_review": "✏️ Edit Review",
        "delete_review": "🗑️ Delete Review",
        "back_to_admin": "🔙 Back to Admin",
        "stats_btn": "📊 Statistics",
        "add_seller_btn": "➕ Add Seller",
        "delete_seller_btn": "➖ Delete Seller",
        "reviews_btn": "📝 Reviews",
        "tickets_btn": "📩 Support Tickets",
        "gen_keys_btn": "🔑 Generate Keys",
        "confirm_btn": "✅ Confirm Payment",
        "cancel": "🔙 Cancel",
        "piece": "pc.",
        "for": "for",
        "pcs": "pcs."
    }
}

def get_text(user_id: int, key: str, **kwargs) -> str:
    """Получить текст на языке пользователя"""
    lang = db.get_user_language(user_id)
    text = TEXTS.get(lang, TEXTS["ru"]).get(key, key)
    if kwargs:
        text = text.format(**kwargs)
    return text

# === КЛАВИАТУРЫ ===
def language_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def main_menu(user_id: int, is_admin: bool = False):
    lang = db.get_user_language(user_id)
    t = TEXTS[lang]
    buttons = [
        [KeyboardButton(text=t["sellers"])],
        [KeyboardButton(text=t["reviews"]), KeyboardButton(text=t["support"])],
        [KeyboardButton(text=t["settings"])]
    ]
    if is_admin:
        buttons.append([KeyboardButton(text=t["admin_panel"])])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def sellers_keyboard(user_id: int):
    lang = db.get_user_language(user_id)
    t = TEXTS[lang]
    sellers = db.get_sellers()
    buttons = []
    for seller_id, data in sellers.items():
        if not re.match(r'^[a-zA-Z0-9_]+$', seller_id):
            continue
        btn_text = f"{data['name']} — ${data['price']}"
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"buy_{seller_id}")])
    buttons.append([InlineKeyboardButton(text=t["back"], callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def quantity_keyboard(user_id: int, seller_id: str, max_qty: int = 10):
    lang = db.get_user_language(user_id)
    t = TEXTS[lang]
    buttons = []
    row = []
    for i in range(1, min(max_qty + 1, 11)):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f"qty_{seller_id}_{i}"))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text=t["back"], callback_data="back_sellers")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_keyboard(user_id: int):
    lang = db.get_user_language(user_id)
    t = TEXTS[lang]
    buttons = [
        [InlineKeyboardButton(text=t["stats_btn"], callback_data="admin_stats")],
        [InlineKeyboardButton(text=t["add_seller_btn"], callback_data="admin_add_seller")],
        [InlineKeyboardButton(text=t["delete_seller_btn"], callback_data="admin_del_seller")],
        [InlineKeyboardButton(text=t["reviews_btn"], callback_data="admin_reviews")],
        [InlineKeyboardButton(text=t["tickets_btn"], callback_data="admin_tickets")],
        [InlineKeyboardButton(text=t["gen_keys_btn"], callback_data="admin_gen_keys")],
        [InlineKeyboardButton(text=t["confirm_btn"], callback_data="admin_confirm")],
        [InlineKeyboardButton(text=t["back"], callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def reviews_admin_keyboard(user_id: int):
    lang = db.get_user_language(user_id)
    t = TEXTS[lang]
    buttons = [
        [InlineKeyboardButton(text=t["add_review"], callback_data="admin_add_review")],
        [InlineKeyboardButton(text=t["edit_review"], callback_data="admin_edit_review")],
        [InlineKeyboardButton(text=t["delete_review"], callback_data="admin_del_review")],
        [InlineKeyboardButton(text=t["back_to_admin"], callback_data="admin_panel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# === СОСТОЯНИЯ ===
class SupportState(StatesGroup):
    waiting_message = State()

class AdminState(StatesGroup):
    add_seller_id = State()
    add_seller_name = State()
    add_seller_price = State()
    del_seller_select = State()
    confirm_payment = State()
    response_ticket = State()
    add_review_text = State()
    add_review_user = State()
    edit_review_select = State()
    edit_review_text = State()
    del_review_select = State()
    gen_keys_select = State()
    gen_keys_count = State()

# === ХЭНДЛЕРЫ ===

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Проверяем, есть ли пользователь в базе
    user_exists = str(message.from_user.id) in db.data["users"]
    
    if not user_exists:
        # Новый пользователь - показываем выбор языка
        await message.answer(
            get_text(message.from_user.id, "choose_language"),
            reply_markup=language_keyboard()
        )
    else:
        # Существующий пользователь - показываем главное меню
        is_admin = message.from_user.id == cfg.ADMIN_ID
        db.add_user(message.from_user.id, message.from_user.username)
        
        await message.answer(
            get_text(message.from_user.id, "welcome"),
            reply_markup=main_menu(message.from_user.id, is_admin)
        )

@dp.callback_query(F.data.startswith("lang_"))
async def process_language(callback: types.CallbackQuery):
    lang = callback.data.replace("lang_", "")
    
    # Добавляем пользователя с выбранным языком
    db.add_user(callback.from_user.id, callback.from_user.username, language=lang)
    
    await callback.message.delete()
    await callback.message.answer(
        get_text(callback.from_user.id, "language_set"),
        reply_markup=main_menu(callback.from_user.id, callback.from_user.id == cfg.ADMIN_ID)
    )
    await callback.answer()

# --- ПРОДАВЦЫ ---
@dp.message(F.text.in_(["🛒 Продавцы", "🛒 Sellers"]))
async def show_sellers(message: types.Message):
    text = get_text(message.from_user.id, "select_seller")
    valid_sellers = 0
    for seller_id, data in db.get_sellers().items():
        if not re.match(r'^[a-zA-Z0-9_]+$', seller_id):
            continue
        keys_left = db.get_keys_count(seller_id)
        text += f"🔹 <b>{data['name']}</b>\n"
        text += f"   {get_text(message.from_user.id, 'price')}: ${data['price']} {get_text(message.from_user.id, 'for')} {get_text(message.from_user.id, 'piece')}\n"
        text += f"   {get_text(message.from_user.id, 'keys_available')}: {keys_left}\n\n"
        valid_sellers += 1
    
    if valid_sellers == 0:
        await message.answer(get_text(message.from_user.id, "no_sellers"))
        return
    
    await message.answer(text, reply_markup=sellers_keyboard(message.from_user.id), parse_mode="HTML")

@dp.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: types.CallbackQuery):
    seller_id = callback.data.replace("buy_", "")
    
    if not re.match(r'^[a-zA-Z0-9_]+$', seller_id):
        await callback.answer(get_text(callback.from_user.id, "invalid_seller"))
        return
    
    seller = db.get_sellers().get(seller_id)
    
    if not seller:
        await callback.answer(get_text(callback.from_user.id, "seller_not_found"))
        return
    
    if db.get_keys_count(seller_id) == 0:
        await callback.answer(get_text(callback.from_user.id, "out_of_stock"))
        return
    
    max_available = min(db.get_keys_count(seller_id), 10)
    
    text = (
        f"🛒 <b>{seller['name']}</b>\n"
        f"💵 {get_text(callback.from_user.id, 'price')}: ${seller['price']} {get_text(callback.from_user.id, 'for')} {get_text(callback.from_user.id, 'piece')}\n\n"
        f"❓ {get_text(callback.from_user.id, 'how_many')}\n"
        f"📦 {get_text(callback.from_user.id, 'available')}: {max_available} {get_text(callback.from_user.id, 'pcs')}"
    )
    
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=quantity_keyboard(callback.from_user.id, seller_id, max_available), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data.startswith("qty_"))
async def process_quantity(callback: types.CallbackQuery):
    data = callback.data.replace("qty_", "")
    
    match = re.match(r'^(.+)_(\d+)$', data)
    if not match:
        await callback.answer("❌ Ошибка формата данных!")
        return
    
    seller_id = match.group(1)
    quantity = int(match.group(2))
    
    if not re.match(r'^[a-zA-Z0-9_]+$', seller_id):
        await callback.answer(get_text(callback.from_user.id, "invalid_seller"))
        return
    
    seller = db.get_sellers().get(seller_id)
    if not seller:
        await callback.answer(get_text(callback.from_user.id, "seller_not_found"))
        return
    
    total_price = seller["price"] * quantity
    
    payment_id = db.create_payment(callback.from_user.id, seller_id, total_price, quantity)
    
    text = (
        f"🛒 <b>{get_text(callback.from_user.id, 'order')}: {seller['name']}</b>\n"
        f"📦 {get_text(callback.from_user.id, 'quantity')}: {quantity} {get_text(callback.from_user.id, 'pcs')}\n"
        f"💵 {get_text(callback.from_user.id, 'total')}: <code>${total_price}</code>\n\n"
        f"📋 <b>{get_text(callback.from_user.id, 'payment_details')}</b>\n"
        f"<code>{cfg.USDT_WALLET}</code>\n\n"
        f"🆔 <b>{get_text(callback.from_user.id, 'payment_id')}:</b> <code>{payment_id}</code>\n\n"
        f"⚠️ {get_text(callback.from_user.id, 'after_payment')}"
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text(callback.from_user.id, "i_paid"), callback_data=f"paid_{payment_id}")]
    ])
    
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data.startswith("paid_"))
async def notify_payment(callback: types.CallbackQuery):
    payment_id = callback.data.replace("paid_", "")
    payment = db.get_payment(payment_id)
    
    if not payment:
        await callback.answer(get_text(callback.from_user.id, "payment_not_found"))
        return
    
    admin_text = (
        f"💰 <b>{get_text(cfg.ADMIN_ID, 'new_payment')}</b>\n\n"
        f"👤 {get_text(cfg.ADMIN_ID, 'user')}: @{callback.from_user.username or callback.from_user.id}\n"
        f"🆔 ID: <code>{callback.from_user.id}</code>\n"
        f"🛒 {get_text(cfg.ADMIN_ID, 'seller')}: {payment['seller_id']}\n"
        f"📦 {get_text(cfg.ADMIN_ID, 'quantity')}: {payment['quantity']} {get_text(cfg.ADMIN_ID, 'pcs')}\n"
        f"💵 {get_text(cfg.ADMIN_ID, 'amount')}: ${payment['amount']}\n"
        f"🆔 {get_text(cfg.ADMIN_ID, 'payment_id')}: <code>{payment_id}</code>\n\n"
        f"{get_text(cfg.ADMIN_ID, 'confirm_usage')}"
    )
    
    await bot.send_message(cfg.ADMIN_ID, admin_text, parse_mode="HTML")
    
    await callback.message.edit_text(
        callback.message.text + f"\n\n{get_text(callback.from_user.id, 'waiting_confirm')}"
    )
    await callback.answer(get_text(callback.from_user.id, "admin_notified"))

# --- ОТЗЫВЫ ---
@dp.message(F.text.in_(["⭐ Отзывы", "⭐ Reviews"]))
async def show_reviews(message: types.Message):
    reviews = db.get_reviews()
    
    if not reviews:
        await message.answer(get_text(message.from_user.id, "no_reviews"))
        return
    
    text = f"⭐ <b>{get_text(message.from_user.id, 'latest_reviews')}</b>\n\n"
    for r in reviews:
        username = r.get('username') or f"User{r['user_id']}"
        edited = f" {get_text(message.from_user.id, 'edited')}" if r.get('edited') else ""
        text += f"📝 <b>#{r['id']}</b> | 👤 <b>{username}</b>{edited}\n"
        text += f"💬 {r['text']}\n"
        text += f"📅 {r['date'][:10]}\n\n"
    
    await message.answer(text, parse_mode="HTML")

# --- ТЕХПОДДЕРЖКА ---
@dp.message(F.text.in_(["🆘 ТехПоддержка", "🆘 Support"]))
async def support_start(message: types.Message, state: FSMContext):
    await state.set_state(SupportState.waiting_message)
    await message.answer(
        f"{get_text(message.from_user.id, 'support_title')}\n\n"
        f"{get_text(message.from_user.id, 'support_desc')}",
        parse_mode="HTML"
    )

@dp.message(SupportState.waiting_message)
async def support_receive(message: types.Message, state: FSMContext):
    ticket_id = db.create_ticket(message.from_user.id, message.text)
    
    admin_text = (
        f"📩 <b>{get_text(cfg.ADMIN_ID, 'new_ticket').format(ticket_id=ticket_id)}</b>\n\n"
        f"👤 {get_text(cfg.ADMIN_ID, 'from_user')}: @{message.from_user.username or message.from_user.id}\n"
        f"🆔 User ID: <code>{message.from_user.id}</code>\n\n"
        f"💬 {get_text(cfg.ADMIN_ID, 'message')}:\n{message.text}\n\n"
        f"{get_text(cfg.ADMIN_ID, 'reply_cmd')}: /reply {ticket_id} [текст]\n"
        f"{get_text(cfg.ADMIN_ID, 'close_cmd')}: /close {ticket_id}"
    )
    await bot.send_message(cfg.ADMIN_ID, admin_text, parse_mode="HTML")
    
    await message.answer(
        get_text(message.from_user.id, "ticket_created").format(ticket_id=ticket_id)
    )
    await state.clear()

# --- НАСТРОЙКИ ---
@dp.message(F.text.in_(["⚙️ Настройки", "⚙️ Settings"]))
async def settings(message: types.Message):
    user_data = db.data["users"].get(str(message.from_user.id), {})
    purchases = len(user_data.get("purchases", []))
    
    text = (
        f"⚙️ <b>{get_text(message.from_user.id, 'settings_title')}</b>\n\n"
        f"🆔 {get_text(message.from_user.id, 'your_id')}: <code>{message.from_user.id}</code>\n"
        f"👤 {get_text(message.from_user.id, 'username')}: @{message.from_user.username or get_text(message.from_user.id, 'not_set')}\n"
        f"🛒 {get_text(message.from_user.id, 'purchases')}: {purchases}\n\n"
        f"💰 {get_text(message.from_user.id, 'wallet')}: {get_text(message.from_user.id, 'not_set')}"
    )
    await message.answer(text, parse_mode="HTML")

# === АДМИН ПАНЕЛЬ ===

@dp.message(F.text.in_(["🔐 Админ панель", "🔐 Admin Panel"]))
async def admin_panel(message: types.Message):
    if message.from_user.id != cfg.ADMIN_ID:
        return
    
    await message.answer(
        get_text(message.from_user.id, "admin_panel_title"),
        reply_markup=admin_keyboard(message.from_user.id),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "admin_panel")
async def admin_panel_callback(callback: types.CallbackQuery):
    await callback.message.edit_text(
        get_text(callback.from_user.id, "admin_panel_title"),
        reply_markup=admin_keyboard(callback.from_user.id),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    users_count = db.get_users_count()
    
    total_keys = 0
    for s in db.get_sellers():
        if re.match(r'^[a-zA-Z0-9_]+$', s):
            total_keys += db.get_keys_count(s)
    
    open_tickets = len(db.get_open_tickets())
    
    text = (
        f"📊 <b>{get_text(callback.from_user.id, 'stats')}</b>\n\n"
        f"👥 {get_text(callback.from_user.id, 'users_count')}: {users_count}\n"
        f"🔑 {get_text(callback.from_user.id, 'total_keys')}: {total_keys}\n"
        f"📩 {get_text(callback.from_user.id, 'open_tickets')}: {open_tickets}\n\n"
        f"💰 {get_text(callback.from_user.id, 'sellers')}:\n"
    )
    for sid, data in db.get_sellers().items():
        if re.match(r'^[a-zA-Z0-9_]+$', sid):
            text += f"  • {data['name']}: {db.get_keys_count(sid)} {get_text(callback.from_user.id, 'keys')} (${data['price']})\n"
    
    await callback.message.edit_text(text, reply_markup=admin_keyboard(callback.from_user.id), parse_mode="HTML")

# --- ДОБАВИТЬ ПРОДАВЦА ---
@dp.callback_query(F.data == "admin_add_seller")
async def admin_add_seller_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.add_seller_id)
    await callback.message.edit_text(
        f"➕ <b>{get_text(callback.from_user.id, 'add_seller_btn')}</b>\n\n"
        f"{get_text(callback.from_user.id, 'enter_seller_id')}",
        parse_mode="HTML"
    )

@dp.message(AdminState.add_seller_id)
async def admin_add_seller_id(message: types.Message, state: FSMContext):
    seller_id = message.text.strip().lower()
    seller_id = re.sub(r'[^a-z0-9_]', '', seller_id)
    
    if not seller_id:
        await message.answer(get_text(message.from_user.id, "id_empty"))
        return
    
    if len(seller_id) < 3:
        await message.answer(get_text(message.from_user.id, "id_short"))
        return
    
    if seller_id in db.get_sellers():
        await message.answer(get_text(message.from_user.id, "id_exists"))
        return
    
    await state.update_data(seller_id=seller_id)
    await state.set_state(AdminState.add_seller_name)
    await message.answer(f"✅ ID: <code>{seller_id}</code>\n\n{get_text(message.from_user.id, 'enter_seller_name')}", parse_mode="HTML")

@dp.message(AdminState.add_seller_name)
async def admin_add_seller_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AdminState.add_seller_price)
    await message.answer(get_text(message.from_user.id, "enter_price"))

@dp.message(AdminState.add_seller_price)
async def admin_add_seller_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text.replace(",", "."))
        if price <= 0:
            await message.answer(get_text(message.from_user.id, "invalid_price"))
            return
    except ValueError:
        await message.answer(get_text(message.from_user.id, "enter_number"))
        return
    
    data = await state.get_data()
    db.add_seller(data["seller_id"], data["name"], price)
    
    await message.answer(
        f"{get_text(message.from_user.id, 'seller_added')}\n\n"
        f"🆔 ID: <code>{data['seller_id']}</code>\n"
        f"🏷️ {get_text(message.from_user.id, 'name')}: {data['name']}\n"
        f"💵 {get_text(message.from_user.id, 'price')}: ${price}",
        reply_markup=admin_keyboard(message.from_user.id),
        parse_mode="HTML"
    )
    await state.clear()

# --- УДАЛИТЬ ПРОДАВЦА ---
@dp.callback_query(F.data == "admin_del_seller")
async def admin_del_seller_start(callback: types.CallbackQuery, state: FSMContext):
    sellers = db.get_sellers()
    valid_sellers = {k: v for k, v in sellers.items() if re.match(r'^[a-zA-Z0-9_]+$', k)}
    
    if not valid_sellers:
        await callback.answer(get_text(callback.from_user.id, "no_sellers_delete"))
        return
    
    buttons = []
    for sid, data in valid_sellers.items():
        buttons.append([InlineKeyboardButton(
            text=f"🗑️ {data['name']}", 
            callback_data=f"delsel_{sid}"
        )])
    buttons.append([InlineKeyboardButton(text=get_text(callback.from_user.id, "cancel"), callback_data="admin_panel")])
    
    await callback.message.edit_text(
        f"➖ <b>{get_text(callback.from_user.id, 'select_seller_delete')}</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("delsel_"))
async def admin_del_seller_confirm(callback: types.CallbackQuery):
    seller_id = callback.data.replace("delsel_", "")
    
    if not re.match(r'^[a-zA-Z0-9_]+$', seller_id):
        await callback.answer(get_text(callback.from_user.id, "invalid_seller"))
        return
    
    seller = db.get_sellers().get(seller_id)
    
    if not seller:
        await callback.answer(get_text(callback.from_user.id, "seller_not_found"))
        return
    
    db.remove_seller(seller_id)
    await callback.message.edit_text(
        f"{get_text(callback.from_user.id, 'seller_deleted')}\n\n<b>{seller['name']}</b>",
        reply_markup=admin_keyboard(callback.from_user.id),
        parse_mode="HTML"
    )

# --- УПРАВЛЕНИЕ ОТЗЫВАМИ ---
@dp.callback_query(F.data == "admin_reviews")
async def admin_reviews_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        f"{get_text(callback.from_user.id, 'reviews_management')}\n\n"
        f"{get_text(callback.from_user.id, 'choose_action')}:",
        reply_markup=reviews_admin_keyboard(callback.from_user.id),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "admin_add_review")
async def admin_add_review_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.add_review_user)
    await callback.message.edit_text(
        f"➕ <b>{get_text(callback.from_user.id, 'add_review')}</b>\n\n"
        f"{get_text(callback.from_user.id, 'enter_review_user')}",
        parse_mode="HTML"
    )

@dp.message(AdminState.add_review_user)
async def admin_add_review_user(message: types.Message, state: FSMContext):
    user_input = message.text.strip()
    await state.update_data(user=user_input)
    await state.set_state(AdminState.add_review_text)
    await message.answer(get_text(message.from_user.id, "enter_review_text"))

@dp.message(AdminState.add_review_text)
async def admin_add_review_text(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user = data["user"]
    
    if user.startswith("@"):
        user = user[1:]
    
    user_id = None
    for uid, udata in db.get_all_users().items():
        if udata.get("username") == user:
            user_id = int(uid)
            break
    
    if not user_id:
        try:
            user_id = int(user)
        except:
            user_id = 0
    
    review_id = db.add_review(user_id, message.text, user if not user_id else None)
    
    await message.answer(
        get_text(message.from_user.id, "review_added").format(review_id=review_id),
        reply_markup=reviews_admin_keyboard(message.from_user.id)
    )
    await state.clear()

@dp.callback_query(F.data == "admin_edit_review")
async def admin_edit_review_start(callback: types.CallbackQuery, state: FSMContext):
    reviews = db.get_reviews()
    if not reviews:
        await callback.answer(get_text(callback.from_user.id, "no_reviews_edit"))
        return
    
    buttons = []
    for r in reviews[-10:]:
        text_short = r['text'][:30] + "..." if len(r['text']) > 30 else r['text']
        username = r.get('username') or f"User{r['user_id']}"
        buttons.append([InlineKeyboardButton(
            text=f"#{r['id']} {username}: {text_short}", 
            callback_data=f"edrev_{r['id']}"
        )])
    buttons.append([InlineKeyboardButton(text=get_text(callback.from_user.id, "back"), callback_data="admin_reviews")])
    
    await callback.message.edit_text(
        f"✏️ <b>{get_text(callback.from_user.id, 'select_review_edit')}</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("edrev_"))
async def admin_edit_review_select(callback: types.CallbackQuery, state: FSMContext):
    review_id = int(callback.data.replace("edrev_", ""))
    review = db.get_review_by_id(review_id)
    
    if not review:
        await callback.answer(get_text(callback.from_user.id, "review_not_found"))
        return
    
    await state.update_data(review_id=review_id)
    await state.set_state(AdminState.edit_review_text)
    
    await callback.message.edit_text(
        f"✏️ <b>{get_text(callback.from_user.id, 'edit_review')} #{review_id}</b>\n\n"
        f"{get_text(callback.from_user.id, 'current_text')}:\n{review['text']}\n\n"
        f"{get_text(callback.from_user.id, 'enter_new_text')}:",
        parse_mode="HTML"
    )

@dp.message(AdminState.edit_review_text)
async def admin_edit_review_save(message: types.Message, state: FSMContext):
    data = await state.get_data()
    review_id = data["review_id"]
    
    if db.edit_review(review_id, message.text):
        await message.answer(
            get_text(message.from_user.id, "review_updated").format(review_id=review_id),
            reply_markup=reviews_admin_keyboard(message.from_user.id)
        )
    else:
        await message.answer(get_text(message.from_user.id, "update_error"))
    
    await state.clear()

@dp.callback_query(F.data == "admin_del_review")
async def admin_del_review_start(callback: types.CallbackQuery, state: FSMContext):
    reviews = db.get_reviews()
    if not reviews:
        await callback.answer(get_text(callback.from_user.id, "no_reviews_delete"))
        return
    
    buttons = []
    for r in reviews[-10:]:
        text_short = r['text'][:30] + "..." if len(r['text']) > 30 else r['text']
        username = r.get('username') or f"User{r['user_id']}"
        buttons.append([InlineKeyboardButton(
            text=f"🗑️ #{r['id']} {username}", 
            callback_data=f"delrev_{r['id']}"
        )])
    buttons.append([InlineKeyboardButton(text=get_text(callback.from_user.id, "back"), callback_data="admin_reviews")])
    
    await callback.message.edit_text(
        f"🗑️ <b>{get_text(callback.from_user.id, 'select_review_delete')}</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("delrev_"))
async def admin_del_review_confirm(callback: types.CallbackQuery):
    review_id = int(callback.data.replace("delrev_", ""))
    db.delete_review(review_id)
    
    await callback.message.edit_text(
        get_text(callback.from_user.id, "review_deleted").format(review_id=review_id),
        reply_markup=reviews_admin_keyboard(callback.from_user.id),
        parse_mode="HTML"
    )

# --- ГЕНЕРАЦИЯ КЛЮЧЕЙ ---
@dp.callback_query(F.data == "admin_gen_keys")
async def admin_gen_menu(callback: types.CallbackQuery, state: FSMContext):
    buttons = []
    for seller_id, data in db.get_sellers().items():
        if re.match(r'^[a-zA-Z0-9_]+$', seller_id):
            buttons.append([InlineKeyboardButton(
                text=f"🔑 {data['name']} ({db.get_keys_count(seller_id)} {get_text(callback.from_user.id, 'pcs')})", 
                callback_data=f"gen_{seller_id}"
            )])
    buttons.append([InlineKeyboardButton(text=get_text(callback.from_user.id, "back"), callback_data="admin_panel")])
    
    await callback.message.edit_text(
        get_text(callback.from_user.id, "select_seller_gen"),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("gen_"))
async def admin_gen_count(callback: types.CallbackQuery, state: FSMContext):
    seller_id = callback.data.replace("gen_", "")
    
    if not re.match(r'^[a-zA-Z0-9_]+$', seller_id):
        await callback.answer(get_text(callback.from_user.id, "invalid_seller"))
        return
    
    await state.update_data(seller_id=seller_id)
    await state.set_state(AdminState.gen_keys_count)
    
    await callback.message.edit_text(
        get_text(callback.from_user.id, "how_many_keys")
    )

@dp.message(AdminState.gen_keys_count)
async def admin_gen_execute(message: types.Message, state: FSMContext):
    try:
        count = int(message.text)
        if count < 1 or count > 100:
            await message.answer(get_text(message.from_user.id, "invalid_range"))
            return
    except ValueError:
        await message.answer(get_text(message.from_user.id, "enter_number"))
        return
    
    data = await state.get_data()
    seller_id = data["seller_id"]
    
    keys = db.generate_keys(seller_id, count)
    
    await message.answer(
        get_text(message.from_user.id, "keys_generated").format(count=count) + "\n\n" +
        f"{get_text(message.from_user.id, 'first_three')}:\n" + "\n".join(keys[:3]) + "\n...",
        reply_markup=admin_keyboard(message.from_user.id)
    )
    await state.clear()

# --- ТИКЕТЫ ---
@dp.callback_query(F.data == "admin_tickets")
async def admin_tickets(callback: types.CallbackQuery):
    tickets = db.get_open_tickets()
    
    if not tickets:
        await callback.message.edit_text(
            get_text(callback.from_user.id, "no_tickets"),
            reply_markup=admin_keyboard(callback.from_user.id)
        )
        return
    
    text = f"📩 <b>{get_text(callback.from_user.id, 'open_tickets')}</b>\n\n"
    for tid, t in tickets.items():
        username = "Unknown"
        for uid, udata in db.get_all_users().items():
            if int(uid) == t['user_id']:
                username = udata.get('username') or uid
                break
        
        text += f"#{tid} | 👤 {username}\n"
        text += f"💬 {t['message'][:50]}...\n\n"
    
    text += f"\n{get_text(callback.from_user.id, 'reply_cmd')}: /reply [ID] [текст]\n{get_text(callback.from_user.id, 'close_cmd')}: /close [ID]"
    
    await callback.message.edit_text(text, reply_markup=admin_keyboard(callback.from_user.id), parse_mode="HTML")

# --- ПОДТВЕРЖДЕНИЕ ОПЛАТЫ ---
@dp.callback_query(F.data == "admin_confirm")
async def admin_confirm_menu(callback: types.CallbackQuery):
    pending = {k: v for k, v in db.data["pending_payments"].items() if v["status"] == "pending"}
    
    if not pending:
        await callback.message.edit_text(
            get_text(callback.from_user.id, "no_pending"),
            reply_markup=admin_keyboard(callback.from_user.id)
        )
        return
    
    text = f"⏳ <b>{get_text(callback.from_user.id, 'pending_payments')}</b>\n\n"
    for pid, p in list(pending.items())[:5]:
        text += f"🆔 <code>{pid}</code>\n"
        text += f"   👤 {p['user_id']} | 📦 {p['quantity']} {get_text(callback.from_user.id, 'pcs')} | 💵 ${p['amount']}\n\n"
    
    text += get_text(callback.from_user.id, "confirm_usage")
    
    await callback.message.edit_text(text, reply_markup=admin_keyboard(callback.from_user.id), parse_mode="HTML")

@dp.message(Command("confirm"))
async def confirm_payment_cmd(message: types.Message):
    if message.from_user.id != cfg.ADMIN_ID:
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer(get_text(message.from_user.id, "confirm_usage_cmd"))
        return
    
    payment_id = args[1]
    payment = db.get_payment(payment_id)
    
    if not payment or payment["status"] == "confirmed":
        await message.answer(get_text(message.from_user.id, "already_paid"))
        return
    
    seller_id = payment["seller_id"]
    quantity = payment["quantity"]
    
    if not re.match(r'^[a-zA-Z0-9_]+$', seller_id):
        await message.answer(get_text(message.from_user.id, "invalid_seller"))
        return
    
    if db.get_keys_count(seller_id) < quantity:
        await message.answer(
            get_text(message.from_user.id, "not_enough_keys").format(need=quantity, have=db.get_keys_count(seller_id))
        )
        return
    
    keys = []
    for _ in range(quantity):
        key = db.get_key(seller_id)
        if key:
            keys.append(key)
    
    if len(keys) != quantity:
        await message.answer(get_text(message.from_user.id, "key_error"))
        return
    
    db.confirm_payment(payment_id)
    db.add_purchase(payment["user_id"], seller_id, keys, payment["amount"])
    
    keys_text = "\n".join([f"<code>{k}</code>" for k in keys])
    user_text = (
        f"✅ <b>{get_text(payment['user_id'], 'payment_confirmed')}</b>\n\n"
        f"🔑 {get_text(payment['user_id'], 'your_keys').format(count=len(keys))}:\n\n"
        f"{keys_text}\n\n"
        f"{get_text(payment['user_id'], 'save_keys')}"
    )
    
    try:
        await bot.send_message(payment["user_id"], user_text, parse_mode="HTML")
        await message.answer(
            get_text(message.from_user.id, "keys_sent").format(user_id=payment['user_id'])
        )
    except Exception as e:
        await message.answer(f"{get_text(message.from_user.id, 'error_sending')}: {e}\n\n{get_text(message.from_user.id, 'keys')}:\n" + "\n".join(keys))

@dp.message(Command("reply"))
async def reply_ticket(message: types.Message):
    if message.from_user.id != cfg.ADMIN_ID:
        return
    
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer(get_text(message.from_user.id, "reply_usage"))
        return
    
    ticket_id = int(args[1])
    text = args[2]
    
    ticket = db.get_ticket(ticket_id)
    if not ticket:
        await message.answer(get_text(message.from_user.id, "ticket_not_found"))
        return
    
    db.add_response(ticket_id, message.from_user.id, text)
    
    user_text = f"📩 <b>{get_text(ticket['user_id'], 'reply_support').format(ticket_id=ticket_id)}</b>\n\n{text}"
    try:
        await bot.send_message(ticket["user_id"], user_text, parse_mode="HTML")
        await message.answer(
            get_text(message.from_user.id, "reply_sent").format(user_id=ticket['user_id'])
        )
    except Exception as e:
        await message.answer(f"{get_text(message.from_user.id, 'error_sending')}: {e}")

@dp.message(Command("close"))
async def close_ticket(message: types.Message):
    if message.from_user.id != cfg.ADMIN_ID:
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer(get_text(message.from_user.id, "close_usage"))
        return
    
    ticket_id = int(args[1])
    db.close_ticket(ticket_id)
    await message.answer(
        get_text(message.from_user.id, "ticket_closed").format(ticket_id=ticket_id)
    )

# === НАВИГАЦИЯ ===

@dp.callback_query(F.data == "back_main")
async def back_main(callback: types.CallbackQuery):
    is_admin = callback.from_user.id == cfg.ADMIN_ID
    await callback.message.delete()
    await callback.message.answer(
        get_text(callback.from_user.id, "main_menu"),
        reply_markup=main_menu(callback.from_user.id, is_admin)
    )

@dp.callback_query(F.data == "back_sellers")
async def back_sellers(callback: types.CallbackQuery):
    await show_sellers(callback.message)

# === ЗАПУСК ===
async def main():
    # Очистка некорректных продавцов при запуске
    for seller_id in list(db.get_sellers().keys()):
        if not re.match(r'^[a-zA-Z0-9_]+$', seller_id):
            print(f"⚠️ Удален некорректный продавец: {seller_id}")
            db.remove_seller(seller_id)
    
    # Генерация ключей для валидных продавцов
    for seller_id in db.get_sellers():
        if db.get_keys_count(seller_id) == 0:
            db.generate_keys(seller_id, 20)
            print(f"Сгенерировано 20 ключей для {seller_id}")
    
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())