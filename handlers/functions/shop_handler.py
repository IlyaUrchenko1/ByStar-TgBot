from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from utils.constants import STAR_TO_RUBLE, ADMIN_IDS
from utils.database import Database

router = Router(name='shop')
db = Database()

class ShopStates(StatesGroup):
    waiting_for_stars = State()
    waiting_for_payment = State()

PAYMENT_DETAILS = """
Реквизиты для оплаты:

РФ 🇷🇺💸 
₽ 2200700636880774
€ 2200701918386050

Armenia 🇦🇲
$ 4083060021344367
€ 4083060031125483

Kazakhstan 🇰🇿
₸ 5269880009919101
"""

@router.callback_query(F.data == "buy_stars")
async def start_buy_stars(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        await callback.message.answer("Введите количество звезд, которое хотите купить:")
        await state.set_state(ShopStates.waiting_for_stars)
    except Exception as e:
        print(f"Error in start_buy_stars: {e}")
        await callback.message.answer("Произошла ошибка. Попробуйте позже.")

@router.message(ShopStates.waiting_for_stars)
async def process_stars_amount(message: Message, state: FSMContext):
    try:
        stars = int(message.text)
        if stars <= 0:
            await message.answer("Пожалуйста, введите положительное число звезд.")
            return
            
        rubles = round(stars * STAR_TO_RUBLE, 2)
        
        await state.update_data(stars=stars, rubles=rubles)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Проверить оплату ✅", callback_data="check_payment")]
        ])
        
        await message.answer(
            f"Сумма к оплате: {rubles} RUB\n\n{PAYMENT_DETAILS}\n\n"
            f"После оплаты нажмите кнопку «Проверить оплату»",
            reply_markup=keyboard
        )
        await state.set_state(ShopStates.waiting_for_payment)
        
    except ValueError:
        await message.answer("Пожалуйста, введите корректное число звезд.")
    except Exception as e:
        print(f"Error in process_stars_amount: {e}")
        await message.answer("Произошла ошибка. Попробуйте позже.")

@router.callback_query(ShopStates.waiting_for_payment, F.data == "check_payment")
async def check_payment(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        
        data = await state.get_data()
        stars = data.get('stars')
        rubles = data.get('rubles')
        
        if not stars or not rubles:
            await callback.message.answer("Произошла ошибка. Начните покупку заново.")
            await state.clear()
            return
            
        user_id = str(callback.from_user.id)
        user = db.get_user(user_id)
        
        if not user:
            await callback.message.answer("Пользователь не найден. Пожалуйста, перезапустите бота.")
            await state.clear()
            return
            
        order_id = db.create_order(user['id'], stars, rubles, "pending")
        
        admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Принять ✅", callback_data=f"approve_payment_{order_id}"),
                InlineKeyboardButton(text="Отклонить ❌", callback_data=f"reject_payment_{order_id}")
            ],
            [InlineKeyboardButton(text="Открыть профиль 👤", url=f"tg://user?id={user_id}")]
        ])
        
        admin_message = (
            f"🔔 Новая заявка на покупку звезд!\n\n"
            f"От: {callback.from_user.mention_html()}\n"
            f"ID: {user_id}\n"
            f"Звезд: {stars}\n"
            f"Сумма: {rubles} RUB"
        )
        
        for admin_id in ADMIN_IDS:
            try:
                await callback.bot.send_message(
                    admin_id,
                    admin_message,
                    reply_markup=admin_keyboard,
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"Failed to notify admin {admin_id}: {e}")
        
        await callback.message.answer(
            "✅ Ваша заявка на покупку отправлена на проверку!\n"
            "Ожидайте подтверждения от администратора."
        )
        await state.clear()
        
    except Exception as e:
        print(f"Error in check_payment: {e}")
        await callback.message.answer("Произошла ошибка при обработке платежа. Попробуйте позже.")
        await state.clear()

@router.callback_query(F.data.startswith("approve_payment_"))
async def approve_payment(callback: CallbackQuery):
    try:
        if callback.from_user.id not in ADMIN_IDS:
            await callback.answer("У вас нет прав для этого действия!", show_alert=True)
            return
            
        order_id = int(callback.data.split("_")[2])
        order = db.get_order(order_id)
        
        if not order:
            await callback.answer("Заказ не найден!", show_alert=True)
            return
            
        if order['status'] != "pending":
            await callback.answer("Этот заказ уже обработан!", show_alert=True)
            return
        
        db.update_order_status(order_id, "completed")
        user = db.get_user(str(order['user_id']))
        
        if user:
            db.update_user_balance(str(user['telegram_id']), order['amount_star'])
            try:
                await callback.bot.send_message(
                    user['telegram_id'],
                    f"✅ Ваш заказ на {order['amount_star']} звезд подтвержден!\n"
                    f"Звезды зачислены на ваш баланс."
                )
            except Exception as e:
                print(f"Failed to notify user {user['telegram_id']}: {e}")
        
        await callback.message.edit_text(
            callback.message.text + "\n\n✅ Оплата подтверждена",
            reply_markup=None
        )
        
    except Exception as e:
        print(f"Error in approve_payment: {e}")
        await callback.answer("Произошла ошибка при подтверждении платежа", show_alert=True)

@router.callback_query(F.data.startswith("reject_payment_"))
async def reject_payment(callback: CallbackQuery):
    try:
        if callback.from_user.id not in ADMIN_IDS:
            await callback.answer("У вас нет прав для этого действия!", show_alert=True)
            return
            
        order_id = int(callback.data.split("_")[2])
        order = db.get_order(order_id)
        
        if not order:
            await callback.answer("Заказ не найден!", show_alert=True)
            return
            
        if order['status'] != "pending":
            await callback.answer("Этот заказ уже обработан!", show_alert=True)
            return
        
        db.update_order_status(order_id, "rejected")
        
        try:
            await callback.bot.send_message(
                order['user_id'],
                f"❌ Ваш заказ на {order['amount_star']} звезд отклонен.\n"
                f"Пожалуйста, проверьте правильность оплаты или обратитесь к администратору."
            )
        except Exception as e:
            print(f"Failed to notify user {order['user_id']}: {e}")
        
        await callback.message.edit_text(
            callback.message.text + "\n\n❌ Оплата отклонена",
            reply_markup=None
        )
        
    except Exception as e:
        print(f"Error in reject_payment: {e}")
        await callback.answer("Произошла ошибка при отклонении платежа", show_alert=True)
