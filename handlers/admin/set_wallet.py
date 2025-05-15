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

# Создаем класс состояний для настроек кошелька
class WalletState(StatesGroup):
    waiting_for_wallet_address = State()  # Определяем состояние для ввода кошелька

# Хэндлер для запуска настройки кошелька
@router.callback_query(F.data == "admin_set_wallet")
async def set_wallet(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("❌ У вас нет прав администратора.")
        return

    # Переходим в состояние ожидания нового кошелька
    await state.set_state(WalletState.waiting_for_wallet_address)
    await message.answer("Введите новый Litecoin-кошелек для пополнений:")

# Хэндлер для получения нового кошелька и сохранения его в базе данных
@router.message(WalletState.waiting_for_wallet_address)
async def save_wallet(message: Message, state: FSMContext):
    new_wallet_address = message.text

    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == message.from_user.id))
        user = result.scalar_one_or_none()
        if user:
            user.wallet_address = new_wallet_address
            await session.commit()

    await message.answer(f"✅ Новый кошелек для пополнений успешно установлен: {new_wallet_address}")
    await state.clear()


