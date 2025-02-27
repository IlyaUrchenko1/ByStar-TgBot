from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from keyboards.user_keyboards import main_menu_inline
from keyboards.admin_keyboards import get_admin_menu
from utils.constants import ADMIN_IDS
from utils.database import Database

router = Router(name='main')
db = Database()

class FilterStates(StatesGroup):
    waiting_for_filter = State()
    waiting_for_field_input = State()

@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    telegram_id = str(message.from_user.id)
    
    # Get referral ID from command arguments
    args = message.text.split()
    referral_id = args[1] if len(args) > 1 else None
    
    user = db.get_user(telegram_id)
    if not user:
        try:
            user = db.create_user(telegram_id, referral_id)
        except Exception as e:
            print(f"Error creating user: {e}")
            await message.answer(
                "❌ Произошла ошибка при создании профиля. Попробуйте позже.",
                reply_markup=main_menu_inline()
            )
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
    try:
        await state.clear()
        
        db_user = db.get_user(str(user.id))
        if not db_user:
            try:
                db_user = db.create_user(str(user.id))
                if not db_user:
                    raise Exception("Failed to create user")
            except Exception as e:
                error_text = "❌ Ошибка получения данных. Используйте /start для перезапуска"
                await send_message(message, error_text, is_callback)
                return

        if user.id in ADMIN_IDS:
            await message.answer(
                "🌟 Админ панель:\n",
                reply_markup=get_admin_menu()
            )
            
        await message.answer("🏠 Главное меню", reply_markup=main_menu_inline())

    except Exception as e:
        print(f"Error in open_home: {e}")
        error_text = "❌ Произошла ошибка. Используйте /start для перезапуска"
        await send_message(message, error_text, is_callback)

async def send_message(message: Message, text: str, is_callback: bool):
    if is_callback:
        try:
            await message.edit_text(text, reply_markup=main_menu_inline())
        except:
            await message.answer(text, reply_markup=main_menu_inline())
    else:
        await message.answer(text, reply_markup=main_menu_inline())

@router.message(F.text == "/get_id")
async def get_id(message: Message):
    await message.answer(
        f"🆔 ID чата: {message.chat.id}\n"
        f"👤 ID пользователя: {message.from_user.id}"
    )
