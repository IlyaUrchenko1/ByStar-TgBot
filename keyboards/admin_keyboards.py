from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def get_admin_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Управление пользователями", callback_data="manage_users")],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_admin_home_menu")]
    ])

def get_admin_home_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_admin_home_menu")]
    ])

