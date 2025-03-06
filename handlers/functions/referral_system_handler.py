from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from utils.database import Database
from utils.constants import BOT_USERNAME

router = Router(name='referral')
db = Database()

@router.callback_query(F.data == "referral_system")
async def show_referral_system(callback: CallbackQuery):
    try:
        telegram_id = str(callback.from_user.id)
        user = db.get_user(telegram_id)
        
        if not user:
            await callback.message.answer("❌ Ошибка получения данных пользователя")
            return

        referral_link = f"t.me/{BOT_USERNAME}?start={telegram_id}"
        
        share_text = (
            f"\n\n ⬆️ Оригинальная ссылка на бота ⬆️ \n🌟 Присоединяйтесь к нашему боту по дешевой покупки звезд!\n\n"
            "• Без KYC\n"
            "• Дешевле чем в других ботах и официальном магазине\n\n" 
            "⬇️ Ваша реферальная ссылка с бонусами ⬇️\n\n"
            f"{referral_link}"
        )
        
        referral_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Поделиться ссылкой", switch_inline_query=share_text)],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data="go_to_home")]
        ])

        referral_count = db.amount_refferal_by_tg_id(telegram_id)
        
        await callback.message.answer(
            "👥 Реферальная система\n\n"
            "🔥 Приглашайте друзей и получайте бонусы!\n\n"
            "💎 Условия программы:\n"
            "- За каждого приглашенного друга вы получите бонусы\n"
            "- Скоро будет доступна монетизация рефералов\n"
            "- Следите за обновлениями системы\n\n"
            f"🔗 Ваша реферальная ссылка:\n{referral_link}\n\n"
            f"📊 Количество ваших рефералов: {referral_count if referral_count else 0}\n\n"
            "⚡️ Скоро здесь появятся новые крутые возможности заработка!",
            reply_markup=referral_keyboard
        )
        
        await callback.answer()

    except Exception as e:
        print(f"Error in show_referral_system: {e}")
        await callback.message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

