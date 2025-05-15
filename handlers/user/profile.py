from aiogram import Router, F
from aiogram.types import Message
from sqlalchemy import select
from database import async_session
from models.models import User

router = Router()

@router.message(F.text == "📄 Профиль")
async def show_profile(message: Message):
    user_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == user_id))
        user = result.scalar_one_or_none()

    if not user:
        await message.answer("Ошибка: профиль не найден.")
        return

    await message.answer(
        f"<b>👤 Профиль пользователя</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🆔 <b>ID:</b> <code>{user.tg_id}</code>\n"
        f"💼 <b>Username:</b> @{user.username or '—'}\n"
        f"💰 <b>Баланс:</b> <code>${user.balance_usd:.2f}</code>\n"
        f"🔐 <b>Статус:</b> <i>Пользователь</i>\n"
        f"━━━━━━━━━━━━━━━━━━━━"
    )

