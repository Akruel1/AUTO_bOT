import asyncio 
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

from config import BOT_TOKEN
from database import init_db

# user handlers
from handlers.user import start, profile, purchase, topup, support

# admin handlers
from handlers.admin import (
    broadcast,
    set_wallet,
    support_panel,
    manage_products,
    topup_admin,
    delete_all,
    admin_announce_discount,
    Admin_text,
    change_text,
    product_summary,     # сводка по товарам
    delete_products      # удаление товаров без фото
)

from utils.topup_checker import check_topups

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    # Инициализация базы данных
    await init_db()

    # Инициализация бота
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
    dp = Dispatcher(storage=MemoryStorage())

    # Регистрируем хендлеры пользователя
    dp.include_routers(
        start.router,
        profile.router,
        purchase.router,
        topup.router,
        support.router,
    )

    # Регистрируем хендлеры админа
    dp.include_routers(
        broadcast.router,
        set_wallet.router,
        support_panel.router,
        manage_products.router,
        topup_admin.router,
        delete_all.router,
        Admin_text.router,
        change_text.router,
        admin_announce_discount.router,
        product_summary.router,   # сводка по товарам
        delete_products.router    # удаление товаров без фото
    )

    # Регистрируем пользовательскую клавиатуру
    from keyboards.user_kb import router as user_kb_router
    dp.include_router(user_kb_router)

    # Запуск проверки пополнений
    asyncio.create_task(check_topups())

    logger.info("Bot is running...")
    await dp.start_polling(bot)


if __name__ == "__main__": 
    asyncio.run(main())
