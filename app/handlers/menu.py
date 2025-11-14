from aiogram import Router, types, F
from app.keyboards.main_menu import main_menu_keyboard
from app.services import marzban_api
from app.services.database import get_marzban_accounts_by_user, get_user_id, add_order
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import re


import os

router = Router()
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
# حافظه موقت برای نگهداری انتخاب‌های کاربر
user_choices = {}

@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "درود ، به ربات cipher connect خوش اومدی ✨\n\nاینترنت آزاد رو با ما تجربه کنید🌐\n\n🟢 اتصال پایدار و با کیفیت \n\n⚡️پر سرعت با کمترین پینگ\n\n🔒 تضمین اتصال ایمن و مطمئن\n\n⚪️ منصفانه ترین قیمت\n\n⏱ پشتیبانی ۲۴ ساعته\n\nجهت دریافت نمایندگی حتما با پشتیبانی در ارتباط باشید ✅\n\n🆔 @freeedomarea",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(lambda c: not c.data.startswith("order_"))
async def handle_menu_selection(callback: types.CallbackQuery):
    data = callback.data
    
    
        # ----------------------------
    # خرید کانفیگ — دو مرحله‌ای بدون state
    # ----------------------------

    if data == "buy_config":
        # مرحله ۱: انتخاب مدت
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🕒 سه ماهه", callback_data="duration_3"),
                InlineKeyboardButton(text="🕑 دو ماهه", callback_data="duration_2"),
                InlineKeyboardButton(text="🕐 یک ماهه", callback_data="duration_1"),
            ],
            [
                InlineKeyboardButton(text="❌ انصراف", callback_data="cancel_payment")
            ]
        ])
        await callback.message.answer("📋 لطفاً مدت پلن مورد نظرت رو انتخاب کن:", reply_markup=keyboard)
        await callback.answer()
        return


    elif data.startswith("duration_"):
        # مرحله ۲: انتخاب حجم بعد از انتخاب مدت
        duration = int(data.split("_")[1])
        user_choices[callback.from_user.id] = {"duration": duration}

        prices = {
            1: [("30", 110), ("40", 120), ("100", 150)],
            2: [("30", 220), ("40", 240), ("100", 300)],
            3: [("30", 330), ("40", 360), ("100", 450)],
        }

        keyboard_buttons = [
            [
                InlineKeyboardButton(
                    text=f"{size} GB — {price_} هزار تومان",
                    callback_data=f"plan_{duration}_{size}"
                )
            ]
            for size, price_ in prices[duration]
        ]

        keyboard_buttons.append([
            InlineKeyboardButton(text="↩️ بازگشت", callback_data="back_to_duration"),
            InlineKeyboardButton(text="📞 حجم بیشتر → پشتیبانی", url="https://t.me/freeedomarea")
        ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        await callback.answer()                
        await callback.message.delete()       
        await callback.message.answer(
            f"📦 پلن {duration} ماهه انتخاب شد.\nحالا حجم مورد نظرت رو انتخاب کن:",
            reply_markup=keyboard
        )
        
        return


    elif data == "back_to_duration":
        user_choices.pop(callback.from_user.id, None)
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🕒 سه ماهه", callback_data="duration_3"),
                InlineKeyboardButton(text="🕑 دو ماهه", callback_data="duration_2"),
                InlineKeyboardButton(text="🕐 یک ماهه", callback_data="duration_1"),
            ],
            [
                InlineKeyboardButton(text="❌ انصراف", callback_data="cancel_payment")
            ]
        ])
        await callback.answer()                
        await callback.message.delete() 
        await callback.message.answer(
            "🔙 برگشتی به مرحله انتخاب مدت:\nلطفاً مدت مورد نظرت رو دوباره انتخاب کن:",
            reply_markup=keyboard
        )
        return


    elif data.startswith("plan_"):
        # مرحله ۳: انتخاب حجم و درخواست اسم کانفیگ
        _, duration_s, size_s = data.split("_")
        duration = int(duration_s)
        size = int(size_s)

        price_map = {
            (1, 30): 110, (1, 40): 120, (1, 100): 150,
            (2, 30): 220, (2, 40): 240, (2, 100): 300,
            (3, 30): 330, (3, 40): 360, (3, 100): 450,
        }
        price = price_map.get((duration, size), 0)

        user_choices[callback.from_user.id] = {
            "duration": duration,
            "size": size,
            "price": price
        }
        await callback.answer()                
        await callback.message.delete() 
        await callback.message.answer(
            f"📋 پلن انتخاب‌شده:\n"
            f"⏱ مدت: {duration} ماهه\n"
            f"📦 حجم: {size} GB\n"
            f"💰 مبلغ: {price:,} هزار تومان\n\n"
            "📝 لطفاً یه اسم دلخواه برای کانفیگت بنویس:",
            parse_mode="HTML"
        )
        return

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
        user_choices.pop(callback.from_user.id, None)
        await callback.answer()                
        await callback.message.delete() 
        await callback.message.answer("✅ عملیات خرید لغو شد.\nمی‌تونی هر زمان خواستی دوباره از منوی خرید اقدام کنی.")
        
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

@router.callback_query(lambda c: c.data == "back_to_menu")
async def back_to_menu(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.message.answer(
        "🔙 برگشتی به منو!\nیکی از گزینه‌های زیر را انتخاب کن:",
        reply_markup=main_menu_keyboard  # ← همون کیبورد منوی اصلی خودت
    )
    await callback.answer()
@router.message(F.text)
async def handle_config_name(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_choices:
        return  # هیچ انتخاب فعالی نداره
    co_name_valid = message.text.strip()
    if not message.text:
        await message.answer("⚠️ لطفاً فقط متن بنویس (اسم کانفیگ).")
        return
    elif not re.match(r'^[A-Za-z0-9]+$', co_name_valid):
        await message.answer("⚠️ لطفاً فقط از حروف و اعداد انگلیسی استفاده کن، بدون فاصله، خط یا هر چیز دیگه.")
        return
    # ذخیره نام
    user_choices[user_id]["config_name"] = message.text.strip()

    data = user_choices[user_id]
    duration = data["duration"]
    size = data["size"]
    price = data["price"]
    name = data["config_name"]

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 ارسال رسید", callback_data="waiting_for_receipt")],
        [InlineKeyboardButton(text="❌ منصرف شدم", callback_data="cancel_payment")]
    ])
    
    await message.answer(
        f"✅ نام کانفیگ: <b>{name}</b>\n"
        f"⏱ مدت: {duration} ماهه\n"
        f"📦 حجم: {size} گیگ\n"
        f"💰 مبلغ: {price:,} هزار تومان\n\n"
        "حالا لطفاً رسید پرداخت رو ارسال کن:",
        parse_mode="HTML",
        reply_markup=keyboard
    )
