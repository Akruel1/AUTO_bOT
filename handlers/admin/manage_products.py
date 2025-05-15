from aiogram import Router, F
from aiogram.types import Message, ContentType
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from config import ADMIN_IDS
from models.models import Product, ProductPhoto
from database import async_session
from keyboards.admin_kb import admin_main_kb

router = Router()

# Состояния для FSM с добавленным состоянием category
class ProductForm(StatesGroup):
    name = State()
    description = State()
    price = State()
    category = State()
    city = State()
    photos = State()

# Проверка прав администратора
def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

@router.callback_query(F.data == "admin_manage_products")
async def add_product(callback: Message, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.message.answer("❌ У вас нет прав администратора.")
        return

    await callback.message.answer("Введите название товара:")
    await state.set_state(ProductForm.name)

@router.message(ProductForm.name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите описание товара:")
    await state.set_state(ProductForm.description)

@router.message(ProductForm.description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Введите цену товара в долларах (например, 25.99):")
    await state.set_state(ProductForm.price)

@router.message(ProductForm.price)
async def process_price(message: Message, state: FSMContext):
    try:
        price = float(message.text)
        await state.update_data(price=price)
    except ValueError:
        await message.answer("❌ Цена должна быть числом! Пожалуйста, введите правильную цену.")
        return

    await message.answer("Введите категорию товара:")
    await state.set_state(ProductForm.category)

@router.message(ProductForm.category)
async def process_category(message: Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.answer("Введите город, в котором находится товар:")
    await state.set_state(ProductForm.city)

@router.message(ProductForm.city)
async def process_city(message: Message, state: FSMContext):
    await state.update_data(city=message.text)
    await message.answer("Теперь отправьте фотографию товара (вы можете отправить несколько).")
    await state.set_state(ProductForm.photos)

@router.message(ProductForm.photos, F.content_type == ContentType.PHOTO)
async def process_photos(message: Message, state: FSMContext):
    data = await state.get_data()
    name = data['name']
    description = data['description']
    price = data['price']
    category = data['category']
    city = data['city']

    file_id = message.photo[-1].file_id

    async with async_session() as session:
        product = Product(
            name=name,
            description=description,
            price_usd=price,
            city=city,
            category=category
        )
        session.add(product)
        await session.commit()

        product_photo = ProductPhoto(file_id=file_id, product_id=product.id)
        session.add(product_photo)
        await session.commit()

    await message.answer(
        "✅ Товар успешно добавлен в базу данных! Теперь товар с фото и описанием будет доступен для пользователей."
    )
    await message.answer("Главное меню:", reply_markup=admin_main_kb())
    await state.clear()

@router.message(ProductForm.photos)
async def invalid_photo(message: Message):
    await message.answer("❌ Пожалуйста, отправьте фотографию товара.")
