from aiogram import Router, F
from aiogram.types import Message
from aiogram.types.input_file import URLInputFile
from sqlalchemy import select
from database import async_session
from models.models import User
from datetime import datetime

router = Router()

@router.message(F.text == "📄 Профиль")
async def show_profile(message: Message):
    user_id = message.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == user_id))
        user = result.scalar_one_or_none()

    if not user:
        await message.answer("❌ Ошибка: профиль не найден.")
        return

    # Определение статуса
    status = "👑 <b>Администратор</b>" if user.is_admin else "🧑 <i>Пользователь</i>"

    # URL изображения (замени на свою ссылку)
    photo_url = "https://i.postimg.cc/yNCdzcQc/5274151932216340705.jpg"

    # Отправка профиля с фото
    await message.answer_photo(
        photo=URLInputFile(photo_url),
        caption=(
            f"<b>🧾 ЛИЧНЫЙ КАБИНЕТ</b>\n"
            f"╭━━━━━━━━━━━━━━━━━━━━━━━╮\n"
            f"🆔 <b>ID:</b> <code>{user.tg_id}</code>\n"
            f"👤 <b>Username:</b> @{user.username or '—'}\n"
            f"💰 <b>Баланс:</b> <code>${user.balance_usd:.2f}</code>\n"
            f"🔒 <b>Статус:</b> {status}\n"
            f"🗓 <b>Дата:</b> <code>{datetime.now().strftime('%d.%m.%Y')}</code>\n"
            f"🕒 <b>Время:</b> <code>{datetime.now().strftime('%H:%M')}</code>\n"
            f"╰━━━━━━━━━━━━━━━━━━━━━━━╯\n\n"
            f"<i>💬 Используйте кнопки ниже для управления — пополнение, покупка, связь.</i>\n"
            f"<b>🔗 MonteCristoBot всегда рядом — @MonteCristoGraff_bot</b>"
        ),
        parse_mode="HTML"
    )
