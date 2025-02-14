from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_inline():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Личный профиль", callback_data="profile")],
        [InlineKeyboardButton(text="🆘 Техподдержка", callback_data="support")],
        [InlineKeyboardButton(text="✅ Наши гарантии", callback_data="guarantees")],
        [InlineKeyboardButton(text="⭐️ Отзывы клиентов", callback_data="reviews")],
        [InlineKeyboardButton(text="💰 Купить звезды", callback_data="buy_stars")],
    ])

def get_profile_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Реферальная система", callback_data="referral_system")],
        [InlineKeyboardButton(text="🗑 Удалить аккаунт", callback_data="delete_account")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
    ])
