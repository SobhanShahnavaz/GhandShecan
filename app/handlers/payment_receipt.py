# app/handlers/payment_receipt.py

from aiogram import Router, types
from datetime import datetime
import os
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.services.database import add_order, get_user_id
from app.handlers.menu import user_choices  # اطلاعات موقت خرید

router = Router()

ORDERS_CHANNEL_ID = int(os.getenv("ORDERS_CHANNEL_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))

@router.message(lambda msg: msg.photo)
async def handle_payment_receipt(message: types.Message):
    """
    هندلر مخصوص دریافت عکس رسید پرداخت از کاربر
    """
    telegram_id = message.from_user.id
    db_user_id = await get_user_id(telegram_id)
    if message.chat.type != "private":
        return
    if not db_user_id:
        await message.answer("⚠️ ابتدا باید در ربات ثبت‌نام کنید.")
        return

    # بررسی اینکه کاربر خرید فعال دارد یا نه
    user_data = user_choices.get(telegram_id)
    if not user_data:
        await message.answer("⚠️ هنوز خریدی شروع نکردی!\nاز منوی اصلی گزینه «خرید کانفیگ» رو انتخاب کن.")
        return

    # گرفتن آخرین عکس (بیشترین رزولوشن)
    file_id = message.photo[-1].file_id

    # گرفتن جزئیات انتخاب‌شده از user_choices
    config_name = user_data.get("config_name", "بدون نام")
    duration = user_data.get("duration", 0)
    size = user_data.get("size", 0)
    price = user_data.get("price", 0)

    # ذخیره در دیتابیس
    order_id = await add_order(telegram_id, config_name, price, duration, size, file_id)

    # پیام برای مدیر
    caption = (
        f"📥 <b>رسید جدید پرداخت</b>\n\n"
        f"👤 <b>کاربر:</b> @{message.from_user.username or message.from_user.full_name}\n"
        f"🆔 <code>{telegram_id}</code>\n"
        f"📝 <b>نام کانفیگ:</b> {config_name}\n"
        f"⏱ <b>مدت:</b> {duration} ماهه\n"
        f"📦 <b>حجم:</b> {size} گیگ\n"
        f"💰 <b>مبلغ:</b> {price:,} هزار تومان\n"
        f"🕒 <b>تاریخ:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )

    # ساخت کیبورد برای مدیر
    keyboard = InlineKeyboardMarkup(inline_keyboard=[[ 
    InlineKeyboardButton(text="✅ تأیید پرداخت", callback_data=f"order_approve_{order_id}"),
    InlineKeyboardButton(text="❌ رد پرداخت", callback_data=f"order_reject_{order_id}")
]])

    try:
        # ارسال به کانال (بدون دکمه، فقط آرشیو)
        await message.bot.send_photo(
            chat_id=ORDERS_CHANNEL_ID,
            photo=file_id,
            caption=caption,
            parse_mode="HTML"
        )

        # ارسال به PV مدیر با دکمه‌های فعال
        sent_admin_msg = await message.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=file_id,
            caption=caption,
            parse_mode="HTML",
            reply_markup=keyboard
        )
        
        await message.answer("✅ رسید شما ارسال شد و در انتظار تأیید مدیر است.")

    except Exception as e:
        await message.answer("⚠️ خطایی در ارسال رسید به مدیر رخ داد.")
        print(f"[Payment Receipt] Error sending to admin: {e}")
    # این پیام آیدی مدیر بود:
    # admin_msg_id = sent_admin_msg.message_id

    # پاک‌سازی انتخاب‌های کاربر بعد از اتمام پرداخت
    user_choices.pop(telegram_id, None)
