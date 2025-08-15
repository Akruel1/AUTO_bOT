import json
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message
from aiogram import types
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton


from config import ADMIN_IDS
from handlers.admin.change_text import EXCHANGE_FILE
from keyboards.admin_kb import admin_main_kb
from utils.set_settings import get_setting

from database import async_session
from sqlalchemy import select
from models.models import Product

router = Router()

def main_menu_kb(user_id: int):
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📄 Профиль"), KeyboardButton(text="💰 Пополнить")],
            [KeyboardButton(text="🛒 Купить"), KeyboardButton(text="🆘 Поддержка")],
            [KeyboardButton(text="📦 Наличие товара"), KeyboardButton(text="📋 Работа")],
            [KeyboardButton(text="💱 Обменники")],
            [KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True
    )

    if user_id in ADMIN_IDS:
        keyboard.keyboard.append([KeyboardButton(text="👑 Админ")])

    return keyboard

@router.message(lambda message: message.text.startswith("👑 Админ"))
async def admin_menu(message: Message):
    user_id = message.from_user.id
    if user_id in ADMIN_IDS:
        keyboard = admin_main_kb()
        await message.answer("Вы находитесь в админ-меню:", reply_markup=keyboard)
    else:
        await message.answer("❌ У вас нет прав администратора.")

@router.message(lambda message: message.text == "🏠 Главное меню")
async def return_to_main_menu(message: Message, state: FSMContext):
    await state.clear()
    keyboard = main_menu_kb(user_id=message.from_user.id)
    await message.answer("🔙 Вы вернулись в главное меню.", reply_markup=keyboard)

@router.message(F.text == "📋 Работа")
async def send_work_text(message: Message):
    text = await get_setting("work_text")
    if text:
        await message.answer(text)
    else:
        await message.answer("❌ Текст работы пока не задан.")


import re

@router.message(F.text == "📦 Наличие товара")
async def send_stock_list(message: Message):
    bot_username = "Graff_montecristobot"

    async with async_session() as session:
        result = await session.execute(select(Product))
        products = result.scalars().all()

    if not products:
        await message.answer("❌ Товары не найдены.")
        return

    # Группируем товары по городу и району
    data = {}  # {city: {district: {product_name: {"count": int, "price": float}}}}

    for p in products:
        city = p.city
        district = p.district or "Центр"
        name = p.name

        data.setdefault(city, {})
        data[city].setdefault(district, {})
        if name not in data[city][district]:
            data[city][district][name] = {"count": 0, "price": float(p.price_usd)}
        data[city][district][name]["count"] += 1

    # Карта эмодзи
    emoji_map = {
        "lsd250mg": "🖼",
        "lsd125mg": "🖼",
        "шишки0.5г": "🌿",
        "шишки1г": "🌿",
        "ск0.5г": "💎",
        "ск1г": "💎",
    }

    def normalize_name(name: str) -> str:
        # убираем пробелы, приводим к нижнему регистру
        key = name.lower().replace(" ", "")
        # заменяем 05 на 0.5 перед "г"
        key = re.sub(r"(?<=\D)05(?=г)", "0.5", key)
        return key

    def get_emoji(name: str) -> str:
        return emoji_map.get(normalize_name(name), "❓")

    text = (
        "🔥 <b>Добро пожаловать в лучший магазин качественных товаров!</b>\n\n"
        "⚠️ - Товар заканчивается\n"
    )

    for city, districts in data.items():
        text += "\n╔═══════════════╗\n"
        text += f"🏘 <b>{city}</b>\n"
        text += "╚═══════════════╝\n"
        for district, products_dict in districts.items():
            text += f"📍 {district}\n"
            for name, info in products_dict.items():
                price = round(info["price"], 2)
                low_stock = "⚠️" if info["count"] < 10 else ""
                emoji = get_emoji(name)

                buy_link = f"<a href='https://t.me/{bot_username}?start=buy'>Купить</a>"

                parts = [f"{emoji} {name}", f"{price}$"]
                if low_stock:
                    parts.append(low_stock)
                parts.append(buy_link)

                text += "    " + " | ".join(parts) + "\n"
            text += "\n"

    text += (
        "\n<b>Лучший товар — только у нас!</b>\n\n"
        f"🤖 Наш бот: <a href='https://t.me/{bot_username}'>@{bot_username}</a>\n"
        "💬 <a href='https://t.me/+zpyv37vypShmYzEy'>Наш чат</a> | 📝 <a href='https://t.me/+tKv_tLOxfbw2N2Ri'>Наши отзывы</a>\n"
    )

    await message.answer(text.strip(), parse_mode="HTML")














def load_exchange_text() -> str:
    try:
        with open(EXCHANGE_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("text", "⚠️ Текст обменников не задан.")
    except FileNotFoundError:
        return "⚠️ Текст обменников не задан."

@router.message(F.text == "💱 Обменники")
async def show_exchange_info(message: Message):
    text = load_exchange_text()
    await message.answer(text)

# В самом низу файла
__all__ = ["main_menu_kb", "router"]


