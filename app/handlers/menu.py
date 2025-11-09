from aiogram import Router, types, F
from app.keyboards.main_menu import main_menu_keyboard
from app.services import marzban_api
from app.services.database import get_marzban_username, set_marzban_username

router = Router()


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
        tg_id = callback.from_user.id
        mb_user = await get_marzban_username(tg_id)

        if not mb_user:
            await callback.message.answer(
                "⚠️ برای این حساب، نام کاربری پنل در دیتابیس یافت نشد.\n"
                "لطفاً با پشتیبانی تماس بگیر تا تنظیم شود."
            )
            await callback.answer()
            return

        await callback.message.answer("⏳ درحال دریافت اطلاعات از پنل ...")
        user_data = await marzban_api.get_user_by_username(mb_user)

        if not user_data:
            await callback.message.answer(
                "⚠️ کاربری با این نام در پنل پیدا نشد یا ارتباط برقرار نشد."
            )
            await callback.answer()
            return

        # ساخت پیام خلاصه کاربر
        username = user_data.get("username")
        status = user_data.get("status")
        used_bytes = user_data.get("used_traffic", 0) or 0
        expire_ts = user_data.get("expire")

        # تبدیل بایت به گیگابایت
        used_gb = used_bytes / (1024 ** 3)
        used_text = f"{used_gb:.2f} GB"

        # محاسبه روزهای باقی‌مانده
        from datetime import datetime, timedelta
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

        # استخراج Subscription Link (در JSON با کلید 'subscription_url' یا 'subscription')
        sub_link = user_data.get("subscription_url") or user_data.get("subscription") or "⛔ لینک اشتراک موجود نیست"

        # ساخت پیام نهایی
        lines = [
            f"👤 <b>{username}</b>",
            f"🔸 وضعیت: {status}",
            f"📦 مصرف: {used_text}",
            f"⏳ انقضا: {expire_text}",
            "\n🔗 لینک اشتراک:",
            f"{sub_link}"
        ]

        await callback.message.answer("\n".join(lines), parse_mode="HTML")
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
