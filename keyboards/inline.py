from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from models.models import Product  # Модели City и Category больше не нужны

# Генерация клавиатуры с городами
def city_kb(cities: list) -> InlineKeyboardMarkup:
    keyboard = []
    for city in cities:
        keyboard.append([InlineKeyboardButton(
            text=city,  # Просто используем строку города
            callback_data=f"city_{city}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Генерация клавиатуры для выбора категории товаров
def category_kb(categories: list, city: str) -> InlineKeyboardMarkup:
    keyboard = []
    for cat in categories:
        keyboard.append([InlineKeyboardButton(
            text=cat,  # теперь cat — строка
            callback_data=f"cat_{city}_{cat}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)




# Генерация клавиатуры для выбора товара
def product_kb(products: list) -> InlineKeyboardMarkup:
    keyboard = []
    for product in products:
        keyboard.append([InlineKeyboardButton(
            text=f"{product.name} — ${product.price_usd:.2f}",
            callback_data=f"product_{product.id}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


# Подтверждение покупки товара
def confirm_purchase_kb(product_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Купить", callback_data=f"buy_{product_id}")
    ]])
