from aiogram import F, Router
from aiogram.client import bot
from aiogram.filters.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from database import async_session
from models.models import User

router = Router()

class TopUpBalance(StatesGroup):
    waiting_for_user_id = State()
    waiting_for_amount = State()

@router.callback_query(F.data == "admin_top_up_requests")
async def admin_start_topup(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите ID пользователя, которому хотите пополнить баланс:")
    await state.set_state(TopUpBalance.waiting_for_user_id)
    await callback.answer()

from sqlalchemy.future import select

@router.message(TopUpBalance.waiting_for_user_id)
async def process_user_id(message: Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("ID должен быть числом. Попробуйте снова:")
        return
    user_id = int(message.text)
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == user_id))
        user = result.scalars().first()
        if not user:
            await message.answer("Пользователь с таким ID не найден. Введите корректный ID:")
            return

    await state.update_data(user_id=user_id)
    await message.answer("Введите сумму для пополнения баланса (в USD):")
    await state.set_state(TopUpBalance.waiting_for_amount)

from aiogram import Bot
from aiogram.types import Message

@router.message(TopUpBalance.waiting_for_amount)
async def process_amount(message: Message, state: FSMContext, bot: Bot):
    try:
        amount = float(message.text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Введите корректное положительное число для суммы:")
        return

    data = await state.get_data()
    user_id = data.get("user_id")

    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == user_id))
        user = result.scalars().first()
        if not user:
            await message.answer("Пользователь не найден при пополнении, операция отменена.")
            await state.clear()
            return

        user.balance_usd += amount
        session.add(user)
        await session.commit()

    await message.answer(f"Баланс пользователя с ID {user_id} успешно пополнен на ${amount:.2f}.")

    try:
        await bot.send_message(user_id, f"💵 Ваш баланс был пополнен на <b>${amount:.2f}</b> администратором.")
    except Exception as e:
        await message.answer(f"⚠️ Не удалось отправить сообщение пользователю. Ошибка: {e}")

    await state.clear()


