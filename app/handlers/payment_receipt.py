# app/handlers/payment_receipt.py

from aiogram import Router, types
from datetime import datetime
import os
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.services.database import add_order, get_user_id

router = Router()

# آیدی مدیر از فایل env خونده میشه
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))


@router.message(lambda msg: msg.photo)
async def handle_payment_receipt(message: types.Message):
    """
    هندلر مخصوص دریافت عکس رسید پرداخت از کاربر
    """
    telegram_id = message.from_user.id
    user_id = await get_user_id(telegram_id)

    if not user_id:
        await message.answer("⚠️ ابتدا باید در ربات ثبت‌نام کنید.")
        return

    # گرفتن آخرین عکس (بیشترین رزولوشن)
    file_id = message.photo[-1].file_id

    # (در نسخه بعدی از انتخاب پلن کاربر می‌گیریم)
    plan_name = "پلن ۱ ماهه"
    price = 45000

    # ذخیره سفارش در دیتابیس
    await add_order(user_id, plan_name, price, file_id)

    # پیام ارسالی برای مدیر
    caption = (
        f"📥 <b>رسید جدید دریافت شد!</b>\n\n"
        f"👤 <b>کاربر:</b> @{message.from_user.username or message.from_user.full_name}\n"
        f"🆔 <code>{telegram_id}</code>\n"
        f"💳 <b>پلن:</b> {plan_name}\n"
        f"💰 <b>مبلغ:</b> {price:,} تومان\n"
        f"🕒 <b>تاریخ:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    try:
        # ارسال عکس رسید برای مدیر
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
        InlineKeyboardButton(text="✅ تأیید پرداخت", callback_data=f"order_approve_{user_id}"),
        InlineKeyboardButton(text="❌ رد پرداخت", callback_data=f"order_reject_{user_id}")
        ]
        ])

        await message.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=file_id,
            caption=caption,
            parse_mode="HTML",
            reply_markup=keyboard
        )

        await message.answer("✅ رسید شما با موفقیت ارسال شد و در انتظار بررسی مدیر است.")
    except Exception as e:
        await message.answer("⚠️ خطایی در ارسال رسید به مدیر رخ داد.")
        print(f"[Payment Receipt] Error sending to admin: {e}")
