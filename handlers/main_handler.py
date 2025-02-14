from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from typing import Optional
from keyboards.user_keyboards import get_profile_keyboard, main_menu_inline
from keyboards.admin_keyboards import get_admin_home_menu, get_admin_menu

from data.requests import get_user_by_telegram_id, create_user
from utils.constants import ADMIN_IDS

router = Router(name='main')

class FilterStates(StatesGroup):
    waiting_for_filter = State()
    waiting_for_field_input = State()

@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    telegram_id = str(message.from_user.id)
    
    args = message.text.split()
    referrer_id = None
    if len(args) > 1:
        try:
            referrer_id = int(args[1])
        except ValueError:
            pass

    user = await get_user_by_telegram_id(telegram_id=telegram_id)
    
    if not user:
        try:
            user = await create_user(
                telegram_id=telegram_id, 
                referral_code=message.from_user.username,
                referrer_id=referrer_id
            )
            
        except Exception as e:
            await message.answer(
                "❌ Произошла ошибка при создании вашего профиля. Попробуйте позже.",
                reply_markup=main_menu_inline()
            )
            print(f"Ошибка в start_command: {e}")
            return

    await open_home(message=message, user=message.from_user, state=state)

@router.callback_query(F.data == "go_to_home")
async def go_to_home(callback: CallbackQuery, state: FSMContext):
    """Обработчик возврата в главное меню"""
    await callback.answer()
    await open_home(callback.message, callback.from_user, state, is_callback=True)
    
@router.message(F.text.in_(["Вернуться домой 🏠"]))
async def go_to_home_reply(message: Message, state: FSMContext):
    await open_home(message, message.from_user, state)
    
@router.message(F.text == "🏠 На главную")
async def go_to_home_reply(message: Message, state: FSMContext):
    await open_home(message, message.from_user, state)

async def open_home(message: Message, user, state: FSMContext, is_callback: bool = False):
    try:
        await state.clear()
        
        db_user = await get_user_by_telegram_id(telegram_id=str(user.id))
        if not db_user:
            try:
                await create_user(telegram_id=str(user.id), )
                db_user = await get_user_by_telegram_id(telegram_id=str(user.id))
                if not db_user:
                    raise Exception("Не удалось создать пользователя")
            except Exception as e:
                error_text = "❌ Ошибка получения данных пользователя. Попробуйте перезапустить бота командой /start\nНикакие данные не будут потеряны"
                if is_callback:
                    try:
                        await message.edit_text(error_text, reply_markup=main_menu_inline())
                    except:
                        await message.answer(error_text, reply_markup=main_menu_inline())
                else:
                    await message.answer(error_text, reply_markup=main_menu_inline())
                return
        
        if user.id in ADMIN_IDS:
            await message.answer(
                "🌟 Админ панель:\n",
                reply_markup=get_admin_menu()
            )
            
        await message.answer("🏠 Главное меню", reply_markup=main_menu_inline())
            
    except Exception as e:
        print(f"Ошибка в go_to_home: {e}")
        error_text = "❌ Произошла ошибка. Попробуйте еще раз или перезапустите бота командой /start"
        if is_callback:
            try:
                await message.edit_text(error_text, reply_markup=main_menu_inline())
            except:
                await message.answer(error_text, reply_markup=main_menu_inline())
        else:
            await message.answer(error_text, reply_markup=main_menu_inline())

@router.message(F.text == "/get_id")
async def get_id(message: Message):
    """Получение ID чата и пользователя"""
    await message.answer(
        f"🆔 ID чата: {message.chat.id}\n"
        f"👤 ID пользователя: {message.from_user.id}"
    )

