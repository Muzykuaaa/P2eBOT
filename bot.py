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

# === КЛАВИАТУРЫ ===
def main_menu(is_admin: bool = False):
    buttons = [
        [KeyboardButton(text="🛒 Продавцы")],
        [KeyboardButton(text="⭐ Отзывы"), KeyboardButton(text="🆘 ТехПоддержка")],
        [KeyboardButton(text="⚙️ Настройки")]
    ]
    if is_admin:
        buttons.append([KeyboardButton(text="🔐 Админ панель")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def sellers_keyboard():
    sellers = db.get_sellers()
    buttons = []
    for seller_id, data in sellers.items():
        # Пропускаем продавцов с некорректными ID
        if not re.match(r'^[a-zA-Z0-9_]+$', seller_id):
            continue
        btn_text = f"{data['name']} — ${data['price']}"
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"buy_{seller_id}")])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def quantity_keyboard(seller_id: str, max_qty: int = 10):
    buttons = []
    row = []
    for i in range(1, min(max_qty + 1, 11)):
        row.append(InlineKeyboardButton(text=str(i), callback_data=f"qty_{seller_id}_{i}"))
        if len(row) == 5:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_sellers")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_keyboard():
    buttons = [
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="➕ Добавить продавца", callback_data="admin_add_seller")],
        [InlineKeyboardButton(text="➖ Удалить продавца", callback_data="admin_del_seller")],
        [InlineKeyboardButton(text="📝 Управление отзывами", callback_data="admin_reviews")],
        [InlineKeyboardButton(text="📩 Тикеты поддержки", callback_data="admin_tickets")],
        [InlineKeyboardButton(text="🔑 Генерировать ключи", callback_data="admin_gen_keys")],
        [InlineKeyboardButton(text="✅ Подтвердить оплату", callback_data="admin_confirm")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def reviews_admin_keyboard():
    buttons = [
        [InlineKeyboardButton(text="➕ Добавить отзыв", callback_data="admin_add_review")],
        [InlineKeyboardButton(text="✏️ Редактировать отзыв", callback_data="admin_edit_review")],
        [InlineKeyboardButton(text="🗑️ Удалить отзыв", callback_data="admin_del_review")],
        [InlineKeyboardButton(text="🔙 Назад в админку", callback_data="admin_panel")]
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
    is_admin = message.from_user.id == cfg.ADMIN_ID
    db.add_user(message.from_user.id, message.from_user.username)
    
    welcome_text = (
        "👋 Добро пожаловать в P2E Keys Shop!\n\n"
        "🔑 Здесь вы можете купить ключи для Play-to-Earn игр\n"
        "💰 Оплата принимается в USDT (TRC20)\n\n"
        "Выберите действие:"
    )
    await message.answer(welcome_text, reply_markup=main_menu(is_admin))

# --- ПРОДАВЦЫ ---
@dp.message(F.text == "🛒 Продавцы")
async def show_sellers(message: types.Message):
    text = "🛒 Выберите продавца:\n\n"
    valid_sellers = 0
    for seller_id, data in db.get_sellers().items():
        # Пропускаем некорректные ID
        if not re.match(r'^[a-zA-Z0-9_]+$', seller_id):
            continue
        keys_left = db.get_keys_count(seller_id)
        text += f"🔹 <b>{data['name']}</b>\n"
        text += f"   💵 Цена: ${data['price']} за штуку\n"
        text += f"   📦 Ключей в наличии: {keys_left}\n\n"
        valid_sellers += 1
    
    if valid_sellers == 0:
        await message.answer("❌ Нет доступных продавцов!")
        return
    
    await message.answer(text, reply_markup=sellers_keyboard(), parse_mode="HTML")

@dp.callback_query(F.data.startswith("buy_"))
async def process_buy(callback: types.CallbackQuery):
    seller_id = callback.data.replace("buy_", "")
    
    # Проверка на валидность ID
    if not re.match(r'^[a-zA-Z0-9_]+$', seller_id):
        await callback.answer("❌ Некорректный ID продавца!")
        return
    
    seller = db.get_sellers().get(seller_id)
    
    if not seller:
        await callback.answer("❌ Продавец не найден!")
        return
    
    if db.get_keys_count(seller_id) == 0:
        await callback.answer("❌ Ключи закончились!")
        return
    
    max_available = min(db.get_keys_count(seller_id), 10)
    
    text = (
        f"🛒 <b>{seller['name']}</b>\n"
        f"💵 Цена: ${seller['price']} за штуку\n\n"
        f"❓ Сколько ключей хотите купить?\n"
        f"📦 Доступно: {max_available} шт."
    )
    
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=quantity_keyboard(seller_id, max_available), parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data.startswith("qty_"))
async def process_quantity(callback: types.CallbackQuery):
    # Формат: qty_seller_1_5
    data = callback.data.replace("qty_", "")
    
    # Находим последнее число (количество)
    match = re.match(r'^(.+)_(\d+)$', data)
    if not match:
        await callback.answer("❌ Ошибка формата данных!")
        return
    
    seller_id = match.group(1)
    quantity = int(match.group(2))
    
    # Проверка на валидность ID
    if not re.match(r'^[a-zA-Z0-9_]+$', seller_id):
        await callback.answer("❌ Некорректный ID продавца!")
        return
    
    seller = db.get_sellers().get(seller_id)
    if not seller:
        await callback.answer(f"❌ Продавец не найден!")
        return
    
    total_price = seller["price"] * quantity
    
    payment_id = db.create_payment(callback.from_user.id, seller_id, total_price, quantity)
    
    text = (
        f"🛒 <b>Заказ: {seller['name']}</b>\n"
        f"📦 Количество: {quantity} шт.\n"
        f"💵 Сумма к оплате: <code>${total_price}</code>\n\n"
        f"📋 <b>Реквизиты для оплаты USDT (TRC20):</b>\n"
        f"<code>{cfg.USDT_WALLET}</code>\n\n"
        f"🆔 <b>ID платежа:</b> <code>{payment_id}</code>\n\n"
        f"⚠️ После оплаты нажмите кнопку ниже.\n"
        f"Администратор проверит платеж и вышлет ключи."
    )
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Я оплатил", callback_data=f"paid_{payment_id}")]
    ])
    
    await callback.message.delete()
    await callback.message.answer(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()

@dp.callback_query(F.data.startswith("paid_"))
async def notify_payment(callback: types.CallbackQuery):
    payment_id = callback.data.replace("paid_", "")
    payment = db.get_payment(payment_id)
    
    if not payment:
        await callback.answer("❌ Платеж не найден!")
        return
    
    admin_text = (
        f"💰 <b>Новая оплата!</b>\n\n"
        f"👤 Пользователь: @{callback.from_user.username or callback.from_user.id}\n"
        f"🆔 ID: <code>{callback.from_user.id}</code>\n"
        f"🛒 Продавец: {payment['seller_id']}\n"
        f"📦 Количество: {payment['quantity']} шт.\n"
        f"💵 Сумма: ${payment['amount']}\n"
        f"🆔 Платеж: <code>{payment_id}</code>\n\n"
        f"Для подтверждения отправьте:\n/confirm {payment_id}"
    )
    
    await bot.send_message(cfg.ADMIN_ID, admin_text, parse_mode="HTML")
    
    await callback.message.edit_text(
        callback.message.text + "\n\n⏳ Ожидаем подтверждения администратора..."
    )
    await callback.answer("✅ Администратор уведомлен!")

# --- ОТЗЫВЫ ---
@dp.message(F.text == "⭐ Отзывы")
async def show_reviews(message: types.Message):
    reviews = db.get_reviews()
    
    if not reviews:
        await message.answer("⭐ Пока нет отзывов. Будьте первым!")
        return
    
    text = "⭐ <b>Последние отзывы:</b>\n\n"
    for r in reviews:
        username = r.get('username') or f"User{r['user_id']}"
        edited = " (изменено)" if r.get('edited') else ""
        text += f"📝 <b>#{r['id']}</b> | 👤 <b>{username}</b>{edited}\n"
        text += f"💬 {r['text']}\n"
        text += f"📅 {r['date'][:10]}\n\n"
    
    await message.answer(text, parse_mode="HTML")

# --- ТЕХПОДДЕРЖКА ---
@dp.message(F.text == "🆘 ТехПоддержка")
async def support_start(message: types.Message, state: FSMContext):
    await state.set_state(SupportState.waiting_message)
    await message.answer(
        "🆘 <b>Техническая поддержка</b>\n\n"
        "Опишите вашу проблему или вопрос одним сообщением.\n"
        "Мы ответим вам как можно скорее!",
        parse_mode="HTML"
    )

@dp.message(SupportState.waiting_message)
async def support_receive(message: types.Message, state: FSMContext):
    ticket_id = db.create_ticket(message.from_user.id, message.text)
    
    admin_text = (
        f"📩 <b>Новый тикет #{ticket_id}</b>\n\n"
        f"👤 От: @{message.from_user.username or message.from_user.id}\n"
        f"🆔 User ID: <code>{message.from_user.id}</code>\n\n"
        f"💬 Сообщение:\n{message.text}\n\n"
        f"Для ответа: /reply {ticket_id} [текст]\n"
        f"Для закрытия: /close {ticket_id}"
    )
    await bot.send_message(cfg.ADMIN_ID, admin_text, parse_mode="HTML")
    
    await message.answer(
        f"✅ Ваше обращение #{ticket_id} принято!\n"
        f"Мы ответим вам в ближайшее время."
    )
    await state.clear()

# --- НАСТРОЙКИ ---
@dp.message(F.text == "⚙️ Настройки")
async def settings(message: types.Message):
    user_data = db.data["users"].get(str(message.from_user.id), {})
    purchases = len(user_data.get("purchases", []))
    
    text = (
        f"⚙️ <b>Ваши настройки</b>\n\n"
        f"🆔 ID: <code>{message.from_user.id}</code>\n"
        f"👤 Username: @{message.from_user.username or 'Нет'}\n"
        f"🛒 Покупок: {purchases}\n\n"
        f"💰 Кошелек для выплат: Не установлен"
    )
    await message.answer(text, parse_mode="HTML")

# === АДМИН ПАНЕЛЬ ===

@dp.message(F.text == "🔐 Админ панель")
async def admin_panel(message: types.Message):
    if message.from_user.id != cfg.ADMIN_ID:
        return
    
    await message.answer(
        "🔐 <b>Административная панель</b>",
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "admin_panel")
async def admin_panel_callback(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🔐 <b>Административная панель</b>",
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "admin_stats")
async def admin_stats(callback: types.CallbackQuery):
    users_count = db.get_users_count()
    
    # Считаем только валидные ключи
    total_keys = 0
    for s in db.get_sellers():
        if re.match(r'^[a-zA-Z0-9_]+$', s):
            total_keys += db.get_keys_count(s)
    
    open_tickets = len(db.get_open_tickets())
    
    text = (
        f"📊 <b>Статистика бота</b>\n\n"
        f"👥 Пользователей: {users_count}\n"
        f"🔑 Всего ключей: {total_keys}\n"
        f"📩 Открытых тикетов: {open_tickets}\n\n"
        f"💰 Продавцы:\n"
    )
    for sid, data in db.get_sellers().items():
        if re.match(r'^[a-zA-Z0-9_]+$', sid):
            text += f"  • {data['name']}: {db.get_keys_count(sid)} ключей (${data['price']})\n"
    
    await callback.message.edit_text(text, reply_markup=admin_keyboard(), parse_mode="HTML")

# --- ДОБАВИТЬ ПРОДАВЦА ---
@dp.callback_query(F.data == "admin_add_seller")
async def admin_add_seller_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.add_seller_id)
    await callback.message.edit_text(
        "➕ <b>Добавление продавца</b>\n\n"
        "Шаг 1/3: Введите ID продавца (только латинские буквы, цифры и _)\n"
        "Например: seller_vip, super_keys, megashop",
        parse_mode="HTML"
    )

@dp.message(AdminState.add_seller_id)
async def admin_add_seller_id(message: types.Message, state: FSMContext):
    # Очищаем ID: только a-z, 0-9, _
    seller_id = message.text.strip().lower()
    seller_id = re.sub(r'[^a-z0-9_]', '', seller_id)
    
    if not seller_id:
        await message.answer("❌ ID не может быть пустым! Используйте только латинские буквы и цифры.")
        return
    
    if len(seller_id) < 3:
        await message.answer("❌ ID слишком короткий (минимум 3 символа)!")
        return
    
    if seller_id in db.get_sellers():
        await message.answer("❌ Такой ID уже существует! Введите другой:")
        return
    
    await state.update_data(seller_id=seller_id)
    await state.set_state(AdminState.add_seller_name)
    await message.answer(f"✅ ID: <code>{seller_id}</code>\n\nШаг 2/3: Введите название продавца (с эмодзи):", parse_mode="HTML")

@dp.message(AdminState.add_seller_name)
async def admin_add_seller_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AdminState.add_seller_price)
    await message.answer("Шаг 3/3: Введите цену за ключ (число, например 2.5):")

@dp.message(AdminState.add_seller_price)
async def admin_add_seller_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text.replace(",", "."))
        if price <= 0:
            await message.answer("❌ Цена должна быть больше 0!")
            return
    except ValueError:
        await message.answer("❌ Введите число! Попробуйте снова:")
        return
    
    data = await state.get_data()
    db.add_seller(data["seller_id"], data["name"], price)
    
    await message.answer(
        f"✅ Продавец добавлен!\n\n"
        f"🆔 ID: <code>{data['seller_id']}</code>\n"
        f"🏷️ Название: {data['name']}\n"
        f"💵 Цена: ${price}",
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )
    await state.clear()

# --- УДАЛИТЬ ПРОДАВЦА ---
@dp.callback_query(F.data == "admin_del_seller")
async def admin_del_seller_start(callback: types.CallbackQuery, state: FSMContext):
    sellers = db.get_sellers()
    valid_sellers = {k: v for k, v in sellers.items() if re.match(r'^[a-zA-Z0-9_]+$', k)}
    
    if not valid_sellers:
        await callback.answer("Нет продавцов для удаления!")
        return
    
    buttons = []
    for sid, data in valid_sellers.items():
        buttons.append([InlineKeyboardButton(
            text=f"🗑️ {data['name']}", 
            callback_data=f"delsel_{sid}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 Отмена", callback_data="admin_panel")])
    
    await callback.message.edit_text(
        "➖ <b>Выберите продавца для удаления:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("delsel_"))
async def admin_del_seller_confirm(callback: types.CallbackQuery):
    seller_id = callback.data.replace("delsel_", "")
    
    if not re.match(r'^[a-zA-Z0-9_]+$', seller_id):
        await callback.answer("❌ Некорректный ID!")
        return
    
    seller = db.get_sellers().get(seller_id)
    
    if not seller:
        await callback.answer("Продавец не найден!")
        return
    
    db.remove_seller(seller_id)
    await callback.message.edit_text(
        f"✅ Продавец <b>{seller['name']}</b> удален!",
        reply_markup=admin_keyboard(),
        parse_mode="HTML"
    )

# --- УПРАВЛЕНИЕ ОТЗЫВАМИ ---
@dp.callback_query(F.data == "admin_reviews")
async def admin_reviews_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📝 <b>Управление отзывами</b>\n\n"
        "Выберите действие:",
        reply_markup=reviews_admin_keyboard(),
        parse_mode="HTML"
    )

@dp.callback_query(F.data == "admin_add_review")
async def admin_add_review_start(callback: types.CallbackQuery, state: FSMContext):
    await state.set_state(AdminState.add_review_user)
    await callback.message.edit_text(
        "➕ <b>Добавление отзыва</b>\n\n"
        "Шаг 1/2: Введите ID пользователя (или @username):",
        parse_mode="HTML"
    )

@dp.message(AdminState.add_review_user)
async def admin_add_review_user(message: types.Message, state: FSMContext):
    user_input = message.text.strip()
    await state.update_data(user=user_input)
    await state.set_state(AdminState.add_review_text)
    await message.answer("Шаг 2/2: Введите текст отзыва:")

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
        f"✅ Отзыв #{review_id} добавлен!",
        reply_markup=reviews_admin_keyboard()
    )
    await state.clear()

@dp.callback_query(F.data == "admin_edit_review")
async def admin_edit_review_start(callback: types.CallbackQuery, state: FSMContext):
    reviews = db.get_reviews()
    if not reviews:
        await callback.answer("Нет отзывов для редактирования!")
        return
    
    buttons = []
    for r in reviews[-10:]:
        text_short = r['text'][:30] + "..." if len(r['text']) > 30 else r['text']
        username = r.get('username') or f"User{r['user_id']}"
        buttons.append([InlineKeyboardButton(
            text=f"#{r['id']} {username}: {text_short}", 
            callback_data=f"edrev_{r['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_reviews")])
    
    await callback.message.edit_text(
        "✏️ <b>Выберите отзыв для редактирования:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("edrev_"))
async def admin_edit_review_select(callback: types.CallbackQuery, state: FSMContext):
    review_id = int(callback.data.replace("edrev_", ""))
    review = db.get_review_by_id(review_id)
    
    if not review:
        await callback.answer("Отзыв не найден!")
        return
    
    await state.update_data(review_id=review_id)
    await state.set_state(AdminState.edit_review_text)
    
    await callback.message.edit_text(
        f"✏️ <b>Редактирование отзыва #{review_id}</b>\n\n"
        f"Текущий текст:\n{review['text']}\n\n"
        f"Введите новый текст:",
        parse_mode="HTML"
    )

@dp.message(AdminState.edit_review_text)
async def admin_edit_review_save(message: types.Message, state: FSMContext):
    data = await state.get_data()
    review_id = data["review_id"]
    
    if db.edit_review(review_id, message.text):
        await message.answer(
            f"✅ Отзыв #{review_id} обновлен!",
            reply_markup=reviews_admin_keyboard()
        )
    else:
        await message.answer("❌ Ошибка при обновлении!")
    
    await state.clear()

@dp.callback_query(F.data == "admin_del_review")
async def admin_del_review_start(callback: types.CallbackQuery, state: FSMContext):
    reviews = db.get_reviews()
    if not reviews:
        await callback.answer("Нет отзывов для удаления!")
        return
    
    buttons = []
    for r in reviews[-10:]:
        text_short = r['text'][:30] + "..." if len(r['text']) > 30 else r['text']
        username = r.get('username') or f"User{r['user_id']}"
        buttons.append([InlineKeyboardButton(
            text=f"🗑️ #{r['id']} {username}", 
            callback_data=f"delrev_{r['id']}"
        )])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_reviews")])
    
    await callback.message.edit_text(
        "🗑️ <b>Выберите отзыв для удаления:</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("delrev_"))
async def admin_del_review_confirm(callback: types.CallbackQuery):
    review_id = int(callback.data.replace("delrev_", ""))
    db.delete_review(review_id)
    
    await callback.message.edit_text(
        f"✅ Отзыв #{review_id} удален!",
        reply_markup=reviews_admin_keyboard(),
        parse_mode="HTML"
    )

# --- ГЕНЕРАЦИЯ КЛЮЧЕЙ ---
@dp.callback_query(F.data == "admin_gen_keys")
async def admin_gen_menu(callback: types.CallbackQuery, state: FSMContext):
    buttons = []
    for seller_id, data in db.get_sellers().items():
        if re.match(r'^[a-zA-Z0-9_]+$', seller_id):
            buttons.append([InlineKeyboardButton(
                text=f"🔑 {data['name']} ({db.get_keys_count(seller_id)} шт.)", 
                callback_data=f"gen_{seller_id}"
            )])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")])
    
    await callback.message.edit_text(
        "🔑 Выберите продавца для генерации ключей:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="HTML"
    )

@dp.callback_query(F.data.startswith("gen_"))
async def admin_gen_count(callback: types.CallbackQuery, state: FSMContext):
    seller_id = callback.data.replace("gen_", "")
    
    if not re.match(r'^[a-zA-Z0-9_]+$', seller_id):
        await callback.answer("❌ Некорректный ID продавца!")
        return
    
    await state.update_data(seller_id=seller_id)
    await state.set_state(AdminState.gen_keys_count)
    
    await callback.message.edit_text(
        "🔢 Сколько ключей сгенерировать? (введите число от 1 до 100):"
    )

@dp.message(AdminState.gen_keys_count)
async def admin_gen_execute(message: types.Message, state: FSMContext):
    try:
        count = int(message.text)
        if count < 1 or count > 100:
            await message.answer("❌ Введите число от 1 до 100!")
            return
    except ValueError:
        await message.answer("❌ Введите число!")
        return
    
    data = await state.get_data()
    seller_id = data["seller_id"]
    
    keys = db.generate_keys(seller_id, count)
    
    await message.answer(
        f"✅ Сгенерировано {count} ключей!\n\n"
        f"Первые 3:\n" + "\n".join(keys[:3]) + "\n...",
        reply_markup=admin_keyboard()
    )
    await state.clear()

# --- ТИКЕТЫ ---
@dp.callback_query(F.data == "admin_tickets")
async def admin_tickets(callback: types.CallbackQuery):
    tickets = db.get_open_tickets()
    
    if not tickets:
        await callback.message.edit_text(
            "📩 Нет открытых тикетов.",
            reply_markup=admin_keyboard()
        )
        return
    
    text = "📩 <b>Открытые тикеты:</b>\n\n"
    for tid, t in tickets.items():
        username = "Unknown"
        for uid, udata in db.get_all_users().items():
            if int(uid) == t['user_id']:
                username = udata.get('username') or uid
                break
        
        text += f"#{tid} | 👤 {username}\n"
        text += f"💬 {t['message'][:50]}...\n\n"
    
    text += "\nДля ответа: /reply [ID] [текст]\nДля закрытия: /close [ID]"
    
    await callback.message.edit_text(text, reply_markup=admin_keyboard(), parse_mode="HTML")

# --- ПОДТВЕРЖДЕНИЕ ОПЛАТЫ ---
@dp.callback_query(F.data == "admin_confirm")
async def admin_confirm_menu(callback: types.CallbackQuery):
    pending = {k: v for k, v in db.data["pending_payments"].items() if v["status"] == "pending"}
    
    if not pending:
        await callback.message.edit_text(
            "✅ Нет ожидающих платежей.",
            reply_markup=admin_keyboard()
        )
        return
    
    text = "⏳ <b>Ожидают подтверждения:</b>\n\n"
    for pid, p in list(pending.items())[:5]:
        text += f"🆔 <code>{pid}</code>\n"
        text += f"   👤 {p['user_id']} | 📦 {p['quantity']} шт. | 💵 ${p['amount']}\n\n"
    
    text += "Для подтверждения отправьте:\n/confirm [PAYMENT_ID]"
    
    await callback.message.edit_text(text, reply_markup=admin_keyboard(), parse_mode="HTML")

@dp.message(Command("confirm"))
async def confirm_payment_cmd(message: types.Message):
    if message.from_user.id != cfg.ADMIN_ID:
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Использование: /confirm [PAYMENT_ID]")
        return
    
    payment_id = args[1]
    payment = db.get_payment(payment_id)
    
    if not payment or payment["status"] == "confirmed":
        await message.answer("❌ Платеж не найден или уже подтвержден!")
        return
    
    seller_id = payment["seller_id"]
    quantity = payment["quantity"]
    
    if not re.match(r'^[a-zA-Z0-9_]+$', seller_id):
        await message.answer("❌ Некорректный ID продавца в платеже!")
        return
    
    if db.get_keys_count(seller_id) < quantity:
        await message.answer(f"❌ Недостаточно ключей! Нужно {quantity}, есть {db.get_keys_count(seller_id)}")
        return
    
    keys = []
    for _ in range(quantity):
        key = db.get_key(seller_id)
        if key:
            keys.append(key)
    
    if len(keys) != quantity:
        await message.answer("❌ Ошибка при выдаче ключей!")
        return
    
    db.confirm_payment(payment_id)
    db.add_purchase(payment["user_id"], seller_id, keys, payment["amount"])
    
    keys_text = "\n".join([f"<code>{k}</code>" for k in keys])
    user_text = (
        f"✅ <b>Оплата подтверждена!</b>\n\n"
        f"🔑 Ваши ключи ({len(keys)} шт.):\n\n"
        f"{keys_text}\n\n"
        f"💾 Сохраните их! Покажите это сообщение при входе в игру."
    )
    
    try:
        await bot.send_message(payment["user_id"], user_text, parse_mode="HTML")
        await message.answer(f"✅ Ключи отправлены пользователю {payment['user_id']}")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка отправки: {e}\n\nКлючи:\n" + "\n".join(keys))

@dp.message(Command("reply"))
async def reply_ticket(message: types.Message):
    if message.from_user.id != cfg.ADMIN_ID:
        return
    
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("Использование: /reply [TICKET_ID] [текст]")
        return
    
    ticket_id = int(args[1])
    text = args[2]
    
    ticket = db.get_ticket(ticket_id)
    if not ticket:
        await message.answer("Тикет не найден!")
        return
    
    db.add_response(ticket_id, message.from_user.id, text)
    
    user_text = f"📩 <b>Ответ поддержки по тикету #{ticket_id}:</b>\n\n{text}"
    try:
        await bot.send_message(ticket["user_id"], user_text, parse_mode="HTML")
        await message.answer(f"✅ Ответ отправлен пользователю {ticket['user_id']}")
    except Exception as e:
        await message.answer(f"⚠️ Ошибка: {e}")

@dp.message(Command("close"))
async def close_ticket(message: types.Message):
    if message.from_user.id != cfg.ADMIN_ID:
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Использование: /close [TICKET_ID]")
        return
    
    ticket_id = int(args[1])
    db.close_ticket(ticket_id)
    await message.answer(f"✅ Тикет #{ticket_id} закрыт")

# === НАВИГАЦИЯ ===

@dp.callback_query(F.data == "back_main")
async def back_main(callback: types.CallbackQuery):
    is_admin = callback.from_user.id == cfg.ADMIN_ID
    await callback.message.delete()
    await callback.message.answer("Главное меню:", reply_markup=main_menu(is_admin))

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