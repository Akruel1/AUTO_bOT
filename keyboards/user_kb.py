from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message
from aiogram.utils.formatting import Text

# Используем правильный фильтр

from config import ADMIN_IDS

from keyboards.admin_kb import admin_main_kb  # Импортируем клавиатуру для администратора
from utils.set_settings import get_setting

router = Router()  # Инициализация роутера

def main_menu_kb(user_id: int):
    print(f"[DEBUG] user_id={user_id}, ADMIN_IDS={ADMIN_IDS}, is_admin={user_id in ADMIN_IDS}")
    # Основное меню


    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📄 Профиль"), KeyboardButton(text="💰 Пополнить")],
            [KeyboardButton(text="🛒 Купить"), KeyboardButton(text="🆘 Поддержка")],
            [KeyboardButton(text="📦 Наличие товара"), KeyboardButton(text="📋 Работа")],
            [KeyboardButton(text="🏠 Главное меню")]
        ],
        resize_keyboard=True
    )

    # Проверка, является ли пользователь администратором
    if user_id in ADMIN_IDS:
        admin_button = KeyboardButton(text="👑 Админ")
        keyboard.keyboard.append([admin_button])  # Добавляем кнопку "Админ" в конец клавиатуры

    return keyboard


# Хэндлер для кнопки "👑 Админ"
@router.message(lambda message: message.text.startswith("👑 Админ"))  # Используем Text(contains) для фильтрации текста
async def admin_menu(message: Message):
    user_id = message.from_user.id
    if user_id in ADMIN_IDS:
        # Если пользователь администратор, показываем админ-клавиатуру
        keyboard = admin_main_kb()  # Показываем админскую клавиатуру
        await message.answer("Вы находитесь в админ-меню:", reply_markup=keyboard)
    else:
        await message.answer("❌ У вас нет прав администратора.")
@router.message(lambda message: message.text == "🏠 Главное меню")
async def return_to_main_menu(message: Message, state: FSMContext):
    await state.clear()  # Очистить состояние
    keyboard = main_menu_kb(user_id=message.from_user.id)
    await message.answer("🔙 Вы вернулись в главное меню.", reply_markup=keyboard)
@router.message(F.text == "📋 Работа")
async def send_work_text(message: Message):
    text = await get_setting("work_text")
    if text:
        await message.answer(text)
    else:
        await message.answer("❌ Текст работы пока не задан.")

@router.message(F.text == "📦 Наличие товара")
async def send_stock_text(message: Message):
    text = await get_setting("stock_text")
    if text:
        await message.answer(text)
    else:
        await message.answer("❌ Текст наличия товара пока не задан.")

# В самом низу файла
__all__ = ["main_menu_kb", "router"]
