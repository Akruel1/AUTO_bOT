import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
from database import async_session
from models.models import Product, User
from asyncio import create_task, sleep

router = Router()

class DiscountFSM(StatesGroup):
    choosing_city = State()
    choosing_category = State()
    entering_new_price = State()
    entering_duration = State()

@router.callback_query(F.data == "admin_announce_discount")
async def announce_discount(callback: CallbackQuery, state: FSMContext):
    async with async_session() as session:
        result = await session.execute(select(Product.city).distinct())
        cities = sorted(set(row[0] for row in result.fetchall() if row[0]))

    if not cities:
        await callback.message.answer("❌ Нет доступных городов.")
        return

    kb = InlineKeyboardBuilder()
    for city in cities:
        kb.button(text=city, callback_data=f"discount_city_{city}")
    kb.adjust(1)
    await callback.message.answer("🏙 Выберите город:", reply_markup=kb.as_markup())
    await state.set_state(DiscountFSM.choosing_city)

@router.callback_query(F.data.startswith("discount_city_"))
async def city_chosen(callback: CallbackQuery, state: FSMContext):
    city = callback.data.split("discount_city_")[1]
    await state.update_data(city=city)

    async with async_session() as session:
        result = await session.execute(select(Product.category).where(Product.city == city).distinct())
        categories = sorted(set(row[0] for row in result.fetchall() if row[0]))

    if not categories:
        await callback.message.answer("❌ В этом городе нет категорий товаров.")
        return

    kb = InlineKeyboardBuilder()
    for cat in categories:
        kb.button(text=cat, callback_data=f"discount_category_{cat}")
    kb.adjust(1)
    await callback.message.answer("📦 Выберите категорию:", reply_markup=kb.as_markup())
    await state.set_state(DiscountFSM.choosing_category)

@router.callback_query(F.data.startswith("discount_category_"))
async def category_chosen(callback: CallbackQuery, state: FSMContext):
    category = callback.data.split("discount_category_")[1]
    await state.update_data(category=category)
    await state.set_state(DiscountFSM.entering_new_price)
    await callback.message.answer("💸 Введите новую цену (она будет применена ко всем товарам в категории):")

@router.message(DiscountFSM.entering_new_price)
async def set_discount_price(message: Message, state: FSMContext):
    try:
        new_price = float(message.text.strip())
        if new_price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❗ Введите корректную цену.")
        return

    await state.update_data(new_price=new_price)
    await state.set_state(DiscountFSM.entering_duration)
    await message.answer("⏰ На сколько минут установить скидку?")

@router.message(DiscountFSM.entering_duration)
async def set_discount_duration(message: Message, state: FSMContext):
    try:
        duration = int(message.text.strip())
        if duration <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❗ Введите корректное количество минут.")
        return

    data = await state.get_data()
    city = data["city"]
    category = data["category"]
    new_price = data["new_price"]

    async with async_session() as session:
        result = await session.execute(
            select(Product).where(Product.city == city, Product.category == category)
        )
        products = result.scalars().all()

        if not products:
            await message.answer("❌ Не найдено товаров для применения скидки.")
            return

        old_prices = {}
        for product in products:
            old_prices[product.id] = product.price_usd
            product.price_usd = new_price

        await session.commit()

        await message.answer(
            f"✅ Скидка установлена на все товары категории «{category}» в городе «{city}» за ${new_price} на {duration} минут."
        )

        # Рассылка с логированием и задержкой
        users = (await session.execute(select(User))).scalars().all()
        text = (
            f"🎉 Акция в городе {city}!\n"
            f"Категория: {category}\n"
            f"Новая цена: ${new_price}\n"
            f"⏳ В течение: {duration} минут."
        )
        for user in users:
            try:
                await message.bot.send_message(user.tg_id, text)
                await sleep(0.05)
            except Exception as e:
                logging.error(f"Ошибка отправки сообщения пользователю {user.tg_id}: {e}")
                continue

        # Запуск задачи восстановления цен
        create_task(restore_prices_after_delay(city, category, old_prices, duration, message))

    await state.clear()

async def restore_prices_after_delay(city: str, category: str, old_prices: dict, delay_minutes: int, msg: Message):
    await sleep(delay_minutes * 60)
    async with async_session() as session:
        result = await session.execute(
            select(Product).where(Product.city == city, Product.category == category)
        )
        products = result.scalars().all()

        for product in products:
            if product.id in old_prices:
                product.price_usd = old_prices[product.id]

        await session.commit()

        await msg.bot.send_message(
            msg.chat.id,
            f"🔁 Скидка на категорию «{category}» в городе «{city}» завершена. Цены восстановлены."
        )
