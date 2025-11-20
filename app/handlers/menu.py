from aiogram import Router, types, F
from app.keyboards.main_menu import main_menu_keyboard,request_cooperation_keyboard
from app.services import marzban_api
from app.services.database import get_marzban_accounts_by_user,is_agent,get_plan_price, get_user, add_order , get_marzban_account_by_id,delete_marzban_account
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import re
from app.services.marzban_api import get_user_by_username,delete_user_from_marzban


import os

router = Router()
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))
# حافظه موقت برای نگهداری انتخاب‌های کاربر
user_choices = {}

@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "درود ، به ربات cipher connect خوش اومدی ✨\n\nاینترنت آزاد رو با ما تجربه کنید🌐\n\n🟢 اتصال پایدار و با کیفیت \n\n⚡️پر سرعت با کمترین پینگ\n\n🔒 تضمین اتصال ایمن و مطمئن\n\n⚪️ منصفانه ترین قیمت\n\n⏱ پشتیبانی ۲۴ ساعته\n\nجهت دریافت نمایندگی حتما با پشتیبانی در ارتباط باشید ✅\n\n🆔 @freeedomarea",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(lambda c: not c.data.startswith("order_") )
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
        

        await callback.answer()
        await callback.message.delete()
        await callback.message.answer("📋 لطفاً مدت پلن مورد نظرت رو انتخاب کن:", reply_markup=keyboard)
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
    
    # ⚠️ اینجا ورودی باید telegram_id باشد نه user_id
        accounts = await get_marzban_accounts_by_user(telegram_id)

        if not accounts:
            await callback.answer()
            await callback.message.delete()
            await callback.message.answer("❌ هیچ حسابی برای شما ثبت نشده است.")
            
            return

        keyboard = InlineKeyboardMarkup(inline_keyboard=[])

        for acc in accounts:
            acc_id = acc[0]               # id جدول
            panel_username = acc[2]       # marzban username

            # دریافت لحظه‌ای از پنل
            info = await get_user_by_username(panel_username)
            if not info:
                icon = "🔴"
                remaining = "-"
            else:
                status = info.get("status", "unknown")
                icon = "🟢" if status == "active" else "🔴"

                # محاسبه روزهای باقی مانده
                expire_ts = info.get("expire")
                if expire_ts:
                    from datetime import datetime
                    try:
                        expire_dt = datetime.fromtimestamp(int(expire_ts))
                        remaining = (expire_dt - datetime.now()).days
                    except:
                        remaining = "-"
                else:
                    remaining = "-"

            keyboard.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"{icon} {panel_username}",
                    callback_data=f"show_acc_{acc_id}"
                )
            ])

        # دکمه بازگشت
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_menu")
        ])
        await callback.answer()
        await callback.message.delete()

        await callback.message.answer(
            "🔰 حساب مورد نظر را انتخاب کنید:",
            reply_markup=keyboard
        )
        



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

        acc_id = int(data.replace("show_acc_", ""))   # ← قبلاً username بود

        telegram_id = callback.from_user.id

        accounts = await get_marzban_accounts_by_user(telegram_id)

        account = next((a for a in accounts if a[0] == acc_id), None)

        if not account:
            await callback.answer()
            await callback.message.delete()
            await callback.message.answer("⚠️ حساب مورد نظر یافت نشد.")
            return

        panel_username = account[2]

        info = await get_user_by_username(panel_username)
        if not info:
            await callback.answer()
            await callback.message.delete()
            await callback.message.answer("❌ دریافت اطلاعات از سرور ممکن نشد.")
            return

        status = info.get("status", "unknown")
        status_icon = "🟢 فعال" if status == "active" else "🔴 غیرفعال"

        used = info.get("used_traffic", 0)
        used_gb = round(used / (1024 ** 3), 2)

        data_limit = info.get("data_limit")
        limit_gb = round(data_limit / (1024 ** 3), 2) if data_limit else "∞"
        created_at = info.get("created_at")
        expire_ts = info.get("expire")
        
        
            
        
        if expire_ts:
            from datetime import datetime
            expire_dt = datetime.fromtimestamp(expire_ts)
            expire_str = expire_dt.strftime("%Y-%m-%d %H:%M")
            remaining_days = (expire_dt - datetime.now()).days
        else:
            remaining_days = "∞"
            expire_str = "∞"
        if data_limit: 
            remaining_gb = round(limit_gb - used_gb, 2)
        else:
            remaining_gb = "∞"
        if created_at:
            created_str = created_at.replace("T", " ").split(".")[0]
        else:
            created_str = "نامشخص"
        links = info.get("subscription_url")
        sub_link = links if links else "❌ لینک موجود نیست"

        kb = [
        [
            InlineKeyboardButton(text=panel_username, callback_data="none"),
            InlineKeyboardButton(text=":نام پلن", callback_data="none")
            
        ],
        [
            InlineKeyboardButton(text=created_str, callback_data="none"),
            InlineKeyboardButton(text=":تاریخ خرید", callback_data="none")
        ],
        [
            InlineKeyboardButton(text=expire_str, callback_data="none"),
            InlineKeyboardButton(text=":تاریخ انقضا", callback_data="none")
        ],
        [
            InlineKeyboardButton(text=f"{remaining_gb} GB", callback_data="none"),
            InlineKeyboardButton(text=":حجم باقی‌مانده", callback_data="none")
            
        ],
        [
            InlineKeyboardButton(text=f"{used_gb} GB", callback_data="none"),
            InlineKeyboardButton(text=":حجم مصرفی", callback_data="none")
            
        ],
        [
            InlineKeyboardButton(text="🔄 تمدید سرویس", callback_data=f"renew_acc_{acc_id}")
        ],
        [
            InlineKeyboardButton(text="🗑 حذف کانفیگ", callback_data=f"delete_acc_{acc_id}")
        ],
        [
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="my_configs")
        ]
        ]

        keyboard = InlineKeyboardMarkup(inline_keyboard=kb)
        # پیام نهایی:
        text = (
            f"👤 <b>{panel_username}</b>\n"
            f"📊 وضعیت: {status_icon}\n"
            f"📦 مصرف: {used_gb} GB از {limit_gb} GB\n"
            f"⏱ روزهای باقی‌مانده: {remaining_days}\n\n"
            f"🔗 <b>لینک اتصال:</b>\n"
            f"<code>{sub_link}</code>"
        )
        await callback.answer()
        await callback.message.delete()
        await callback.message.answer(text, parse_mode="HTML", reply_markup=keyboard)
        

    elif data.startswith("renew_acc_"):
        acc_id = int(data.replace("renew_acc_", ""))
        telegram_id = callback.from_user.id

        # پاک کردن کیبورد پیام قبلی (تا دوباره روی دکمه زده نشه)
        try:
            await callback.message.delete()
        except:
            try:
                await callback.message.edit_reply_markup(reply_markup=None)
            except:
                pass

        await callback.answer()

        # --- 1) گرفتن رکورد حساب از دیتابیس (تو تابعت احتمالا موجوده) ---
        # فرض می‌کنم تابعی مثل get_marzban_account_by_id داری؛ اگر نداری بگو تا اضافه کنم
        account = await get_marzban_account_by_id(acc_id)
        if not account:
            await callback.message.answer("⚠️ حساب مورد نظر یافت نشد.")
            return

        panel_username = account[2]   
        plan_months = int(account[8]) if account[8] is not None else None
        plan_size_gb = float(account[9]) if account[9] is not None else None
        

        if not plan_months or not plan_size_gb:
            # اگر اطلاعات پلن ذخیره نشده، بهتره از orders یا config_name استخراج کنیم یا خطا بدیم
            await callback.message.answer("⚠️ اطلاعات پلن قبلی ناقص است. امکان تمدید اتومات وجود ندارد.")
            return

        plan_price = await get_plan_price(int(plan_size_gb), int(plan_months))

        if not plan_price:
            await callback.message.answer("⚠️ خطا: قیمت پلن تمدید پیدا نشد. با پشتیبانی تماس بگیرید.")
            return

        marzban_user = await get_user_by_username(panel_username)
        if not marzban_user:
            await callback.message.answer("❌ خطا در دریافت اطلاعات از پنل مرزبان.")
            return
        # ذخیره اطلاعات تمدید در user_choices، مثل خرید اولیه
        user_choices[telegram_id] = {
            "action": "renew",
            "acc_id": acc_id,
            "config_name": panel_username,
            "duration": plan_months,
            "size": plan_size_gb,
            "price": plan_price
        }

        await callback.message.answer(
            f"💳 مبلغ تمدید: {plan_price:,} هزار تومان\n"
            "لطفاً رسید پرداخت را ارسال کنید.",
        )

    elif data.startswith("delete_acc_"):
        acc_id = int(data.split("_", 2)[2])

        # پاک کردن دکمه‌های قبلی
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except:
            pass

        await callback.answer()

        # پیام تأیید
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ لغو", callback_data="cancel_delete"),
                InlineKeyboardButton(text="🗑 حذف نهایی", callback_data=f"confirm_delete_{acc_id}")
            ]
        ])

        await callback.message.answer(
            "⚠️ آیا از حذف این کانفیگ مطمئن هستید؟\nاین عملیات غیرقابل بازگشت است.\nفقط اگر کمتر از یک روز از خرید شما گذشته باشد،\n اکانت شما به اندازه مبلغ پرداختی شارژ میشود(پس از ارتباط با پشتیبانی!)",
            reply_markup=kb
        )
    elif data == "cancel_delete":
        try:
            await callback.message.delete()
        except:
            await callback.message.edit_reply_markup(None)

        await callback.answer("❎ حذف لغو شد.")

    elif data.startswith("confirm_delete_"):
        acc_id = int(data.split("_", 2)[2])

        # حذف پیام تایید
        try:
            await callback.message.delete()
        except:
            pass

        await callback.answer()

        # گرفتن رکورد از دیتابیس
        account = await get_marzban_account_by_id(acc_id)
        if not account:
            await callback.message.answer("❌ حساب پیدا نشد.")
            return
        tg_id = account[1]
        panel_username = account[2]   # username در مرزبان

        # --- حذف از پنل ---
        ok = await delete_user_from_marzban(panel_username)
        if not ok:
            await callback.message.answer("❌ خطا در حذف از پنل مرزبان.")
            return
        
        # --- حذف از دیتابیس ---
        await delete_marzban_account(acc_id)
        userinforaw = await get_user(tg_id)
        username = userinforaw[2]
        firstname = userinforaw[3]

        await callback.bot.send_message(
            LOG_CHANNEL_ID,
            f"کاربر <a href='tg://user?id={tg_id}'>{firstname}</a> با آیدی {username} حساب(کانفیگ) {panel_username} را حذف کرد.",
            parse_mode="HTML",
        )
        # پیام موفقیت
        await callback.message.answer(
            "🗑 کانفیگ با موفقیت حذف شد. برای بررسی بازگشت وجه به کیف پولتان به پشتیبانی پیام دهید.",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 بازگشت", callback_data="my_configs")],
                [InlineKeyboardButton(text="🏠 منو", callback_data="back_to_menu")]
            ])
        )

    elif data == "agent_panel":
        tg_id = callback.from_user.id
        is_agent_bo = await is_agent(tg_id)
        if not is_agent_bo:
            await callback.message.edit_text(
                "شما در لیست نمایندگان نیستید.\n"
                "در صورت تمایل برای همکاری دکمه زیر را بزنید:",
                reply_markup=request_cooperation_keyboard()
            )
        else:
            # placeholder for agent panel
            await callback.message.edit_text(
                "🎉 پنل نمایندگی شما آماده است.\n(بعداً این بخش را تکمیل می‌کنیم.)"
            )
    elif data == "request_agent":
        await callback.answer("درخواست شما ثبت شد. منتظر تایید ادمین باشید.", show_alert=False)

    elif data == "back_to_menu":
        await callback.message.delete()
        await callback.message.answer(
            "🔙 برگشتی به منو! Cipher Connect آماده همراهی شماست.🟢\nیکی از گزینه‌های زیر را انتخاب کن:",
            reply_markup=main_menu_keyboard()  # ← همون کیبورد منوی اصلی خودت
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
