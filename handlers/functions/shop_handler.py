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
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Подтвердить оплату ✅", callback_data="check_payment")]
        ])
        
        await message.answer(
            f"💰 Сумма к оплате: {rubles} RUB\n"
            f"👤 Получатель: @{target_username}\n\n{PAYMENT_DETAILS}\n\n"
            f"✅ После совершения оплаты нажмите кнопку «Подтвердить оплату»",
            reply_markup=keyboard
        )
        await state.set_state(ShopStates.waiting_for_payment)
        
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректное число звезд.")
    except Exception as e:
        print(f"Error in process_stars_amount: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")

@router.callback_query(ShopStates.waiting_for_payment, F.data == "check_payment")
async def check_payment(callback: CallbackQuery, state: FSMContext):
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
            
        user_id = str(callback.from_user.id)
        user = db.get_user(user_id)
        
        if not user:
            await callback.message.answer("❌ Пользователь не найден. Пожалуйста, перезапустите бота командой /start")
            await state.clear()
            return
            
        order_id = db.create_order(user['id'], stars, rubles, "pending")
        
        admin_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="Подтвердить ✅", callback_data=f"approve_payment_{order_id}_{target_username}_{user_id}"),
                InlineKeyboardButton(text="Отклонить ❌", callback_data=f"reject_payment_{order_id}_{user_id}")
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
            f"💰 Сумма: {rubles} RUB"
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
        # Проверка прав администратора
        if not callback.from_user or callback.from_user.id not in ADMIN_IDS:
            await callback.answer("⛔️ У вас нет прав для этого действия!", show_alert=True)
            return
            
        # Парсинг и валидация данных из callback
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
            
        # Проверка заказа
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
        
        # Обновление статуса заказа
        if not db.update_order_status(order_id, "completed"):
            await callback.answer("❌ Ошибка при обновлении статуса заказа", show_alert=True)
            return

        # Отправка начального уведомления пользователю
        try:
            await callback.bot.send_message(
                chat_id=user_id,
                text=f"✅ Ваш заказ на {order['amount_star']} Telegram звезд для @{username} принят!\n"
                     f"⏳ Звезды будут зачислены в течение нескольких минут."
            )
        except Exception as e:
            print(f"Failed to send initial notification to user {user_id}: {e}")
            await callback.answer("⚠️ Не удалось отправить уведомление пользователю", show_alert=True)

        # Обработка покупки звезд через API
        try:
            import aiohttp
            import os
            
            api_key = os.getenv('STAR_SOV_API_KEY')
            api_url = os.getenv('URL_SEND_PAID_STAR_SOV')
            
            if not api_key or not api_url:
                raise ValueError("Missing API configuration")
            
            async with aiohttp.ClientSession() as session:
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }
                data = {
                    "Username": username,  # Используем username получателя
                    "Quantity": order['amount_star']
                }
                
                async with session.post(api_url, 
                                      headers=headers, 
                                      json=data,
                                      timeout=30) as response:
                    response_text = await response.text()
                    
                    if response.status == 200:
                        # Обновление баланса пользователя
                        if not db.update_user_balance(user_id, order['amount_star']):
                            raise Exception("Failed to update user balance")
                            
                        # Отправка уведомления об успехе
                        await callback.bot.send_message(
                            chat_id=user_id,
                            text=f"🌟 Поздравляем! {order['amount_star']} Telegram звезд успешно зачислены для @{username}!\n"
                                 f"💫 Спасибо за покупку! Желаем приятного использования.\n"
                                 f"🎁 Будем рады видеть вас снова!"
                        )
                    else:
                        await callback.bot.send_message(
                            chat_id=user_id,
                            text=f"⚠️ Произошла техническая ошибка при зачислении звезд.\n"
                                 f"👨‍💻 Пожалуйста, обратитесь к администратору @admin"
                        )
                        print(f"Star purchase API error: {response_text}")
                        raise Exception(f"API returned status {response.status}: {response_text}")
        
            # Обновление сообщения администратора
            try:
                await callback.message.edit_text(
                    f"{callback.message.text}\n\n✅ Оплата подтверждена и обработана",
                    reply_markup=None
                )
            except Exception as e:
                print(f"Failed to update admin message: {e}")
            
        except aiohttp.ClientError as e:
            print(f"API connection error: {e}")
            db.update_order_status(order_id, "error")
            await callback.answer("❌ Ошибка соединения с сервером звезд", show_alert=True)
            
        except Exception as e:
            print(f"Error processing stars: {e}")
            db.update_order_status(order_id, "error")
            await callback.answer("❌ Произошла ошибка при зачислении звезд", show_alert=True)
        
    except Exception as e:
        print(f"Error in approve_payment: {e}")
        await callback.answer("❌ Произошла ошибка при подтверждении платежа", show_alert=True)

@router.callback_query(F.data.startswith("reject_payment_"))
async def reject_payment(callback: CallbackQuery):
    try:
        if callback.from_user.id not in ADMIN_IDS:
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
