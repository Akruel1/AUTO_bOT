from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select, delete
from sqlalchemy.orm import joinedload

from database import async_session
from models.models import Product

router = Router()


@router.callback_query(F.data == "admin_delete_products_no_photos")
async def delete_products_no_photos(callback: CallbackQuery):
    confirm_text = "🗑 Удаляем все товары без фотографий..."
    await callback.message.edit_text(confirm_text)

    async with async_session() as session:
        # Получаем все товары с их фото
        result = await session.execute(
            select(Product).options(joinedload(Product.photos))
        )
        products = result.unique().scalars().all()

        # Находим товары без фото
        products_to_delete = [p for p in products if len(p.photos) == 0]

        if not products_to_delete:
            await callback.message.edit_text("✅ Все товары имеют хотя бы одно фото. Нечего удалять.")
            return

        # Удаляем товары без фото
        for product in products_to_delete:
            await session.delete(product)
        await session.commit()

        await callback.message.edit_text(f"✅ Удалено {len(products_to_delete)} товаров без фотографий.")
