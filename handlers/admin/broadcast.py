from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from database import async_session
from models.models import User
from config import ADMIN_IDS

router = Router()

# Состояния
class BroadcastState(StatesGroup):
    waiting_for_text = State()

# Конфиг ссылок
OPERATOR_USERNAME = "The_Graff_Monte_Cristo"
BOT_USERNAME = "Graff_montecristobot"
CHAT_LINK = "https://t.me/+zpyv37vypShmYzEy"
REVIEWS_LINK = "https://t.me/+tKv_tLOxfbw2N2Ri"

# Запуск рассылки
@router.callback_query(F.data == "admin_broadcast")
async def broadcast_message(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    await state.set_state(BroadcastState.waiting_for_text)
    await callback.message.answer("Введите текст для рассылки всем пользователям (HTML поддерживается):")
    await callback.answer()

# Приём текста и отправка рассылки
@router.message(BroadcastState.waiting_for_text)
async def send_broadcast(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав администратора.")
        return

    broadcast_text = message.text  # Берём как есть, не трогаем HTML

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Написать оператору", url=f"https://t.me/{OPERATOR_USERNAME}")],
        [InlineKeyboardButton(text="🤖 Перейти в бота", url=f"https://t.me/{BOT_USERNAME}")],
        [InlineKeyboardButton(text="💭 Наш чат", url=CHAT_LINK)],
        [InlineKeyboardButton(text="⭐ Наши отзывы", url=REVIEWS_LINK)]
    ])

    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

    sent_count = 0
    for user in users:
        try:
            await message.bot.send_message(
                chat_id=user.tg_id,
                text=broadcast_text,
                parse_mode="HTML",  # Включаем HTML-парсинг
                reply_markup=kb
            )
            sent_count += 1
        except Exception as e:
            print(f"Не удалось отправить {user.tg_id}: {e}")

    await message.answer(f"✅ Сообщение отправлено {sent_count} пользователям.")
    await state.clear()

