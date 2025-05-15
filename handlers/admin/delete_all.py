from sqlalchemy import delete
from aiogram import Router, F
from aiogram.types import CallbackQuery
from database import async_session
from models.models import Product, ProductPhoto

router = Router()

@router.callback_query(F.data == "admin_delete_all_products")
async def admin_delete_all_products_handler(callback: CallbackQuery):
    async with async_session() as session:
        # Удаляем все фото товаров
        await session.execute(delete(ProductPhoto))
        # Удаляем все товары
        await session.execute(delete(Product))
        await session.commit()

    await callback.answer("Все товары и их фото успешно удалены.", show_alert=True)
