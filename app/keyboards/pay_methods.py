from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def Payment_keyboard() -> InlineKeyboardMarkup:
    keyboard=[
        [InlineKeyboardButton(text="💳 انتقال به کارت", callback_data="waiting_for_receipt")],
        [InlineKeyboardButton(text="💰 پرداخت از موجودی", callback_data="pay_with_wallet")],
        [InlineKeyboardButton(text="👀 کد تخفیف دارم", callback_data="have_off_code")],
        [InlineKeyboardButton(text="❌ منصرف شدم", callback_data="cancel_payment")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)