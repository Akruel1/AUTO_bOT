from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def admin_main_kb():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="admin_top_up_requests"),
                InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast"),
            ],
            [
                InlineKeyboardButton(text="🛠 Управление товарами", callback_data="admin_manage_products"),
                InlineKeyboardButton(text="🪙 Настройка кошелька", callback_data="admin_set_wallet"),
            ],
            [
                InlineKeyboardButton(text="🗑 Удалить все товары", callback_data="admin_delete_all_products"),
            ],
            [
                InlineKeyboardButton(text="🛠 Установить текст работы", callback_data="admin_set_work_text"),
                InlineKeyboardButton(text="📦 Установить текст наличия товара", callback_data="admin_set_stock_text"),
            ],
            [
                InlineKeyboardButton(text="📝 Установить текст обменников", callback_data="admin_set_exchange_text"),  # ← Новая кнопка
            ]
        ]
    )
    return keyboard
