from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from models.models import SupportMessage
from database import async_session

router = Router()

# Состояние для ожидания ответа от админа
class SupportAnswer(StatesGroup):
    waiting_for_answer = State()

# Храним ID сообщения, чтобы потом найти нужную заявку
admin_message_state = {}

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
            [InlineKeyboardButton(text="✏️ Ответить", callback_data=f"reply_{msg.id}")],
            [InlineKeyboardButton(text="✅ Пометить как решённое", callback_data=f"resolve_{msg.id}")]
        ])
        await message.answer(f"Сообщение от пользователя {msg.user_id}:\n{msg.message}", reply_markup=kb)

@router.callback_query(F.data.startswith("reply_"))
async def prompt_admin_for_reply(callback: CallbackQuery, state: FSMContext):
    message_id = int(callback.data.split("_")[1])
    admin_message_state[callback.from_user.id] = message_id

    await state.set_state(SupportAnswer.waiting_for_answer)
    await callback.message.answer("✉️ Напишите сообщение, которое будет отправлено пользователю.")
    await callback.answer()

@router.message(SupportAnswer.waiting_for_answer)
async def handle_admin_reply(message: Message, state: FSMContext, bot):
    admin_id = message.from_user.id
    message_id = admin_message_state.get(admin_id)

    if not message_id:
        await message.answer("⚠️ Не удалось определить, к какому сообщению относится ответ.")
        return

    async with async_session() as session:
        result = await session.execute(
            select(SupportMessage).where(SupportMessage.id == message_id)
        )
        msg = result.scalar_one_or_none()

        if not msg:
            await message.answer("⚠️ Сообщение не найдено.")
        else:
            # Отправляем ответ пользователю
            try:
                await bot.send_message(
                    msg.user_id,
                    f"📨 Ответ от поддержки:\n{message.text}"
                )
                msg.is_resolved = True
                await session.commit()
                await message.answer("✅ Ответ отправлен и сообщение помечено как решённое.")
            except Exception as e:
                await message.answer(f"⚠️ Не удалось отправить сообщение пользователю: {e}")

    await state.clear()
    admin_message_state.pop(admin_id, None)

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
                    "✅ Ваше обращение в поддержку было рассмотрено и помечено как решённое.\nСпасибо за ваше сообщение!"
                )
            except Exception as e:
                await callback.message.answer(f"⚠️ Не удалось отправить сообщение пользователю: {e}")

            await callback.message.edit_text("✅ Сообщение помечено как решённое.")
        else:
            await callback.message.edit_text("⚠️ Сообщение не найдено или уже решено.")

    await callback.answer()
