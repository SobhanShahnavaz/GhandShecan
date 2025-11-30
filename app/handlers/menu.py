from aiogram import Router, types, F
from app.keyboards.main_menu import main_menu_keyboard,request_cooperation_keyboard,agent_menu_keyboard
from app.keyboards.admin_menu import admin_menu_keyboard
from app.services import marzban_api
from app.services.database import add_order , get_marzban_account_by_id,delete_marzban_account,list_agent_requests
from app.services.database import get_marzban_accounts_by_user,get_agent,get_plan_price_by_DMA, get_user,add_agent_request
from app.services.database import add_agent, delete_agent_request, add_agent_stats, get_agent_stats, is_agent
from app.services.database import get_plans,delete_plan,add_plan,get_available_months,get_sizes_for_month,get_plan_by_id
from app.services.database import count_test_accounts,add_test_account,get_all_test_usernames
from app.services.database import get_all_cards,add_card,get_active_card,activate_card
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import re
from app.services.marzban_api import get_user_by_username,delete_user_from_marzban,delete_disabled_tests_in_marzban,create_Test_in_marzban
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
import math
import os
from MessageAddresses import ANDROID_HELP_MESSAGE_Url

router = Router()
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))
SUPPORT_ACC_ID = int(os.getenv("SUPPORT_ACC_ID"))

ANDROID_HELP_MESSAGE_URL =ANDROID_HELP_MESSAGE_Url
# حافظه موقت برای نگهداری انتخاب‌های کاربر
user_choices = {}
def tehran_now():
    return datetime.now(ZoneInfo("Asia/Tehran"))

@router.callback_query(F.data == "main_menu")
async def show_main_menu(callback: types.CallbackQuery):
    telegram_id = callback.from_user.id
    isAgent = await is_agent(telegram_id)
    if isAgent:
        await callback.message.edit_text(
            "درود ، به ربات cipher connect خوش اومدی ✨\n\nاینترنت آزاد رو با ما تجربه کنید🌐\n\n🟢 اتصال پایدار و با کیفیت \n\n⚡️پر سرعت با کمترین پینگ\n\n🔒 تضمین اتصال ایمن و مطمئن\n\n⚪️ منصفانه ترین قیمت\n\n⏱ پشتیبانی ۲۴ ساعته\n\nجهت دریافت نمایندگی حتما با پشتیبانی در ارتباط باشید ✅\n\n🆔 @freeedomarea",
            reply_markup=agent_menu_keyboard()
        )
        await callback.answer()
    else:
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
        telegram_id = callback.from_user.id

        # Detect if user is agent or normal user
        is_agent_user = await is_agent(telegram_id)
        for_agent = 1 if is_agent_user else 0

        months_list = await get_available_months(for_agent)

        if not months_list:
            await callback.message.edit_text("⚠️ هیچ پلنی موجود نیست.")
            return

        kb = InlineKeyboardMarkup(inline_keyboard=[])

        for m in months_list:
            kb.inline_keyboard.append([
                InlineKeyboardButton(text=f"{m} ماهه", callback_data=f"duration_{m}")
            ])

        kb.inline_keyboard.append([
            InlineKeyboardButton(text="❌ انصراف", callback_data="cancel_payment")
        ])

        user_choices[telegram_id] = {"action": "choose_duration", "for_agent": for_agent}

        await callback.message.edit_text("⏱ لطفاً مدت سرویس را انتخاب کنید:", reply_markup=kb)

    
    elif data.startswith("duration_"):
        telegram_id = callback.from_user.id

        if "action" not in user_choices.get(telegram_id, {}):
            return

        months = int(data.split("_")[1])
        for_agent = user_choices[telegram_id]["for_agent"]

        plans = await get_sizes_for_month(months, for_agent)

        if not plans:
            await callback.message.edit_text("⚠️ هیچ پلنی با این مدت وجود ندارد.")
            return
    
         # NEW: show user limit selection before plan selection
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="تک کاربر", callback_data="limit_1")],
            [InlineKeyboardButton(text="3 کاربر", callback_data="limit_3")],
            [InlineKeyboardButton(text="5 کاربر", callback_data="limit_5")],
            [InlineKeyboardButton(text="🔙 بازگشت", callback_data="buy_config")]
        ])
        user_choices[telegram_id] = {
            "action": "choose_limit",
            "for_agent": for_agent,
            "months": months
        }
        await callback.message.edit_text(
        "👥 تعداد کاربران همزمان را انتخاب کنید:",
        reply_markup=kb
    )
    
    
    
    elif data.startswith("limit_"):
        telegram_id = callback.from_user.id
        limit = int(data.split("_")[1])
        
           
        if limit == 3:
            multiplier = 2
        elif limit == 5:
            multiplier = 3
        else:
            multiplier = 1
        if "action" not in user_choices.get(telegram_id, {}):
            return

        months = user_choices[telegram_id]["months"]
        for_agent = user_choices[telegram_id]["for_agent"]

        plans = await get_sizes_for_month(months, for_agent)
        kb = InlineKeyboardMarkup(inline_keyboard=[])

        for plan_id, data_gb, price in plans:
            kb.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"{data_gb * multiplier}GB - {price * multiplier:,} تومان",
                    callback_data=f"plan_{plan_id}"
                )
            ])

        kb.inline_keyboard.append([
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="buy_config"),
            InlineKeyboardButton(text="📞 حجم بیشتر → پشتیبانی", url="https://t.me/freeedomarea")
        ])
        
        user_choices[telegram_id] = {
            "action": "choose_size",
            "for_agent": for_agent,
            "months": months,
            "user_limit" :limit
        }

        await callback.message.edit_text(
            f"📦 حجم مورد نظر برای پلن {months} ماهه {limit} کاربره را انتخاب کنید:",
            reply_markup=kb
        )


    elif data.startswith("plan_"):
        telegram_id = callback.from_user.id
        plan_id = int(data.split("_")[1])

        plan = await get_plan_by_id(plan_id)
        if not plan:
            await callback.message.answer("⚠️ پلن یافت نشد.")
            return

        _, data_gb, months, price, for_agent = plan
        
        
        limit = user_choices[telegram_id]["user_limit"]
        if limit == 3:
            Max_Dev = "سه"
            multiplier = 2
        elif limit == 5:
            Max_Dev = "پنج"
            multiplier = 3
        else:
            Max_Dev = "تک"
            multiplier = 1
        user_choices[telegram_id] = {
            "action": "buy",
            "duration": months,
            "size": data_gb*multiplier,
            "price": price*multiplier,
            "plan_id": plan_id,
            "is_agent":for_agent,
            "user_limit" :limit,
            "max_device":Max_Dev
        }

        await callback.message.edit_text(
            f"📋 پلن انتخاب‌شده:{Max_Dev} کاربره\n"
            f"⏱ مدت: {months} ماهه\n"
            f"📦 حجم: {data_gb*multiplier} GB\n"
            f"💰 مبلغ: {multiplier*price:,} هزار تومان\n\n"   
            "📝 لطفاً یک نام انگلیسی برای کانفیگ وارد کنید:(بیش از 2 حرف داشته باشد)",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="❌ لغو", callback_data="cancel_payment")]]
            )
        )


    elif data == "my_configs":
        telegram_id = callback.from_user.id
    
    # ⚠️ اینجا ورودی باید telegram_id باشد نه user_id
        accounts = await get_marzban_accounts_by_user(telegram_id)
        backkeyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="back_to_menu_without_del")]
            ])
        if not accounts:
            await callback.answer()
            await callback.message.delete()
            await callback.message.answer("❌ هیچ حسابی برای شما ثبت نشده است.",reply_markup=backkeyboard)
            
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
                    
                    try:
                        expire_dt = datetime.fromtimestamp(int(expire_ts), ZoneInfo("Asia/Tehran"))
                        remaining = (expire_dt - tehran_now()).days
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
        telegram_id = callback.from_user.id

        agent = await is_agent(telegram_id)
        is_agent_flag = 1 if agent else 0

        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="⬇️ دریافت اکانت",  callback_data="recieve_test_account")],
                [InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="back_to_menu")]
            ])

        if agent:
            await callback.message.edit_text(
                "نماینده عزیز، شما میتوانید 5 عدد اکانت تست در روز دریافت کنید.\nهر اکانت یک گیگابایت حجم و 5 ساعت زمان دارد.",
                reply_markup=keyboard
            )
        else:
            await callback.message.edit_text(
                "کاربر عزیز، شما میتوانید 2 عدد اکانت تست در ماه دریافت کنید.\nهر اکانت یک گیگابایت حجم و 1 ساعت زمان دارد.",
                reply_markup=keyboard
            )



    elif data == "recieve_test_account":
        telegram_id = callback.from_user.id

        agent = await is_agent(telegram_id)
        is_agent_flag = 1 if agent else 0

        current_count = await count_test_accounts(telegram_id, is_agent_flag)

        # LIMITS
        if agent:
            limit = 5  # daily
        else:
            limit = 2  # monthly
        
        
        if current_count >= limit:
            if agent:
                await callback.answer(
                    "⛔️ سقف دریافت اکانت تست امروز پر شده است. (۵ تا در روز)",
                    show_alert=True
                )
            else:
                await callback.answer(
                    "⛔️ سقف دریافت اکانت تست این ماه پر شده است. (۲ تا در ماه)",
                    show_alert=True
                )
            return
        

        # Otherwise allowed!
        
        user = await get_user(telegram_id)

        # Determine username
        username = callback.from_user.username
        tg_phonenum = user[5] if isinstance(user, (list, tuple)) else user["phone_number"]

        base = username if username else tg_phonenum if tg_phonenum else f"user{telegram_id}"

        number = current_count + 1

        # Username format: <base>-Test<number>
        test_username = f"{base}-Test{number}"
        
        # Register the attempt 
        await add_test_account(telegram_id,test_username, is_agent_flag)
        # Duration differs
        if agent:
            duration_hours = 5
        else:
            duration_hours = 1

        try:
            sub_link = await create_Test_in_marzban(test_username, duration_hours)
        except Exception as e:
            await callback.message.answer(f"❌ خطا در ساخت اکانت تست:\n{e}")
            return

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📘 نحوه استفاده از لینک", url=ANDROID_HELP_MESSAGE_URL)],
                [InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="back_to_menu_without_del")]
            ])
        
        msg = (
            "🧪 <b>اکانت تست شما ساخته شد!</b>\n\n"
            f"ℹ️ توجه داشته باشید که اکانت تست در منوی کانفیگ های من نمایش داده نمیشود.\n"
            f"⏳ <b>مدت اعتبار:</b> {duration_hours} ساعت\n"
            f"📦 <b>حجم:</b> 1 گیگابایت\n\n"
            f"🔗 <b>لینک سابسکریبشن:</b>\n<code>{sub_link}</code>\n\n"
            "آموزش استفاده:"
            
        )

        await callback.message.answer(msg, parse_mode="HTML",reply_markup=keyboard)



    elif data == "wallet":
        await callback.answer("💰 مدیریت کیف پول به‌زودی فعال می‌شود!", show_alert=True)

    elif data == "profile":
        await callback.answer("👤 نمایش مشخصات کاربری در حال آماده‌سازی است.", show_alert=True)

    elif data == "apps":
        await callback.answer("📲 نصب برنامه‌ها به‌زودی اضافه می‌شود!", show_alert=True)

    elif data == "support":
        sup_link = SUPPORT_ACC_ID
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📫 ارتباط با پشتیبان", url=f"tg://user?id={sup_link}")],
                [InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="back_to_menu")]
            ])
        await callback.message.edit_text("با زدن روی لینک زیر میتوانید با پشتیبانی در ارتباط باشید.",
        parse_mode="HTML",
        reply_markup=keyboard)

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
        card = await get_active_card()
        card_number = card[2]
        card_owner = card[3]
        await callback.message.answer(
            "📸 لطفاً تصویر رسید پرداخت خود را ارسال کنید.\n\n"
            f"📸 <code>{card_number}</code>\n {card_owner} \n" #this will be payment card and the name.
            "در صورت لغو، از منوی اصلی گزینه‌ی دیگری را انتخاب کنید.",
            parse_mode="HTML"
        )
        await callback.answer()


    elif data.startswith("show_acc_"):

        acc_id = int(data.replace("show_acc_", ""))   # ← قبلاً username بود

        telegram_id = callback.from_user.id

        accounts = await get_marzban_accounts_by_user(telegram_id)

        account = next((a for a in accounts if a[0] == acc_id), None)
        backkeyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="back_to_menu_without_del")]
            ])
        if not account:
            await callback.answer()
            await callback.message.delete()
            await callback.message.answer("⚠️ حساب مورد نظر یافت نشد.", reply_markup= backkeyboard)
            return
        
        panel_username = account[2]

        info = await get_user_by_username(panel_username)
        if not info:
            await callback.answer()
            await callback.message.delete()
            await callback.message.answer("❌ دریافت اطلاعات از سرور ممکن نشد.", reply_markup= backkeyboard)
            return

        status = info.get("status", "unknown")
        status_icon = "🟢 فعال" if status == "active" else "🔴 غیرفعال"

        used = info.get("used_traffic", 0)
        used_gb = round(used / (1024 ** 3), 2)

        data_limit = info.get("data_limit")
        limit_gb = round(data_limit / (1024 ** 3), 2) if data_limit else "∞"
        created_at = info.get("created_at")
        expire_ts = info.get("expire")
        dt = datetime.fromisoformat(created_at)
        dt_utc = dt.replace(tzinfo=timezone.utc)
        created_at_tehran = dt_utc.astimezone(ZoneInfo("Asia/Tehran"))
        
            
        
        if expire_ts:
            
            expire_dt = datetime.fromtimestamp(expire_ts, ZoneInfo("Asia/Tehran"))
            expire_str = expire_dt.strftime("%Y-%m-%d %H:%M")
            remaining_days = (expire_dt - tehran_now()).days
        else:
            remaining_days = "∞"
            expire_str = "∞"
        if data_limit: 
            remaining_gb = round(limit_gb - used_gb, 2)
        else:
            remaining_gb = "∞"
        if created_at_tehran:
            created_str = created_at_tehran.strftime("%Y-%m-%d %H:%M")
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
            InlineKeyboardButton(text="➕ افزودن حجم", callback_data=f"add_data_{acc_id}")
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
        
    elif data.startswith("add_data_"):
        acc_id = int(data.split("_")[2])
        telegram_id = callback.from_user.id

        try:
            await callback.message.delete()
        except:
            pass

        await callback.answer()

        account = await get_marzban_account_by_id(acc_id)
        if not account:
            await callback.message.answer("⚠️ حساب مورد نظر یافت نشد.")
            return

        panel_username = account[2]

        # store user choice
        user_choices[telegram_id] = {
            "action": "add_data",
            "acc_id": acc_id,
            "config_name": panel_username
        }

        # Ask the user how much data they want
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="10GB - 15 هزار تومان", callback_data="adddata_10"),
            ],
            [
                InlineKeyboardButton(text="50GB - 60 هزار تومان", callback_data="adddata_50"),
            ],
            [
                InlineKeyboardButton(text="❌ لغو", callback_data="cancel_payment")
            ]
        ])

        await callback.message.answer(
            f"چقدر حجم می‌خوای اضافه کنی برای {panel_username}؟",
            reply_markup=kb
        )
    elif data.startswith("adddata_"):
        telegram_id = callback.from_user.id
        if telegram_id not in user_choices:
            await callback.message.answer("⚠️ مشکلی پیش آمد. دوباره تلاش کنید.")
            return

        gb = int(data.split("_")[1])

        price_map = {
            10: 15,
            50: 60
        }
        price = price_map.get(gb)

        user_choices[telegram_id]["size"] = gb
        user_choices[telegram_id]["price"] = price

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 انتقال به کارت", callback_data="waiting_for_receipt")],
            [InlineKeyboardButton(text="❌ منصرف شدم", callback_data="cancel_payment")]
        ])
        await callback.message.answer(
            f"📌 حجم انتخاب‌شده: {gb}GB\n"
            f"💰 مبلغ: {price:,} هزار تومان\n\n"
            "خب، روش پرداختت رو انتخاب کن",
            reply_markup=kb,

        )

    elif data.startswith("renew_acc_"):
        acc_id = int(data.replace("renew_acc_", ""))
        telegram_id = callback.from_user.id
        is_agent_user = await is_agent(telegram_id)
        for_agent = 1 if is_agent_user else 0

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
        user_limit = float(account[10]) if account[10] is not None else None
        if user_limit == 3:
            mdtext = "سه"
            multip =2 
        elif user_limit == 5:
            multip =3
            mdtext = "پنج"
        else:
            multip =1
            mdtext = "تک"
        if not plan_months or not plan_size_gb:
            # اگر اطلاعات پلن ذخیره نشده، بهتره از orders یا config_name استخراج کنیم یا خطا بدیم
            await callback.message.answer("⚠️ اطلاعات پلن قبلی ناقص است. امکان تمدید اتومات وجود ندارد.")
            return

        plan_price = await get_plan_price_by_DMA(int(plan_size_gb/multip), int(plan_months), int(for_agent))

        if not plan_price:
            await callback.message.answer("⚠️ خطا: قیمت پلن تمدید پیدا نشد. با پشتیبانی تماس بگیرید.")
            return

        marzban_user = await get_user_by_username(panel_username)
        if not marzban_user:
            await callback.message.answer("❌ خطا در دریافت اطلاعات از پنل مرزبان.")
            return
        plan_price = plan_price*multip
        # ذخیره اطلاعات تمدید در user_choices، مثل خرید اولیه
        user_choices[telegram_id] = {
            "action": "renew",
            "acc_id": acc_id,
            "config_name": panel_username,
            "duration": plan_months,
            "size": plan_size_gb,
            "price": plan_price,
            "is_agent": for_agent,
            "user_limit" : user_limit,
            "max_device" : mdtext

        }
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 انتقال به کارت", callback_data="waiting_for_receipt")],
            [InlineKeyboardButton(text="❌ منصرف شدم", callback_data="cancel_payment")]
        ])

        await callback.message.answer(
            f"💳 مبلغ تمدید: {plan_price:,} هزار تومان\n"
            "لطفاً روش پرداخت را انتخاب کنید.",
            reply_markup=kb,
            parse_mode="HTML"
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

        # Check if agent
        agent = await get_agent(tg_id)
        if not agent:
            # Not agent → show request button
            await callback.message.edit_text(
                "شما هنوز نماینده نیستید.\nبرای درخواست همکاری روی دکمه زیر کلیک کنید.",
                reply_markup=request_cooperation_keyboard()
            )
            return

        # Get stats
        stats = await get_agent_stats(tg_id)
        user = await get_user(tg_id)  # برای گرفتن تاریخ ثبت‌نام

        # Extract values (fall back to 0 / N/A)
        number_of_buys = stats[3] if stats else 0
        total_income = stats[4] if stats else 0
        sum_buy_prices = stats[5] if stats else 0
        sum_of_data_added = stats[8] if stats else 0
        sum_of_gb_added = stats[9] if stats else 0
        sum_renew_prices = stats[6] if stats else 0
        approved_date = stats[7] if stats else "N/A"

        register_date = user[6] if user else "N/A"
        
        if total_income>999:
            Million = math.floor(total_income/1000)
            Thousand = total_income - (Million*1000)
            text_total_income = f"{Million} میلیون و {Thousand}"
        else:
            text_total_income =f"{total_income} هزار تومان"
        
        if sum_buy_prices>999:
            Million = math.floor(sum_buy_prices/1000)
            Thousand = sum_buy_prices - (Million*1000)
            text_sum_buy_prices = f"{Million} میلیون و {Thousand}"
        else:
            text_sum_buy_prices =f"{sum_buy_prices} هزار تومان"
        
        if sum_of_data_added>999:
            Million = math.floor(sum_of_data_added/1000)
            Thousand = sum_of_data_added - (Million*1000)
            text_sum_of_data_added = f"{Million} میلیون و {Thousand}"
        else:
            text_sum_of_data_added =f"{sum_of_data_added} هزار تومان"
        
        if sum_renew_prices>999:
            Million = math.floor(sum_renew_prices/1000)
            Thousand = sum_renew_prices - (Million*1000)
            text_sum_renew_prices = f"{Million} میلیون و {Thousand}"
        else:
            text_sum_renew_prices =f"{sum_renew_prices} هزار تومان"
           
        

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=str(number_of_buys), callback_data="noop"),
                InlineKeyboardButton(text="تعداد خرید", callback_data="noop")
                
            ],
            [
                InlineKeyboardButton(text=f"{text_total_income}", callback_data="noop"),
                InlineKeyboardButton(text="درآمد کل", callback_data="noop")
            ],
            [
                InlineKeyboardButton(text=f"{text_sum_buy_prices}", callback_data="noop"),
                InlineKeyboardButton(text="جمع خریدها", callback_data="noop")
            ],
            [
                InlineKeyboardButton(text=f"{sum_of_gb_added}", callback_data="noop"),
                InlineKeyboardButton(text="حجم اضافه شده", callback_data="noop")
            ],
            [
                InlineKeyboardButton(text=f"{text_sum_of_data_added}", callback_data="noop"),
                InlineKeyboardButton(text="مبلغ حجم اضافه شده", callback_data="noop")
            ],
            [
                InlineKeyboardButton(text=f"{text_sum_renew_prices}", callback_data="noop"),
                InlineKeyboardButton(text="جمع تمدیدها", callback_data="noop")
            ],
            [
                InlineKeyboardButton(text=str(register_date), callback_data="noop"),
                InlineKeyboardButton(text="تاریخ عضویت", callback_data="noop")
            ],
            [
                InlineKeyboardButton(text=str(approved_date), callback_data="noop"),
                InlineKeyboardButton(text="تاریخ تایید", callback_data="noop")
            ],
            [
                InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="back_to_menu")
            ]
        ])

        await callback.message.edit_text(
            "📊 *پنل نمایندگی*\n\nاینجا اطلاعات و آمار نمایندگی شما نمایش داده می‌شود.",
            reply_markup=kb,
            parse_mode="Markdown"
        )


    elif data == "request_agent":
        await add_agent_request(callback.from_user)

        await callback.message.edit_text("درخواست شما برای ادمین ارسال شد.")
        keyb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="مشاهده درخواست‌ها",callback_data="view_agent_requests")]])
        # notify admin
        await callback.bot.send_message(
            ADMIN_ID,
            f"درخواست همکاری جدید:\n"
            f"@{callback.from_user.username}\n"
            f"ID: {callback.from_user.id}",
            reply_markup= keyb
        )
    
    elif data == "view_agent_requests":
        requests = await list_agent_requests()
        
        if not requests:
            await callback.message.edit_text("هیچ درخواست همکاری در انتظار تایید نیست.")
            return

        kb = InlineKeyboardMarkup(inline_keyboard=[])

        for req in requests:
            tg_id = req[1]
            name =  req[2]

            kb.inline_keyboard.append([
                InlineKeyboardButton(
                    text=f"✔ تایید {name}",
                    callback_data=f"approve_agent_{tg_id}"
                ),
                InlineKeyboardButton(
                    text=f"❌ رد {name}",
                    callback_data=f"reject_agent_{tg_id}"
                )
            ])

        await callback.message.edit_text("درخواست‌های در انتظار:", reply_markup=kb)


    elif data.startswith("approve_agent_"):
        tg_id = int(data.split("_")[2])

        # Fetch request
        requests = await  list_agent_requests()
        req = next((r for r in requests if r[1] == tg_id), None)

        if not req:
            await callback.answer("این درخواست دیگر وجود ندارد.", show_alert=True)
            return

        # Add user to agents table
        await add_agent(
            telegram_id=req[1],
            username=req[2],
            first_name=req[3],
            last_name=req[4],
            phone_number=None,
            is_joined=1,
        )
        await add_agent_stats(
            telegram_id=req[1],
            username= req[2]
        )

        # Remove pending request
        await delete_agent_request(tg_id)

        await callback.answer("نماینده با موفقیت اضافه شد.", show_alert=True)

        await callback.message.edit_text("نماینده تایید شد ✔")
        
        # notify the agent
        await callback.bot.send_message(
            tg_id,
            "درخواست همکاری شما تایید شد!\n"
            "اکنون شما به عنوان نماینده ثبت شده‌اید."
        )
    
    elif data.startswith("reject_agent_"):
        tg_id = int(data.split("_")[2])

        # Remove request from DB
        await delete_agent_request(tg_id)

        await callback.answer("درخواست رد شد.", show_alert=True)

        await callback.message.edit_text("درخواست همکاری رد شد ❌")

        # notify user
        try:
            await callback.bot.send_message(
                tg_id,
                "درخواست همکاری شما توسط ادمین رد شد."
            )
        except:
            pass
    
    elif data == "back_to_menu_without_del":
        telegram_id = callback.from_user.id
        isAgent = await is_agent(telegram_id)
        if isAgent:
            await callback.message.answer(
                "🔙 برگشتی به منو! Cipher Connect آماده همراهی شماست.🟢\nیکی از گزینه‌های زیر را انتخاب کن:",
                reply_markup=agent_menu_keyboard()  # ← همون کیبورد منوی اصلی خودت
            )
            await callback.answer()
        else:
            await callback.message.answer(
                "🔙 برگشتی به منو! Cipher Connect آماده همراهی شماست.🟢\nیکی از گزینه‌های زیر را انتخاب کن:",
                reply_markup=main_menu_keyboard()  # ← همون کیبورد منوی اصلی خودت
            )
            await callback.answer()


    elif data == "back_to_menu":
        telegram_id = callback.from_user.id
        isAgent = await is_agent(telegram_id)
        await callback.message.delete()
        if isAgent:
            await callback.message.answer(
                "🔙 برگشتی به منو! Cipher Connect آماده همراهی شماست.🟢\nیکی از گزینه‌های زیر را انتخاب کن:",
                reply_markup=agent_menu_keyboard()  # ← همون کیبورد منوی اصلی خودت
            )
            await callback.answer()
        else:
            await callback.message.answer(
                "🔙 برگشتی به منو! Cipher Connect آماده همراهی شماست.🟢\nیکی از گزینه‌های زیر را انتخاب کن:",
                reply_markup=main_menu_keyboard()  # ← همون کیبورد منوی اصلی خودت
            )
            await callback.answer()

    elif data == "admin_show_plans":
        plans = await get_plans()

        if not plans:
            await callback.message.edit_text("⚠️ هیچ پلنی ثبت نشده است.")
            return

        kb = InlineKeyboardMarkup(inline_keyboard=[])

        # Header row
        kb.inline_keyboard.append([
            InlineKeyboardButton(text="حجم", callback_data="none"),
            InlineKeyboardButton(text="مدت", callback_data="none"),
            InlineKeyboardButton(text="قیمت", callback_data="none"),
            InlineKeyboardButton(text="هدف", callback_data="none"),
            InlineKeyboardButton(text="حذف", callback_data="none"),
        ])

        for p in plans:
            plan_id, data_gb, months, price, for_agent = p
            if for_agent:
                cust = "همکار"
            else:
                cust = "کاربر"
            kb.inline_keyboard.append([
                InlineKeyboardButton(text=f"{data_gb}GB", callback_data="none"),
                InlineKeyboardButton(text=f"{months} ماه", callback_data="none"),
                InlineKeyboardButton(text=f"{price:,}", callback_data="none"),
                InlineKeyboardButton(text=f"{cust}", callback_data="none"),
                InlineKeyboardButton(text="❌", callback_data=f"delplan_{plan_id}")
            ])

        kb.inline_keyboard.append([
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="axtar_menu")
        ])

        await callback.message.edit_text("📦 لیست پلن‌های که برای فروش تعریف شده است:", reply_markup=kb)
    
    
    elif data.startswith("delplan_"):
        plan_id = int(data.split("_")[1])

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✔ حذف", callback_data=f"deleplan_confirm_{plan_id}")
            ],
            [
                InlineKeyboardButton(text="❌ انصراف", callback_data="admin_show_plans")
            ]
        ])

        await callback.message.edit_text(
            f"آیا از حذف پلن {plan_id} مطمئن هستید؟",
            reply_markup=keyboard
        )
    elif data.startswith("deleplan_confirm_"):
        plan_id = int(data.split("_")[2])

        await delete_plan(plan_id)

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔙 بازگشت", callback_data="admin_show_plans")
            ]
        ])

        await callback.message.edit_text(
            f"✔ پلن {plan_id} با موفقیت حذف شد.",
            reply_markup=kb
        )
    elif data == "admin_add_plan":
        admin_user = callback.from_user.id
        user_choices[admin_user] = {"action": "adding_plan", "step": 1}

        await callback.message.edit_text(
            "🔢 مقدار حجم پلن را به گیگابایت وارد کنید:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="❌ لغو", callback_data="axtar_menu")]]
            )
        )
    
    elif data == "admin_manage_cards":
        admin_user = callback.from_user.id
        admin_name = callback.from_user.first_name

        await callback.message.edit_text(
            f"چه کاری مد نظرتان است {admin_name} عزیز؟",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                [InlineKeyboardButton(text="📁 مشاهده کارت ها", callback_data="none")],
                [InlineKeyboardButton(text="📥 افزودن کارت جدید", callback_data="admin_add_card")],
                [InlineKeyboardButton(text="💳 تغییر کارت فعال", callback_data="admin_change_card")],
                [InlineKeyboardButton(text="🔙 بازگشت", callback_data="axtar_menu")]
            ]
            )
        )

    elif data == "admin_add_card":
        admin_user = callback.from_user.id
        user_choices[admin_user] = {"action": "adding_card", "step": 1}

        await callback.message.edit_text(
            "🏷 یک لیبل برای کارت بنویسید(فقط به شما نمایش داده میشود):\n مثال:ملت من، بلوبانک دو.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="❌ لغو", callback_data="axtar_menu")]]
            )
        )
    
    
    elif data == "admin_change_card":
        admin_user = callback.from_user.id
        cards = await get_all_cards()
       
        if not cards:
            await callback.message.edit_text("خطا در بارگذاری کارت ها، به سازنده پیام بدهید")
            return
        
        kb = InlineKeyboardMarkup(inline_keyboard=[])

        kb.inline_keyboard.append([
            InlineKeyboardButton(text="لیبل", callback_data="none"),
            InlineKeyboardButton(text="وضعیت", callback_data="none"),
            
        ])

        for c in cards:
            card_id, label, number, owner,activity = c
            if activity:
                kb.inline_keyboard.append([
                InlineKeyboardButton(text=f"{label}", callback_data="none"),
                InlineKeyboardButton(text=f"ON", callback_data="none")
            ])
            else:
                kb.inline_keyboard.append([
                    InlineKeyboardButton(text=f"{label}", callback_data="none"),
                    InlineKeyboardButton(text=f"OFF", callback_data=f"activate_card_{card_id}")
                ])

        kb.inline_keyboard.append([
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="axtar_menu")
        ])
        await callback.message.edit_text("📦 لیست کارت ها:(در هر زمان فقط یک کارت میتواند فعال باشد)\n برای فعال سازی یک کارت روی وضعیت آن کلیک کنید.", reply_markup=kb)
    
    elif data.startswith("activate_card_"):
        card_id = int(data.split("_")[2])
        try: 
            await activate_card(card_id)
            await callback.answer("✔️ کارت با موفقیت فعال شد!" , show_alert=True)
            return
        except:
            await callback.answer("❌ نتوانستم کارت را فعال کنم، به سازنده پیام بده!" , show_alert=True)
            return


        
    
    elif data == "remove_disabled_tests":
        usernames = await get_all_test_usernames()
        await delete_disabled_tests_in_marzban(usernames)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔙 بازگشت", callback_data="axtar_menu")
            ]
        ])
        
        await callback.message.edit_text("🧹 تست‌های غیرفعال پاک شدند.",reply_markup=kb)


    elif data == "axtar_menu":
        await callback.message.edit_text("🛠 پنل مدیریت", reply_markup=admin_menu_keyboard())


@router.message(F.text)
async def handle_text_inputs(message: types.Message):
    user_id = message.from_user.id

    if user_id not in user_choices:
        return

    action = user_choices[user_id].get("action")

    # Config name input
    if action == "buy":
        return await handle_config_name(message)

    # Admin adding plan
    if action == "adding_plan":
        return await handle_admin_add_plan_input(message)
    
    if action == "adding_card":
        return await handle_admin_add_card_input(message)

    # Other text-based actions can be added here later


async def handle_admin_add_plan_input(message: types.Message):
    user_id = message.from_user.id
    state = user_choices[user_id]

    step = state.get("step", 1)

    # STEP 1 → read GB
    if step == 1:
        try:
            data_gb = int(message.text)
        except:
            await message.answer("❌ حجم باید عدد باشد. دوباره وارد کنید:")
            return

        state["data_gb"] = data_gb
        state["step"] = 2

        await message.answer("⏳ مدت پلن (به ماه) را وارد کنید:")
        return

    # STEP 2 → read months
    if step == 2:
        try:
            months = int(message.text)
        except:
            await message.answer("❌ مدت باید عدد باشد. دوباره وارد کنید:")
            return

        state["months"] = months
        state["step"] = 3

        await message.answer("💰 قیمت پلن را وارد کنید (بر حسب هزار تومان،بدون صفر،مثلا:110 یا 50 یا 400):")
        return

    # STEP 3 → read price
    if step == 3:
        try:
            price = int(message.text)
        except:
            await message.answer("❌ قیمت باید عدد باشد. دوباره وارد کنید:")
            return

        state["price"] = price
        state["step"] = 4

        await message.answer(
            "📌 آیا این پلن مخصوص نماینده‌هاست یا کاربران؟\n\n"
            "برای نماینده‌ها: 1\n"
            "برای کاربران: 0\n\n"
            "لطفاً فقط عدد *0* یا *1* ارسال کنید(انگلیسی):",
            parse_mode="Markdown"
        )
        return

    # STEP 4 → read for_agent flag (0 or 1)
    if step == 4:
        if message.text not in ("0", "1"):
            await message.answer("❌ فقط عدد 0 یا 1 مجاز است.\nدوباره ارسال کنید:")
            return

        for_agent = int(message.text)

        data_gb = state["data_gb"]
        months = state["months"]
        price = state["price"]

        await add_plan(data_gb, months, price, for_agent)

        # clear state
        user_choices.pop(user_id, None)

        await message.answer(
            "✔ پلن جدید با موفقیت ثبت شد.\n\n"
            f"📦 حجم: {data_gb}GB\n"
            f"⏳ مدت: {months} ماه\n"
            f"💰 قیمت: {price:,} تومان\n"
            f"👥 مخصوص: {'نمایندگان' if for_agent == 1 else 'کاربران'}",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🔙 بازگشت", callback_data="axtar_menu")]]
            )
        )
        return

async def handle_admin_add_card_input(message: types.Message):
    user_id = message.from_user.id
    state = user_choices[user_id]

    step = state.get("step", 1)

    # STEP 1 → read GB
    if step == 1:
        try:
            label = str(message.text)
        except:
            await message.answer("❌ خطای پردازش متن. دوباره وارد کنید:")
            return

        state["card_label"] = label
        state["step"] = 2

        await message.answer("💳 شماره کارت را وارد کنید:\n پیوسته و بدون فاصله مثل:\n 6104338391916565")
        return
    if step == 2:
        try:
            card_number = str(message.text)
        except:
            await message.answer("❌ خطای پردازش متن. دوباره وارد کنید:")
            return

        state["card_number"] = card_number
        state["step"] = 3

        await message.answer("👤 نام و نام خانوادگی صاحب کارت را وارد کنید: \n این نام به کاربران نمایش داده میشود.")
        return

    if step == 3:
        try:
            card_owner = str(message.text)
        except:
            await message.answer("❌ خطای پردازش متن. دوباره وارد کنید:")
            return

        

        card_label = state["card_label"]
        card_number = state["card_number"]
        

        await add_card(card_label, card_number, card_owner)

        # clear state
        user_choices.pop(user_id, None)

        await message.answer(
            "✔ کارت جدید با موفقیت ثبت شد.\n\n"
            f"📦 لیبل: {card_label}\n"
            f"⏳ شماره: {card_number}\n"
            f"💰 مالک: {card_owner}\n",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🔙 بازگشت", callback_data="axtar_menu")]]
            )
        )
        return

async def handle_config_name(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_choices:
        return  # هیچ انتخاب فعالی نداره
    
    co_name_valid = message.text.strip()
    if not message.text:
        await message.answer("⚠️ لطفاً فقط متن بنویس (اسم کانفیگ).")
        return
    elif not re.match(r'^[A-Za-z0-9]{3,}$', co_name_valid):
        await message.answer("⚠️ لطفاً فقط از حروف و اعداد انگلیسی استفاده کن، بدون فاصله، خط یا هر چیز دیگه، و بیش تر از سه حرف.")
        return
    # ذخیره نام
    user_choices[user_id]["config_name"] = message.text.strip()

    data = user_choices[user_id]
    duration = data["duration"]
    size = data["size"]
    price = data["price"]
    name = data["config_name"]
    max_dev = data["max_device"]
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 انتقال به کارت", callback_data="waiting_for_receipt")],
        [InlineKeyboardButton(text="❌ منصرف شدم", callback_data="cancel_payment")]
    ])
    card = await get_active_card()
    card_number = card[2]
    card_owner = card[3]
    await message.answer(
        f"✅ نام کانفیگ: <b>{name}</b>, {max_dev} کاربره\n"
        f"⏱ مدت: {duration} ماهه\n"
        f"📦 حجم: {size} گیگ\n"
        f"💰 مبلغ: {price:,} هزار تومان\n\n"
        "از چه روشی میخوای پرداخت کنی؟",
        parse_mode="HTML",
        reply_markup=keyboard
    )