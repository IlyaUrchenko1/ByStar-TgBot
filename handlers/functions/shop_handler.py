from decimal import Decimal
import logging
from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
import requests
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

router = Router()
logger = logging.getLogger(__name__)

CRYPTOCLOUD_API_URL = "https://api.cryptocloud.plus/v2/invoice/create"
API_KEY = os.getenv("API_KEY")
SHOP_ID = os.getenv("SHOP_ID")

STAR_PRICES = {
    "1": 5,      # 5 USD за 1 звезду
    "5": 20,     # 20 USD за 5 звезд  
    "10": 35,    # 35 USD за 10 звезд
    "20": 60     # 60 USD за 20 звезд
}

@router.callback_query(F.data == "buy_stars")
async def show_star_packages(callback: types.CallbackQuery):
    """Показывает доступные пакеты звезд для покупки"""
    await callback.answer()
    
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[
            [
                types.InlineKeyboardButton(text=f"⭐ x{stars} - ${price}", 
                                         callback_data=f"buy_stars:{stars}")
            ] for stars, price in STAR_PRICES.items()
        ]
    )
    
    await callback.message.answer(
        "🌟 Выберите количество звезд для покупки:\n\n"
        "Все платежи безопасно обрабатываются через @CryptoCloud Plus",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("buy_stars:"))
async def process_buy_stars(callback: types.CallbackQuery, state: FSMContext):
    """Обрабатывает выбор пакета звезд и создает счет для оплаты"""
    stars = callback.data.split(":")[1]
    amount = STAR_PRICES[stars]
    
    try:
        headers = {
            "Authorization": f"Token {API_KEY}",
            "Content-Type": "application/json"
        }
        
        data = {
            "shop_id": SHOP_ID,
            "amount": str(amount),
            "currency": "USD",
            "order_id": f"stars_{callback.from_user.id}_{int(datetime.now().timestamp())}",
            "description": f"Покупка {stars} звезд",
            "lang": "ru"
        }
        
        response = requests.post(CRYPTOCLOUD_API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        
        if result.get("status") == "success" and result.get("result"):
            payment_data = result["result"]
            payment_link = payment_data["link"]
            payment_uuid = payment_data["uuid"]
            expiry_date = datetime.strptime(payment_data["expiry_date"], "%Y-%m-%d %H:%M:%S.%f")
            currency_info = payment_data["currency"]
            
            await state.update_data(
                payment_uuid=payment_uuid,
                stars_amount=stars,
                user_id=callback.from_user.id,
                timestamp=datetime.now().isoformat(),
                expiry_date=expiry_date.isoformat()
            )
            
            keyboard = types.InlineKeyboardMarkup(
                inline_keyboard=[
                    [types.InlineKeyboardButton(
                        text="💳 Оплатить", 
                        url=payment_link
                    )],
                    [types.InlineKeyboardButton(
                        text="🔄 Проверить оплату",
                        callback_data=f"check_payment:{payment_uuid}"
                    )]
                ]
            )
            
            message_text = (
                f"🌟 Заказ на {stars} звезд создан!\n\n"
                f"💰 Сумма к оплате: ${amount}\n"
                f"💱 Валюта: {currency_info['name']} ({currency_info['fullcode']})\n"
                f"⏳ Действителен до: {expiry_date.strftime('%d.%m.%Y %H:%M')}\n\n"
                "⚠️ После оплаты нажмите 'Проверить оплату'"
            )
            
            await callback.message.edit_text(
                message_text,
                reply_markup=keyboard
            )
            
        else:
            raise Exception("Failed to create invoice")
            
    except Exception as e:
        logger.error(f"Error creating payment: {e}")
        await callback.message.edit_text(
            "❌ Произошла ошибка при создании платежа. Попробуйте позже."
        )

@router.callback_query(F.data.startswith("check_payment:"))
async def check_payment_status(callback: types.CallbackQuery, state: FSMContext):
    """Проверяет статус оплаты"""
    payment_uuid = callback.data.split(":")[1]
    
    try:
        url = "https://api.cryptocloud.plus/v2/invoice/info"
        headers = {
            "Authorization": f"Token {API_KEY}"
        }
        params = {
            "uuid": payment_uuid
        }

        response = requests.get(url, headers=headers, params=params)
        result = response.json()

        if response.status_code == 200 and result.get("status") == "success":
            payment_data = result["result"]
            payment_status = payment_data["status"]
            
            if payment_status == "paid":
                # Здесь можно добавить логику начисления звезд
                await callback.message.edit_text(
                    "✅ Оплата успешно проведена!\n"
                    "Звезды начислены на ваш баланс.",
                    reply_markup=None
                )
            elif payment_status == "expired":
                await callback.message.edit_text(
                    "❌ Время оплаты истекло.\n"
                    "Пожалуйста, создайте новый заказ.",
                    reply_markup=None
                )
            else:
                await callback.answer(
                    "❌ Оплата еще не поступила. Попробуйте позже.",
                    show_alert=True
                )
        else:
            raise Exception("Failed to check payment status")
        
    except Exception as e:
        logger.error(f"Error checking payment: {e}")
        await callback.answer(
            "❌ Произошла ошибка при проверке оплаты. Попробуйте позже.",
            show_alert=True
        )
