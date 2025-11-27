from aiogram import Router, types, F
from aiogram.filters import Command
from app.keyboards.admin_menu import admin_menu_keyboard
import os

router = Router()


ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

@router.message(Command("axtar"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:  # replace with your constant
        return

    await message.answer("🛠 پنل مدیریت", reply_markup=admin_menu_keyboard())

