from aiogram import Router, F
from aiogram.types import Message, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.utils.chat_action import logger
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from config import ADMIN_IDS
from database import async_session
from models.models import User
from keyboards.user_kb import main_menu_kb  # Импортируем клавиатуру пользователя

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    tg_id = message.from_user.id
    username = message.from_user.username
    display_name = f"@{username}" if username else message.from_user.first_name

    async with async_session() as session:
        try:
            result = await session.execute(select(User).where(User.tg_id == tg_id))
            user = result.scalar_one_or_none()

            if not user:
                user = User(tg_id=tg_id, username=username or "Без username")
                session.add(user)
                await session.commit()
        except SQLAlchemyError as e:
            error_msg = str(e.__dict__.get('orig', e))
            logger.error(f"Database error on start: {error_msg}")
            await message.answer(f"❌ Ошибка базы данных: {error_msg}")
            return

    keyboard = main_menu_kb(tg_id)

    await message.bot.send_chat_action(chat_id=message.chat.id, action="upload_photo")

    try:
        await message.answer_photo(
            photo="https://i.postimg.cc/qvP4nbbV/5846001388587437021.jpg",
            caption=(
                f"🏪 <b>Graff Monte Cristo</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"👋 Привет, <b>{display_name}</b>!\n"
                f"Добро пожаловать в наш магазин.\n\n"
                f"🛍 Здесь вы можете приобрести только лучшие товары по самым выгодным ценам.\n"
                f"Выберите нужный раздел ниже ⬇️"
            ),
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Ошибка при отправке фото: {e}")
        await message.answer(
            f"👋 Привет, <b>{display_name}</b>!\nДобро пожаловать в магазин.\nВыберите нужный раздел ниже ⬇️",
            reply_markup=keyboard,
            parse_mode="HTML"
        )



