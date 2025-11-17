from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.services.database import update_order_status, get_order_by_id, get_user , add_marzban_account
from app.services.marzban_api import create_user_in_marzban
import os
from datetime import datetime, timedelta

router = Router()

ORDERS_CHANNEL_ID = int(os.getenv("ORDERS_CHANNEL_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))
HELP_MESSAGE_URL = "https://t.me/wvpnw/556"

@router.callback_query(lambda c: c.data.startswith("order_approve_"))
async def approve_order(callback: types.CallbackQuery):
    
    print(f"[DEBUG] Callback received: {callback.data}")
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ فقط مدیر اصلی می‌تونه این کار رو انجام بده.", show_alert=True)
        return

    order_id = int(callback.data.split("_")[-1])
    order = await get_order_by_id(order_id)
    user_id = order[1] if isinstance(order, (list, tuple)) else order["telegram_user_id"]
    if not order:
        await callback.answer("❌ سفارش پیدا نشد!", show_alert=True)
        return
    user = await get_user(user_id)
    await update_order_status(order_id, "approved")
    tg_username = user[2] if isinstance(user, (list, tuple)) else user["username"]
    tg_phonenum = user[5] if isinstance(user, (list, tuple)) else user["phone_number"]
    if tg_username:
        prefix = tg_username
    else :
        prefix = tg_phonenum
    try:
        # ساخت یوزر در مرزبان
        config_name = order[2] if isinstance(order, (list, tuple)) else order["plan_name"]
        Plan_name = config_name + "-" + prefix
        price = order[3] if isinstance(order, (list, tuple)) else order["price"]
        duration = order[4] if isinstance(order, (list, tuple)) else order["duration"]
        data_limit = order[5] if isinstance(order, (list, tuple)) else order["data_limit"]
        days = duration * 30
        expire_timestamp = int((datetime.utcnow() + timedelta(days)).timestamp())
        # تبدیل قیمت یا حجم به مشخصات پلن (موقت)
        # مثلا بر اساس نام کانفیگ، حجم و مدت مشخص کن
        sub_link = await create_user_in_marzban(username=Plan_name, data_limit_gb=data_limit, expire_days= days)
        await add_marzban_account(user_id,Plan_name,"Active",expire_timestamp,0,sub_link)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📘 نحوه استفاده از لینک", url=HELP_MESSAGE_URL)],
            [InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="back_to_menu")]
        ])
        await callback.bot.send_message(
            user_id,
            f"✅ حساب شما ساخته شد!\n\n"
            f"🔗 <b>لینک اشتراک:</b>\n<code>{sub_link}</code>",
            parse_mode="HTML",
            reply_markup=keyboard
        )
        # ارسال لینک به کاربر
        
        await callback.bot.send_message(
            ADMIN_ID,  
            "سفارش با موفقیت تأیید شد ✅")
    except Exception as e:
        await callback.bot.send_message(user_id, "⚠️ خطا در ساخت حساب در پنل. پشتیبانی در حال بررسی است.")
        await callback.bot.send_message(
            ADMIN_ID,  
            "خطایی در روند تایید رخ داد. لطفا خطاهارا بررسی کنید!")
        print(f"[Marzban Error] {e}")
    try:
        if callback.message.chat.type == "private":
            await callback.message.delete()
    except Exception as e:
        print(f"[DEBUG] Couldn't delete message: {e}")
    
    
    


@router.callback_query(lambda c: c.data.startswith("order_reject_"))
async def reject_order(callback: types.CallbackQuery):
    print(f"[DEBUG] Callback received: {callback.data}")
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("⛔ فقط مدیر اصلی می‌تونه این کار رو انجام بده.", show_alert=True)
        return

    order_id = int(callback.data.split("_")[-1])
    order = await get_order_by_id(order_id)
    user_id = order[1] if isinstance(order, (list, tuple)) else order["telegram_user_id"]
    if not order:
        await callback.answer("❌ سفارش پیدا نشد!", show_alert=True)
        return

    await update_order_status(order_id, "rejected")

    try:
        await callback.bot.send_message(
            user_id,  
            "❌ پرداخت شما رد شد.\nلطفاً به پشتیبانی پیام بدهید."
        )
    except Exception as e:
        print(e,user_id)
    try:
        if callback.message.chat.type == "private":
            await callback.message.delete()
    except Exception as e:
        print(f"[DEBUG] Couldn't delete message: {e}")
    
    await callback.bot.send_message(
        ADMIN_ID,
        "سفارش رد شد 🚫")
    
