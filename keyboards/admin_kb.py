from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_main_kb():
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="admin_top_up_requests"),
                InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast"),
            ],
            [
                InlineKeyboardButton(text="🛠 Товары", callback_data="admin_manage_products"),
                InlineKeyboardButton(text="🪙 Кошелек", callback_data="admin_set_wallet"),
            ],
            [
                InlineKeyboardButton(text="🗑 Все товары", callback_data="admin_delete_all_products"),
                InlineKeyboardButton(text="🗑 Без фото", callback_data="admin_delete_products_no_photos"),
            ],
            [
                InlineKeyboardButton(text="🛠 Текст работы", callback_data="admin_set_work_text"),
                InlineKeyboardButton(text="📦 Текст наличия", callback_data="admin_set_stock_text"),
            ],
            [
                InlineKeyboardButton(text="📝 Текст обменников", callback_data="admin_set_exchange_text"),
            ],
            [
                InlineKeyboardButton(text="📉 Скидка", callback_data="admin_announce_discount"),
                InlineKeyboardButton(text="📊 Сводка", callback_data="admin_products_summary"),
            ]
        ]
    )
    return keyboard
