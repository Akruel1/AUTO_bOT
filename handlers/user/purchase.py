from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from sqlalchemy import select

from database import async_session
from models.models import Product, ProductPhoto, User
from keyboards.inline import city_kb, category_kb, product_kb, confirm_purchase_kb

router = Router()

@router.message(F.text == "🛒 Купить")
async def buy_entry(message: Message):
    # Получаем все уникальные города из товаров
    async with async_session() as session:
        result = await session.execute(select(Product.city).distinct())
        cities = result.scalars().all()

    if not cities:
        await message.answer("Нет доступных городов.")
        return

    await message.answer("Выберите город:", reply_markup=city_kb(cities))


@router.callback_query(F.data.startswith("city_"))
async def select_city(callback: CallbackQuery):
    city = callback.data.split("_")[1]

    async with async_session() as session:
        result = await session.execute(
            select(Product.category).where(Product.city == city).distinct()
        )
        categories = result.scalars().all()

    if not categories:
        await callback.message.answer("Нет категорий товаров для этого города.")
        return

    await callback.message.edit_text("Выберите категорию:", reply_markup=category_kb(categories, city))



@router.callback_query(F.data.startswith("cat_"))
async def select_category(callback: CallbackQuery):
    _, city, category = callback.data.split("_")

    async with async_session() as session:
        # Получаем все товары для выбранного города и категории
        result = await session.execute(
            select(Product).where(Product.city == city, Product.category == category)
        )
        products = result.scalars().all()

        # Фильтруем товары, у которых есть хотя бы одно фото
        products_with_photos = []
        for product in products:
            res = await session.execute(
                select(ProductPhoto).where(ProductPhoto.product_id == product.id)
            )
            photos = res.scalars().all()
            if photos:
                products_with_photos.append(product)

    if not products_with_photos:
        await callback.message.edit_text("Нет доступных товаров в этом городе и категории.")
        return

    await callback.message.edit_text("Выберите товар:", reply_markup=product_kb(products_with_photos))



@router.callback_query(F.data.startswith("product_"))
async def confirm_purchase(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])

    async with async_session() as session:
        product = await session.get(Product, product_id)
        if not product:
            await callback.message.edit_text("❌ Товар не найден.")
            return

        text = (
            f"<b>{product.name}</b>\n"
            f"{product.description}\n\n"
            f"💵 Цена: <b>${product.price_usd:.2f}</b>"
        )
        await callback.message.edit_text(
            text,
            reply_markup=confirm_purchase_kb(product_id)
        )


@router.callback_query(F.data.startswith("buy_"))
async def make_purchase(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    user_id = callback.from_user.id

    async with async_session() as session:
        # Получаем пользователя
        result = await session.execute(select(User).where(User.tg_id == user_id))
        user = result.scalar_one_or_none()

        # Получаем товар
        product = await session.get(Product, product_id)
        if not user or not product:
            await callback.message.edit_text("❌ Ошибка. Попробуйте позже.")
            return

        # Проверяем баланс пользователя
        if user.balance_usd < float(product.price_usd):
            await callback.message.edit_text("❗ Недостаточно средств на балансе.")
            return

        # Получаем доступные фотографии товара
        result = await session.execute(
            select(ProductPhoto).where(ProductPhoto.product_id == product_id)
        )
        files = result.scalars().all()

        if not files:
            await callback.message.edit_text("❌ Нет доступных экземпляров товара.")
            return

        # Берем первое фото из списка доступных
        file_to_send = files[0]

        # Списание баланса и удаление файла
        user.balance_usd -= float(product.price_usd)
        await session.delete(file_to_send)
        await session.commit()

    # Отправка файла вне сессии, чтобы не держать сессию открытой слишком долго
    await callback.message.answer_photo(
        photo=file_to_send.file_id,
        caption=f"<b>{product.name}</b>\n\n{product.description}\n\n✅ Покупка завершена!"
    )

    # Теперь обновим клавиатуру с товарами, если надо
    async with async_session() as session:
        # Проверим, остались ли фото у этого товара
        result = await session.execute(
            select(ProductPhoto).where(ProductPhoto.product_id == product_id)
        )
        remaining_files = result.scalars().all()

        city = product.city
        category = product.category

        if not remaining_files:
            # Если фото закончились — обновим список товаров без этого товара
            result = await session.execute(
                select(Product).where(Product.city == city, Product.category == category)
            )
            products = result.scalars().all()

            # Фильтруем товары с фото
            products_with_photos = []
            for p in products:
                res = await session.execute(select(ProductPhoto).where(ProductPhoto.product_id == p.id))
                photos = res.scalars().all()
                if photos:
                    products_with_photos.append(p)

            if products_with_photos:
                if callback.message.reply_to_message:
                    await callback.message.reply_to_message.edit_text(
                        "Выберите товар:",
                        reply_markup=product_kb(products_with_photos)
                    )
                else:
                    await callback.message.answer(
                        "Выберите товар:",
                        reply_markup=product_kb(products_with_photos)
                    )
            else:
                await callback.message.answer("Нет доступных товаров в этом городе и категории.")

        # Удаляем сообщение с подтверждением покупки, оно уже не нужно
        await callback.message.delete()



