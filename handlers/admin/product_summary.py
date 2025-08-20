from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database import async_session
from models.models import Product

router = Router()


@router.callback_query(F.data == "admin_products_summary")
async def products_summary(callback: CallbackQuery):
    async with async_session() as session:
        # Загружаем товары с фото (joinedload), убираем дубли через .unique()
        result = await session.execute(
            select(Product).options(joinedload(Product.photos))
        )
        products = result.unique().scalars().all()

    if not products:
        await callback.message.edit_text("❌ В базе нет товаров.")
        return

    summary = "📊 <b>Сводка по товарам</b>\n\n"

    # Группируем товары по категориям и городам
    categories = {}
    for product in products:
        categories.setdefault(product.category, {})
        categories[product.category].setdefault(product.city, {"count": 0, "photos": 0})
        categories[product.category][product.city]["count"] += 1
        categories[product.category][product.city]["photos"] += len(product.photos)

    # Формируем текст для вывода
    for category, cities in sorted(categories.items()):
        summary += f"📦 <b>{category}</b>\n"
        for city, stats in sorted(cities.items()):
            summary += (
                f"   🏙 {city} — {stats['count']} шт. "
                f"(фото: {stats['photos']})\n"
            )
        summary += "\n"

    # Если текст длиннее лимита 4096 символов — разбиваем на части
    chunks = [summary[i:i+4000] for i in range(0, len(summary), 4000)]
    for idx, chunk in enumerate(chunks):
        if idx == 0:
            await callback.message.edit_text(chunk, parse_mode="HTML")
        else:
            await callback.message.answer(chunk, parse_mode="HTML")
