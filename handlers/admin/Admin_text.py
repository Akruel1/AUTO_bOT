from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from utils.set_settings import set_setting 

router = Router()

class AdminTextFSM(StatesGroup):
    waiting_for_work_text = State()
    waiting_for_stock_text = State()


@router.callback_query(F.data == "admin_set_work_text")
async def prompt_set_work_text(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("✍️ Введите текст для кнопки <b>📋 Работа</b>:")
    await state.set_state(AdminTextFSM.waiting_for_work_text)
    await callback.answer()


@router.callback_query(F.data == "admin_set_stock_text")
async def prompt_set_stock_text(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("✍️ Введите текст для кнопки <b>📦 Наличие товара</b>:")
    await state.set_state(AdminTextFSM.waiting_for_stock_text)
    await callback.answer()


@router.message(AdminTextFSM.waiting_for_work_text)
async def set_work_text(message: Message, state: FSMContext):
    await set_setting("work_text", message.text)
    await message.answer("✅ Текст для '📋 Работа' успешно сохранён.")
    await state.clear()


@router.message(AdminTextFSM.waiting_for_stock_text)
async def set_stock_text(message: Message, state: FSMContext):
    await set_setting("stock_text", message.text)
    await message.answer("✅ Текст для '📦 Наличие товара' успешно сохранён.")
    await state.clear()
