from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from utils.constants import STAR_TO_RUBLE, ADMIN_IDS, ALLOWED_TO_ADMIN_PANEL_IDS
from utils.database import Database
import os
import hmac
import json
import hashlib
import requests
import uuid
from datetime import datetime

router = Router(name='shop')
db = Database()

class ShopStates(StatesGroup):
    waiting_for_recipient = State()
    waiting_for_username = State()
    waiting_for_stars = State()
    waiting_for_payment = State()

PAYMENT_DETAILS = """
💳 Реквизиты для оплаты:        

🇷🇺 Россия (RUB)
₽ 2200700636880774
€ 2200701918386050

🇰🇿 Казахстан (KZT)
₸ 5269880009919101
"""

@router.callback_query(F.data == "buy_stars")
async def start_buy_stars(callback: CallbackQuery, state: FSMContext):
    try:
        # if not callback.from_user.id in ADMIN_IDS:
        #     await callback.answer("Пока-что в разработке!", show_alert=True)
        #     return
        
        await callback.answer()
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Себе", callback_data="buy_for_self")],
            [InlineKeyboardButton(text="Другу", callback_data="buy_for_friend")]
        ])
        
        await callback.message.answer("✨ Кому вы хотите купить звезды?", reply_markup=keyboard)
        await state.set_state(ShopStates.waiting_for_recipient)
    except Exception as e:
        print(f"Error in start_buy_stars: {e}")
        await callback.message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@router.callback_query(ShopStates.waiting_for_recipient, F.data == "buy_for_self")
async def buy_for_self(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        
        if not callback.from_user.username:
            await callback.message.answer("⚠️ Для покупки звезд себе необходимо установить username в настройках Telegram!")
            await state.clear()
            return
        
        username = callback.from_user.username
        await state.update_data(target_username=username)
        
        await callback.message.answer(f"✨ Вы покупаете звезды для себя (@{username}).\nВведите желаемое количество звезд для покупки (50 - 100000):")
        await state.set_state(ShopStates.waiting_for_stars)
    except Exception as e:
        print(f"Error in buy_for_self: {e}")
        await callback.message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")
        await state.clear()

@router.callback_query(ShopStates.waiting_for_recipient, F.data == "buy_for_friend")
async def buy_for_friend(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        await callback.message.answer("✨ Введите username друга в формате @username:")
        await state.set_state(ShopStates.waiting_for_username)
    except Exception as e:
        print(f"Error in buy_for_friend: {e}")
        await callback.message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")
        await state.clear()

@router.message(ShopStates.waiting_for_username)
async def process_friend_username(message: Message, state: FSMContext):
    try:
        username = message.text.strip()
        
        # Проверяем формат username
        if not username.startswith('@') or len(username) < 2:
            await message.answer("❌ Пожалуйста, введите корректный username в формате @username")
            return
        
        # Убираем @ из username
        username = username[1:]
        
        # Проверяем, что username содержит только допустимые символы
        if not all(c.isalnum() or c == '_' for c in username):
            await message.answer("❌ Username может содержать только буквы, цифры и знак подчеркивания")
            return
        
        await state.update_data(target_username=username)
        
        # Запрашиваем подтверждение
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_username")],
            [InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_purchase")]
        ])
        
        await message.answer(f"Вы собираетесь купить звезды для пользователя @{username}. Всё верно?", reply_markup=keyboard)
    except Exception as e:
        print(f"Error in process_friend_username: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")
        await state.clear()

@router.callback_query(ShopStates.waiting_for_username, F.data == "confirm_username")
async def confirm_username(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        
        data = await state.get_data()
        username = data.get('target_username')
        
        if not username:
            await callback.message.answer("❌ Произошла ошибка. Пожалуйста, начните покупку заново.")
            await state.clear()
            return
        
        await callback.message.answer(f"✨ Вы покупаете звезды для @{username}.\nВведите желаемое количество звезд для покупки (50 - 100000):")
        await state.set_state(ShopStates.waiting_for_stars)
    except Exception as e:
        print(f"Error in confirm_username: {e}")
        await callback.message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")
        await state.clear()

@router.callback_query(F.data == "cancel_purchase")
async def cancel_purchase(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("❌ Покупка отменена.")
    await state.clear()

@router.message(ShopStates.waiting_for_stars)
async def process_stars_amount(message: Message, state: FSMContext):
    try:
        stars = int(message.text)
        if stars < 50 or stars > 100000:
            await message.answer("❌ Пожалуйста, введите число звезд от 50 до 100000.")
            return
            
        rubles = round(stars * STAR_TO_RUBLE, 2)
        
        data = await state.get_data()
        target_username = data.get('target_username')
        
        await state.update_data(stars=stars, rubles=rubles)
        
        # Создаем уникальный ID заказа
        order_id = f"order_{message.from_user.id}_{int(datetime.now().timestamp())}"
        await state.update_data(order_id=order_id)
        
        # Показываем пользователю варианты оплаты
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить по СБП", callback_data="pay_sbp")],
            [InlineKeyboardButton(text="💰 Оплатить переводом на карту", callback_data="pay_card")]
        ])
        
        await message.answer(
            f"💰 Сумма к оплате: {rubles} RUB\n"
            f"👤 Получатель: @{target_username}\n\n"
            f"Выберите способ оплаты:",
            reply_markup=keyboard
        )
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректное число звезд.")
    except Exception as e:
        print(f"Error in process_stars_amount: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")

@router.callback_query(F.data == "pay_sbp")
async def pay_with_sbp(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        
        data = await state.get_data()
        stars = data.get('stars')
        rubles = data.get('rubles')
        target_username = data.get('target_username')
        order_id = data.get('order_id')
        
        if not stars or not rubles or not target_username or not order_id:
            await callback.message.answer("❌ Произошла ошибка. Пожалуйста, начните покупку заново.")
            await state.clear()
            return
        
        # Получаем данные для Lava Pay из .env
        secret_key = os.getenv("LAVA_SECRET_KEY", "51372c3ef4b5bcefb07c3d0237675258f9088a1a")
        shop_id = os.getenv("LAVA_SHOP_ID", "e9a3cee7-e740-4422-a0c1-4fba8f7652b9")
        
        # Создаем данные для запроса
        payment_data = {
            "sum": rubles,
            "orderId": order_id,
            "shopId": shop_id,
            "comment": f"Покупка {stars} звезд для @{target_username}"
        }
        
        # Сериализуем данные в JSON
        json_str = json.dumps(payment_data)
        json_bytes = json_str.encode()
        
        # Создаем подпись
        sign = hmac.new(
            bytes(secret_key, 'UTF-8'),
            json_bytes,
            hashlib.sha256
        ).hexdigest()
        
        # Отправляем запрос в Lava API
        headers = {
            'Signature': sign,
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            'https://api.lava.ru/business/invoice/create',
            data=json_bytes,
            headers=headers
        )
        
        response_data = response.json()
        print(f"Lava API response: {response_data}")
        
        if response.status_code == 200 and response_data.get('status_check'):
            payment_url = response_data.get('data', {}).get('url')
            
            await state.update_data(payment_method="СБП (Lava Pay)")
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="💳 Оплатить", url=payment_url)],
                [InlineKeyboardButton(text="✅ Я оплатил(а)", callback_data="check_payment")]
            ])
            
            await callback.message.answer(
                f"💰 Сумма к оплате: {rubles} RUB\n"
                f"👤 Получатель: @{target_username}\n\n"
                f"Для оплаты через СБП нажмите кнопку «Оплатить»\n\n"
                f"✅ После совершения оплаты нажмите кнопку «Я оплатил(а)»",
                reply_markup=keyboard
            )
            
            await state.set_state(ShopStates.waiting_for_payment)
        else:
            print(f"Lava API error: {response_data}")
            await callback.message.answer(
                "❌ Произошла ошибка при создании платежа через СБП. Пожалуйста, выберите другой способ оплаты."
            )
    except Exception as e:
        print(f"Error in pay_with_sbp: {e}")
        await callback.message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@router.callback_query(F.data == "pay_card")
async def pay_with_card(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        
        data = await state.get_data()
        stars = data.get('stars')
        rubles = data.get('rubles')
        target_username = data.get('target_username')
        
        if not stars or not rubles or not target_username:
            await callback.message.answer("❌ Произошла ошибка. Пожалуйста, начните покупку заново.")
            await state.clear()
            return
        
        await state.update_data(payment_method="Перевод на карту")
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Я оплатил(а)", callback_data="check_payment")]
        ])
        
        await callback.message.answer(
            f"💰 Сумма к оплате: {rubles} RUB\n"
            f"👤 Получатель: @{target_username}\n\n{PAYMENT_DETAILS}\n\n"
            f"✅ После совершения оплаты нажмите кнопку «Я оплатил(а)»",
            reply_markup=keyboard
        )
        
        await state.set_state(ShopStates.waiting_for_payment)
        
    except Exception as e:
        print(f"Error in pay_with_card: {e}")
        await callback.message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

@router.callback_query(ShopStates.waiting_for_payment, F.data == "check_payment")
async def check_payment(callback: CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        
        data = await state.get_data()
        stars = data.get('stars')
        rubles = data.get('rubles')
        target_username = data.get('target_username')
        order_id = data.get('order_id')
        payment_method = data.get('payment_method', "Не указан")
        
        if not stars or not rubles or not target_username:
            await callback.message.answer("❌ Произошла ошибка. Пожалуйста, начните покупку заново.")
            await state.clear()
            return
            
        user_id = str(callback.from_user.id)
        user = db.get_user(user_id)
        
        if not user:
            await callback.message.answer("❌ Пользователь не найден. Пожалуйста, перезапустите бота командой /start")
            await state.clear()
            return
            
        db_order_id = db.create_order(user['id'], stars, rubles, "pending")
        
        admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Подтвердить ✅", callback_data=f"approve_payment_{db_order_id}_{target_username}_{user_id}"),
                InlineKeyboardButton(text="Отклонить ❌", callback_data=f"reject_payment_{db_order_id}_{user_id}")
            ],
            [InlineKeyboardButton(text="Профиль пользователя 👤", url=f"tg://user?id={user_id}")]
        ])
        
        admin_message = (
            f"🔔 Новая заявка на покупку звезд!\n\n"
            f"👤 От: {callback.from_user.mention_html()}\n"
            f"🆔 ID: {user_id}\n"
            f"📝 Username заказчика: @{callback.from_user.username}\n"
            f"📝 Username получателя: @{target_username}\n"
            f"⭐️ Количество звезд: {stars}\n"
            f"💰 Сумма: {rubles} RUB\n"
            f"💳 Способ оплаты: {payment_method}\n"
            f"🧾 ID заказа: {order_id}"
        )
        
        for admin_id in ADMIN_IDS:
            try:
                await callback.bot.send_message(
                    chat_id=admin_id,
                    text=admin_message,
                    reply_markup=admin_keyboard,
                    parse_mode="HTML"
                )
            except Exception as e:
                print(f"Failed to notify admin {admin_id}: {e}")
        
        await callback.message.answer(
            "✅ Ваша заявка на покупку успешно отправлена!\n"
            "⏳ Ожидайте подтверждения от администратора.\n"
            "💫 Мы уведомим вас о статусе заказа."
        )
        await state.clear()
        
    except Exception as e:
        print(f"Error in check_payment: {e}")
        await callback.message.answer("❌ Произошла ошибка при обработке платежа. Пожалуйста, попробуйте позже.")
        await state.clear()

@router.callback_query(F.data.startswith("approve_payment_"))
async def approve_payment(callback: CallbackQuery):
    try:
        if not callback.from_user or callback.from_user.id not in ALLOWED_TO_ADMIN_PANEL_IDS:
            await callback.answer("⛔️ У вас нет прав для этого действия!", show_alert=True)
            return
            
        try:
            callback_parts = callback.data.split("_")
            if len(callback_parts) != 5:
                raise ValueError("Invalid callback data format")
            
            order_id = int(callback_parts[2])
            username = callback_parts[3]
            user_id = callback_parts[4]
            
            if not username or not user_id:
                raise ValueError("Missing username or user_id")
                
        except (ValueError, IndexError) as e:
            print(f"Error parsing callback data: {e}")
            await callback.answer("❌ Некорректные данные запроса", show_alert=True)
            return
            
        order = db.get_order(order_id)
        if not order:
            await callback.answer("❌ Заказ не найден!", show_alert=True)
            return
            
        if order['status'] != "pending":
            await callback.answer("⚠️ Этот заказ уже обработан!", show_alert=True)
            return
            
        if order['amount_star'] <= 0:
            await callback.answer("❌ Некорректное количество звезд в заказе", show_alert=True)
            return
        
        if not db.update_order_status(order_id, "completed"):
            await callback.answer("❌ Ошибка при обновлении статуса заказа", show_alert=True)
            return

        try:
            await callback.bot.send_message(
                chat_id=user_id,
                text=f"✅ Ваш заказ на {order['amount_star']} Telegram звезд для @{username} принят!\n"
                     f"⏳ Звезды будут зачислены в течение нескольких минут."
            )
            
            await callback.message.edit_text(
                f"{callback.message.text}\n\n✅ Оплата подтверждена\n⭐️ Звезды будут зачислены вручную",
                reply_markup=None
            )
            
        except Exception as e:
            print(f"Failed to send notification to user {user_id}: {e}")
            await callback.answer("⚠️ Не удалось отправить уведомление пользователю", show_alert=True)

    except Exception as e:
        print(f"Error in approve_payment: {e}")
        await callback.answer("❌ Произошла ошибка при обработке платежа", show_alert=True)

@router.callback_query(F.data.startswith("reject_payment_"))
async def reject_payment(callback: CallbackQuery):
    try:
        if callback.from_user.id not in ALLOWED_TO_ADMIN_PANEL_IDS:
            await callback.answer("⛔️ У вас нет прав для этого действия!", show_alert=True)
            return
            
        order_id = int(callback.data.split("_")[2])
        user_id = callback.data.split("_")[3]
        order = db.get_order(order_id)
        
        if not order:
            await callback.answer("❌ Заказ не найден!", show_alert=True)
            return
            
        if order['status'] != "pending":
            await callback.answer("⚠️ Этот заказ уже обработан!", show_alert=True)
            return
        
        db.update_order_status(order_id, "rejected")
        
        try:
            await callback.bot.send_message(
                chat_id=user_id,
                text=f"❌ Ваш заказ на {order['amount_star']} Telegram звезд отклонен.\n"
                     f"💭 Возможные причины:\n"
                     f"• Неверная сумма оплаты\n"
                     f"• Оплата не поступила\n"
                     f"• Некорректные реквизиты\n\n"
                     f"👨‍💻 Для уточнения деталей обратитесь к администратору @Ara_stars"
            )
        except Exception as e:
            print(f"Failed to notify user {user_id}: {e}")
        
        await callback.message.edit_text(
            f"{callback.message.text}\n\n❌ Оплата отклонена",
            reply_markup=None
        )
        
    except Exception as e:
        print(f"Error in reject_payment: {e}")
        await callback.answer("❌ Произошла ошибка при отклонении платежа", show_alert=True)
