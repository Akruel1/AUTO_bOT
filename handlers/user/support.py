from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
from sqlalchemy import insert
from models.models import SupportMessage
from database import async_session
from config import ADMIN_IDS

router = Router()


class SupportFSM(StatesGroup):
    waiting_for_message = State()


@router.message(F.text.startswith("🆘 Поддержка") | F.text.startswith("🔧"))
async def ask_support_message(message: Message, state: FSMContext):
    await message.answer("✍️ Пожалуйста, опишите вашу проблему:")
    await state.set_state(SupportFSM.waiting_for_message)


@router.message(SupportFSM.waiting_for_message)
async def handle_support_message(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username
    support_message = message.text

    async with async_session() as session:
        new_message = SupportMessage(user_id=user_id, message=support_message)
        session.add(new_message)
        await session.commit()

    await message.answer("✅ Ваше сообщение отправлено в поддержку. Мы свяжемся с вами как можно скорее.")
    await state.clear()

    # Уведомление админам
    for admin_id in ADMIN_IDS:
        await message.bot.send_message(
            admin_id,
          f"🆘 Новое сообщение в поддержку от <code>{user_id}</code> (@{username if username else 'нет username'}):\n\n"
          f"<i>{support_message}</i>\n\n"
          f"Введите <b>/support</b> чтобы просмотреть все сообщения."

        )
