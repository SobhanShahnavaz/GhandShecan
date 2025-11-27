from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="🤝 درخواست همکاری", callback_data="request_agent")],
        [InlineKeyboardButton(text="🛒 خرید کانفیگ", callback_data="buy_config"),InlineKeyboardButton(text="💎 اکانت تست", callback_data="test_account")],
        [InlineKeyboardButton(text="💼 کانفیگ‌های من", callback_data="my_configs")],
        [InlineKeyboardButton(text="💳 کیف پول / ارسال رسید", callback_data="wallet")],
        [InlineKeyboardButton(text="👤 مشخصات کاربری", callback_data="profile"),InlineKeyboardButton(text="📲 نصب برنامه", callback_data="apps")],
        [InlineKeyboardButton(text="🧑‍💬 پشتیبانی آنلاین", callback_data="support")],
        [InlineKeyboardButton(text="👥 زیرمجموعه‌گیری", callback_data="referrals")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def agent_menu_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(text="💸‌ پنل همکاری", callback_data="agent_panel")],
        [InlineKeyboardButton(text="🛒 خرید کانفیگ", callback_data="buy_config"),InlineKeyboardButton(text="💎 اکانت تست", callback_data="test_account")],
        [InlineKeyboardButton(text="💼 کانفیگ‌های من", callback_data="my_configs")],
        [InlineKeyboardButton(text="💳 کیف پول / ارسال رسید", callback_data="wallet")],
        [InlineKeyboardButton(text="👤 مشخصات کاربری", callback_data="profile"),InlineKeyboardButton(text="📲 نصب برنامه", callback_data="apps")],
        [InlineKeyboardButton(text="🧑‍💬 پشتیبانی آنلاین", callback_data="support")],
        [InlineKeyboardButton(text="👥 زیرمجموعه‌گیری", callback_data="referrals")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def request_cooperation_keyboard()-> InlineKeyboardMarkup:

    keyboard =[
        [InlineKeyboardButton(
            text="درخواست همکاری",
            callback_data="request_agent"
        )]
    ]
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)