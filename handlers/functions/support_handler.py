from aiogram import Router, F	
from aiogram.types import Message
router = Router(name='support')

@router.message(F.text == "🆘 Поддержка") 
async def show_support(message: Message):
    try:
        await message.answer(
            "👨‍💻 По всем вопросам обращайтесь к:\n"
            "@Ara_stars\n"
            "Среднее время ответа 5-10 минут"
        )
    except Exception as e:
        print(f"Error in show_support: {e}")
        await message.answer("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")
