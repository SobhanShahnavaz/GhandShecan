from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard=[
        [InlineKeyboardButton(text="📦 نمایش پلن‌ها", callback_data="admin_show_plans")],
        [InlineKeyboardButton(text="➕ افزودن پلن", callback_data="admin_add_plan")],
        [InlineKeyboardButton(text="💳 مدیریت کارت ها", callback_data="admin_manage_cards")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)