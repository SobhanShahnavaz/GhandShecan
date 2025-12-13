from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def custom_plan_keyboard(gb: int, days: int):
    return InlineKeyboardMarkup(inline_keyboard=[

        # Title: حجم سرویس
        [InlineKeyboardButton(text="حجم سرویس", callback_data="none")],

        [
            InlineKeyboardButton(text="🔼", callback_data="inc_gb"),
            InlineKeyboardButton(text=f"{gb} گیگابایت", callback_data="none"),
            InlineKeyboardButton(text="🔽", callback_data="dec_gb")
        ],

        [
            InlineKeyboardButton(text="+10", callback_data="inc_gb_big"),
            InlineKeyboardButton(text="-10", callback_data="dec_gb_big")
        ],

        # Title: مدت زمان سرویس
        [InlineKeyboardButton(text="مدت زمان سرویس", callback_data="none")],

        [
            InlineKeyboardButton(text="🔼", callback_data="inc_days"),
            InlineKeyboardButton(text=f"{days} روز", callback_data="none"),
            InlineKeyboardButton(text="🔽", callback_data="dec_days")
        ],

        [
            InlineKeyboardButton(text="+10", callback_data="inc_days_big"),
            InlineKeyboardButton(text="-10", callback_data="dec_days_big")
        ],

        [InlineKeyboardButton(text="مرحله بعدی", callback_data="admin_custom_next")],
        [InlineKeyboardButton(text="نمیخوام 🫩", callback_data="axtar_menu")]
    ])
