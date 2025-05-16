import json
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

router = Router()

EXCHANGE_FILE = "exchange_text.json"

# Состояние FSM
class AdminSetExchangeText(StatesGroup):
    waiting_for_text = State()

# Функция для сохранения текста
def save_exchange_text(text: str):
    with open(EXCHANGE_FILE, "w", encoding="utf-8") as f:
        json.dump({"text": text}, f, ensure_ascii=False, indent=2)

# Хэндлер — нажатие админом кнопки "📝 Установить текст обменников"
@router.callback_query(F.data == "admin_set_exchange_text")
async def admin_set_exchange_text(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("✏️ Введите новый текст для раздела 'Обменники':")
    await state.set_state(AdminSetExchangeText.waiting_for_text)
    await callback.answer()

# Хэндлер — приём текста от админа
@router.message(AdminSetExchangeText.waiting_for_text)
async def admin_save_exchange_text(message: Message, state: FSMContext):
    text = message.text
    save_exchange_text(text)
    await message.answer("✅ Текст обменников успешно обновлён.")
    await state.clear()
