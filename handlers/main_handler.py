from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, FSInputFile
from keyboards.user_keyboards import main_menu_inline, get_help_menu
from keyboards.admin_keyboards import get_admin_menu
from utils.constants import ADMIN_IDS
from utils.database import Database

router = Router(name='main')
db = Database()

@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    telegram_id = str(message.from_user.id)
    referral_id = message.text.split()[1] if len(message.text.split()) > 1 else None
    
    user = db.get_user(telegram_id) or db.create_user(telegram_id, referral_id)
    if not user:
        await message.answer("❌ Ошибка при создании профиля", reply_markup=main_menu_inline())
        return

    await open_home(message, message.from_user, state)

@router.callback_query(F.data == "go_to_home")
async def go_to_home(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await open_home(callback.message, callback.from_user, state, is_callback=True)

@router.message(F.text.in_(["Вернуться домой 🏠", "🏠 На главную"]))
async def go_to_home_reply(message: Message, state: FSMContext):
    await open_home(message, message.from_user, state)

async def open_home(message: Message, user, state: FSMContext, is_callback: bool = False):
    await state.clear()
    
    db_user = db.get_user(str(user.id)) or db.create_user(str(user.id))
    if not db_user:
        await message.answer("❌ Ошибка получения данных. Используйте /start")
        return

    if user.id in ADMIN_IDS:
        await message.answer("Админ панель:", reply_markup=get_admin_menu())
        
    await message.answer("🔄 Загрузка данных...", reply_markup=get_help_menu())
    try:
        await message.answer_photo(
            FSInputFile("./images/logo_for_start.jpg"), 
            caption="🏠 Главное меню", 
            reply_markup=main_menu_inline()
        )
    except FileNotFoundError:
        await message.answer(
            "🏠 Главное меню",
            reply_markup=main_menu_inline()
        )

@router.message(F.text == "/get_id")
async def get_id(message: Message):
    await message.answer(
        f"🆔 ID чата: {message.chat.id}\n"
        f"👤 ID пользователя: {message.from_user.id}"
    )
