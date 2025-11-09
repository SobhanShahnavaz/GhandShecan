from aiogram import Router, types, F
from app.keyboards.main_menu import main_menu_keyboard
from app.services import marzban_api
from app.services.database import get_marzban_accounts_by_user, get_user_id, add_order
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import os

router = Router()
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "درود ، به ربات cipher connect خوش اومدی ✨\n\nاینترنت آزاد رو با ما تجربه کنید🌐\n\n🟢 اتصال پایدار و با کیفیت \n\n⚡️پر سرعت با کمترین پینگ\n\n🔒 تضمین اتصال ایمن و مطمئن\n\n⚪️ منصفانه ترین قیمت\n\n⏱ پشتیبانی ۲۴ ساعته\n\nجهت دریافت نمایندگی حتما با پشتیبانی در ارتباط باشید ✅\n\n🆔 @freeedomarea",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query()
async def handle_menu_selection(callback: types.CallbackQuery):
    data = callback.data

    if data == "buy_config":
        await callback.answer("🛍 بخش خرید کانفیگ در حال ساخت است...", show_alert=True)

    elif data == "my_configs":
        telegram_id = callback.from_user.id
        user_id = await get_user_id(telegram_id)

        if not user_id:
            await callback.message.answer("⚠️ ابتدا باید ثبت‌نام کنید.")
            return

        accounts = await get_marzban_accounts_by_user(user_id)
        if not accounts:
            await callback.message.answer("❌ هیچ حسابی برای شما ثبت نشده است.")
            return

        # ساخت کیبورد اینلاین از حساب‌ها
        keyboard = InlineKeyboardMarkup(inline_keyboard=[])
        for acc in accounts:
            username = acc[2]  # panel_username
            status = acc[3] or "unknown"
            icon = "🟢" if status == "active" else "🔴"
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"{icon} {username}",
                    callback_data=f"show_acc_{username}"
                )
            ])

        await callback.message.answer(
            "🔰 حساب مورد نظر را انتخاب کنید:",
            reply_markup=keyboard
        )
        await callback.answer()



    elif data == "test_account":
        await callback.answer("🧪 اکانت تست به‌زودی فعال می‌شود!", show_alert=True)

    elif data == "wallet":
        await callback.answer("💰 مدیریت کیف پول به‌زودی فعال می‌شود!", show_alert=True)

    elif data == "profile":
        await callback.answer("👤 نمایش مشخصات کاربری در حال آماده‌سازی است.", show_alert=True)

    elif data == "apps":
        await callback.answer("📲 نصب برنامه‌ها به‌زودی اضافه می‌شود!", show_alert=True)

    elif data == "support":
        await callback.answer("🧑‍💬 پشتیبانی آنلاین به‌زودی فعال می‌شود.", show_alert=True)

    elif data == "referrals":
        await callback.answer("👥 بخش زیرمجموعه‌گیری به‌زودی می‌آید!", show_alert=True)
    
    elif data == "send_receipt":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📤 ارسال رسید", callback_data="waiting_for_receipt")],
            [InlineKeyboardButton(text="❌ منصرف شدم", callback_data="cancel_payment")]
        ])

        await callback.message.answer(
            "💳 لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=keyboard
        )
        await callback.answer()

    elif data == "cancel_payment":
        await callback.message.answer("✅ عملیات خرید لغو شد.\nمی‌تونی هر زمان خواستی دوباره از منوی خرید اقدام کنی.")
        await callback.answer()
    
    elif data == "waiting_for_receipt":
        await callback.message.answer(
            "📸 لطفاً تصویر رسید پرداخت خود را ارسال کنید.\n\n"
            "در صورت لغو، از منوی اصلی گزینه‌ی دیگری را انتخاب کنید."
        )
        await callback.answer()


    elif data.startswith("show_acc_"):
        panel_username = data.replace("show_acc_", "")
        telegram_id = callback.from_user.id
        user_id = await get_user_id(telegram_id)

        accounts = await get_marzban_accounts_by_user(user_id)
        account = next((a for a in accounts if a[2] == panel_username), None)

        if not account:
            await callback.message.answer("⚠️ حساب مورد نظر یافت نشد.")
            return

        status = account[3] or "نامشخص"
        expire_ts = account[4]
        used_traffic = account[5] or 0
        subscription_url = account[6] or "⛔ لینک اشتراک موجود نیست"

        # تبدیل بایت به گیگابایت
        used_gb = used_traffic / (1024 ** 3)
        used_text = f"{used_gb:.2f} GB"

        # محاسبه روزهای باقی‌مانده
        from datetime import datetime
        if expire_ts:
            expire_date = datetime.utcfromtimestamp(expire_ts)
            remaining_days = (expire_date - datetime.utcnow()).days
            if remaining_days < 0:
                expire_text = "⛔ منقضی شده"
            elif remaining_days == 0:
                expire_text = "⚠️ کمتر از ۱ روز"
            else:
                expire_text = f"{remaining_days} روز باقی‌مانده"
        else:
            expire_text = "نامشخص"

        text = (
            f"👤 <b>{panel_username}</b>\n"
            f"🔸 وضعیت: {status}\n"
            f"📦 مصرف: {used_text}\n"
            f"⏳ انقضا: {expire_text}\n\n"
            f"🔗 <b>لینک اشتراک:</b>\n"
            f"{subscription_url}"
        )

        await callback.message.answer(text, parse_mode="HTML")
        await callback.answer()
