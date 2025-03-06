from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

def main_menu_inline():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Купить звезды", callback_data="buy_stars")],
        [
            InlineKeyboardButton(text="👥 Реферальная система", callback_data="referral_system"),
            InlineKeyboardButton(text="🎁 Активировать промокод (СКОРО)", callback_data="promocode")
        ],
        [InlineKeyboardButton(text="⭐️ Отзывы клиентов", url="https://t.me/arastars1")]
    ])

def get_profile_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👥 Реферальная система", callback_data="referral_system"),
            InlineKeyboardButton(text="🗑 Удалить аккаунт", callback_data="delete_account")
        ],
        [InlineKeyboardButton(text="🏠 Главное меню", callback_data="to_home_menu")]
    ])
    

def get_help_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="❓ FAQ"),
                KeyboardButton(text="🆘 Поддержка")
            ],
            [
                KeyboardButton(text="🏠 На главную")
            ]
        ],
        resize_keyboard=True
    )
