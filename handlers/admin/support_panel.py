from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from sqlalchemy import select, update
from models.models import SupportMessage
from database import async_session

router = Router()

@router.message(F.text == "/support")
async def show_support_messages(message: Message):
    async with async_session() as session:
        result = await session.execute(select(SupportMessage).where(SupportMessage.is_resolved == False))
        unresolved_messages = result.scalars().all()

    if not unresolved_messages:
        await message.answer("Нет новых сообщений в поддержку.")
        return

    for msg in unresolved_messages:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Решено", callback_data=f"resolve_{msg.id}")]
        ])
        await message.answer(f"Сообщение от пользователя {msg.user_id}:\n{msg.message}", reply_markup=kb)

@router.callback_query(F.data.startswith("resolve_"))
async def resolve_support_message(callback: CallbackQuery, bot):
    message_id = int(callback.data.split("_")[1])

    async with async_session() as session:
        result = await session.execute(
            select(SupportMessage).where(SupportMessage.id == message_id)
        )
        msg = result.scalar_one_or_none()

        if msg:
            msg.is_resolved = True
            await session.commit()

            # Уведомление пользователя
            try:
                await bot.send_message(
                    msg.user_id,
                    "✅ Ваше обращение в поддержку было рассмотрено и решено.\nСпасибо за ваше сообщение!"
                )
            except Exception as e:
                await callback.message.answer(f"⚠️ Не удалось отправить сообщение пользователю: {e}")

            await callback.message.edit_text("✅ Сообщение помечено как решённое.")
        else:
            await callback.message.edit_text("⚠️ Сообщение не найдено или уже решено.")

    await callback.answer()

