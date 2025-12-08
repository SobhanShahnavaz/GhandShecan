from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard=[
        [InlineKeyboardButton(text="📦 نمایش پلن‌ها", callback_data="admin_show_plans"),InlineKeyboardButton(text="🔗 تغییر لینک ها", callback_data="set_tutor_links")],
        [InlineKeyboardButton(text="➕ افزودن پلن", callback_data="admin_add_plan")],
        [InlineKeyboardButton(text="💳 مدیریت کارت ها", callback_data="admin_manage_cards"),InlineKeyboardButton(text="🎫 مدیریت تخفیف ها", callback_data="admin_manage_offcodes")],
        [InlineKeyboardButton(text="💵 انتقال اعتبار", callback_data="admin_send_credit")],
        [InlineKeyboardButton(text="🗑 حذف تست‌های غیرفعال", callback_data="remove_disabled_tests")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)