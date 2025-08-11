from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from sqlalchemy import select
import random

from database import async_session
from models.models import Product, ProductPhoto, User
from keyboards.inline import confirm_purchase_kb

router = Router()


def city_kb(cities: list[str]) -> InlineKeyboardMarkup:
    buttons = []
    row = []
    for i, city in enumerate(cities, start=1):
        row.append(InlineKeyboardButton(text=city, callback_data=f"city_{city}"))
        if i % 2 == 0:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def district_kb(city: str) -> InlineKeyboardMarkup | None:
    async with async_session() as session:
        result = await session.execute(
            select(Product.district).where(Product.city == city).distinct()
        )
        districts = result.scalars().all()

    if not districts:
        return None

    buttons = []
    row = []
    for i, district in enumerate(districts, start=1):
        row.append(InlineKeyboardButton(text=district, callback_data=f"district_{city}_{district}"))
        if i % 2 == 0:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def category_kb(categories: list[str], city: str, district: str) -> InlineKeyboardMarkup | None:
    if not categories:
        return None

    buttons = []
    row = []
    for i, category in enumerate(categories, start=1):
        row.append(InlineKeyboardButton(text=category, callback_data=f"cat_{city}_{district}_{category}"))
        if i % 2 == 0:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(F.text == "🛒 Купить")
async def buy_entry(message: Message):
    async with async_session() as session:
        result = await session.execute(select(Product.city).distinct())
        cities = result.scalars().all()

    if not cities:
        await message.answer("Нет доступных городов.")
        return

    await message.answer("Выберите город:", reply_markup=city_kb(cities))


@router.callback_query(F.data.startswith("city_"))
async def select_city(callback: CallbackQuery):
    city = callback.data.split("_", 1)[1]

    kb = await district_kb(city)
    if kb is None:
        async with async_session() as session:
            result = await session.execute(
                select(Product.category).where(Product.city == city).distinct()
            )
            categories = result.scalars().all()

        if not categories:
            await callback.message.answer("Нет категорий товаров для этого города.")
            return

        kb_cat = category_kb(categories, city, district="")
        await callback.message.edit_text("Выберите категорию:", reply_markup=kb_cat)
    else:
        await callback.message.edit_text(f"Выберите район в городе {city}:", reply_markup=kb)


@router.callback_query(F.data.startswith("district_"))
async def select_district(callback: CallbackQuery):
    _, city, district = callback.data.split("_", 2)

    async with async_session() as session:
        result = await session.execute(
            select(Product.category).where(Product.city == city, Product.district == district).distinct()
        )
        categories = result.scalars().all()

    if not categories:
        await callback.message.answer("Нет категорий товаров для этого города и района.")
        return

    kb_cat = category_kb(categories, city, district)
    await callback.message.edit_text(
        f"Выберите категорию для города {city} и района {district}:",
        reply_markup=kb_cat
    )


@router.callback_query(F.data.startswith("cat_"))
async def select_category(callback: CallbackQuery):
    _, city, district, category = callback.data.split("_", 3)

    async with async_session() as session:
        result = await session.execute(
            select(Product).where(Product.city == city, Product.district == district, Product.category == category)
        )
        products = result.scalars().all()

        products_with_photos = []
        for product in products:
            res = await session.execute(
                select(ProductPhoto).where(ProductPhoto.product_id == product.id)
            )
            photos = res.scalars().all()
            if photos:
                products_with_photos.append((product, photos))

    if not products_with_photos:
        await callback.message.edit_text("Нет доступных товаров в этом городе, районе и категории.")
        return

    product, photos = random.choice(products_with_photos)
    text = (
        f"<b>{product.name}</b>\n"
        f"{product.description}\n\n"
        f"💵 Цена: <b>${product.price_usd:.2f}</b>"
    )
    await callback.message.edit_text(
        text=text,
        reply_markup=confirm_purchase_kb(product.id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("buy_"))
async def make_purchase(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == user_id))
        user = result.scalar_one_or_none()
        product = await session.get(Product, product_id)

        if not user or not product:
            await callback.message.edit_text("❌ Ошибка. Попробуйте позже.")
            return

        if user.balance_usd < float(product.price_usd):
            await callback.message.edit_text("❗ Недостаточно средств на балансе.")
            return

        result = await session.execute(
            select(ProductPhoto).where(ProductPhoto.product_id == product_id)
        )
        files = result.scalars().all()

        if not files:
            await callback.message.edit_text("❌ Нет доступных экземпляров товара.")
            return

        file_to_send = files[0]
        user.balance_usd -= float(product.price_usd)
        await session.delete(file_to_send)
        await session.commit()

    await callback.message.answer_photo(
        photo=file_to_send.file_id,
        caption=f"<b>{product.name}</b>\n\n{product.description}\n\n✅ Покупка завершена!",
        parse_mode="HTML"
    )
    await callback.message.delete()
