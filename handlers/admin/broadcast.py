from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup  # Импортируем StatesGroup
from aiogram.filters import Command
from sqlalchemy import select

from database import async_session
from models.models import User
from config import ADMIN_IDS

router = Router()

# Создаем класс состояний, который наследуется от StatesGroup
class BroadcastState(StatesGroup):
    waiting_for_text = State()  # Определяем состояние

# Хэндлер для запуска рассылки
@router.callback_query(F.data == "admin_broadcast")
async def broadcast_message(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав администратора.")
        return

    # Переходим в состояние ожидания текста для рассылки
    await state.set_state(BroadcastState.waiting_for_text)
    await message.answer("Введите текст для рассылки всем пользователям:")

# Хэндлер для получения текста рассылки
@router.message(BroadcastState.waiting_for_text)
async def send_broadcast(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав администратора.")
        return

    # Получаем текст для рассылки
    broadcast_text = message.text

    # Получаем всех пользователей из базы данных
    async with async_session() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()

    # Отправляем сообщение каждому пользователю
    for user in users:
        try:
            await message.bot.send_message(user.tg_id, broadcast_text)
        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю {user.tg_id}: {e}")

    await message.answer("✅ Сообщение успешно разослано всем пользователям!")

    # После выполнения рассылки, сбрасываем состояние
    await state.clear()  # вместо await state.finish()

