from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
import aiohttp
from keyboards.user_kb import main_menu_kb
from config import LTC_API_URL, LTC_WALLET, ADMIN_IDS
from database import async_session
from models.models import TopUpRequest, User

router = Router()

# FSM для пополнения
class TopUpFSM(StatesGroup):
    waiting_for_amount = State()


def cancel_kb():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="Отменить")]],
        resize_keyboard=True
    )

@router.message(F.text == "💰 Пополнить")
async def topup_start(message: Message, state: FSMContext):
    await message.answer(
        "Введите сумму пополнения в <b>USD</b>:", 
        reply_markup=cancel_kb()
    )
    await state.set_state(TopUpFSM.waiting_for_amount)

@router.message(TopUpFSM.waiting_for_amount, F.text.lower() == "отменить")
async def cancel_topup(message: Message, state: FSMContext):
    await state.clear()
    tg_id = message.from_user.id
    await message.answer("❌ Пополнение отменено.", reply_markup=main_menu_kb(tg_id))

@router.message(TopUpFSM.waiting_for_amount)
async def topup_amount_entered(message: Message, state: FSMContext):
    try:
        amount_usd = float(message.text)
        if amount_usd < 1:
            raise ValueError
    except ValueError:
        await message.answer("❗ Введите корректную сумму (минимум 1 USD). Или напишите 'Отменить' для выхода.")
        return

    # Получаем курс LTC/USD с CoinGecko
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.coingecko.com/api/v3/simple/price?ids=litecoin&vs_currencies=usd") as resp:
            if resp.status != 200:
                await message.answer("⚠️ Не удалось получить курс LTC. Попробуйте позже.")
                return
            data = await resp.json()
            ltc_usd = data.get("litecoin", {}).get("usd")
            if ltc_usd is None:
                await message.answer("⚠️ Курс LTC временно недоступен.")
                return

    amount_ltc = round(amount_usd / ltc_usd, 8)

    # Получаем кошелек из базы данных (предположим, что кошелек хранится у админа с id = ADMIN_IDS[0])
    async with async_session() as session:
        admin_tg_id = ADMIN_IDS[0]
        result = await session.execute(select(User).where(User.tg_id == admin_tg_id))
        admin_user = result.scalar_one_or_none()
        if not admin_user or not admin_user.wallet_address:
            await message.answer("⚠️ Кошелек для пополнения не установлен. Обратитесь к администратору.")
            return

        # Сохраняем заявку в БД
        result = await session.execute(select(User).where(User.tg_id == message.from_user.id))
        user = result.scalar_one_or_none()

        request = TopUpRequest(
            user_id=user.id,
            amount_usd=amount_usd,
            expected_ltc=amount_ltc
        )
        session.add(request)
        await session.commit()

    tg_id = message.from_user.id
    await message.answer(
        f"✅ Для пополнения на <b>${amount_usd:.2f}</b>\n"
        f"вам нужно перевести <b>{amount_ltc:.8f} LTC</b>\n\n"
        f"🪙 На адрес:\n<code>{admin_user.wallet_address}</code>\n\n"
         f"⚠️ Заявка будет проверяться в течение часа. "
        f"После подтверждения баланс пополнится автоматически.",
        reply_markup=main_menu_kb(tg_id)
    )

    await state.clear()
