from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

router = Router(name='faq')

@router.message(F.text == "❓ FAQ")
async def show_faq(message: Message):
    try:
        faq_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📋 Правила", url="https://telegra.ph/Publichnaya-oferta-na-okazanie-uslugi-po-pokupke-Telegram-Stars-02-27-2"),
                InlineKeyboardButton(text="📢 Новости", url="t.me/AraStarsCommunity"),
                InlineKeyboardButton(text="💬 Отзывы", url="t.me/arastars1")
            ],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="go_to_home")]
        ])
        
        await message.answer(
            text="ℹ️ Выберите интересующий вас раздел:",
            reply_markup=faq_keyboard
        )
        
    except Exception as e:
        print(f"Error in show_faq: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")


