from aiogram import Router, types, F
from app.keyboards.main_menu import main_menu_keyboard,request_cooperation_keyboard,agent_menu_keyboard
from app.keyboards.admin_menu import admin_menu_keyboard
from app.keyboards.pay_methods import Payment_keyboard
from app.services import marzban_api
from app.services.database import add_order , get_marzban_account_by_id,delete_marzban_account,list_agent_requests,get_user_id
from app.services.database import get_marzban_accounts_by_user,get_agent,get_plan_price_by_DMA, get_user,add_agent_request
from app.services.database import add_agent, delete_agent_request, add_agent_stats, get_agent_stats, is_agent
from app.services.database import get_plans,delete_plan,add_plan,get_available_months,get_sizes_for_month,get_plan_by_id
from app.services.database import count_test_accounts,add_test_account,get_all_test_usernames
from app.services.database import get_all_cards,add_card,get_active_card,activate_card,update_order_status
from app.services.database import get_all_tutorials,update_tutorial_link,get_tutorials_by_device
from app.services.database import get_user_stats,add_balance_by_telegram_id,transfer_balance
from app.services.database import increase_approved_buy, add_transaction
from app.services.database import add_data_added,add_agent_income,increment_agent_buys,add_buy_price,is_agent
from app.services.database import get_user_price_for_plan,add_renew_price,add_gb_added
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import re
from app.services.marzban_api import get_user_by_username,delete_user_from_marzban,delete_disabled_tests_in_marzban,create_Test_in_marzban
from app.services.marzban_api import update_user_in_marzban,create_user_in_marzban,add_data_for_user_in_marzban
from app.services.database import get_marzban_account_by_user_plan,update_marzban_account_after_renew,add_marzban_account
from datetime import datetime,timezone,timedelta
from zoneinfo import ZoneInfo
import math
import os


router = Router()
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID"))
ORDERS_CHANNEL_ID = int(os.getenv("ORDERS_CHANNEL_ID"))
SUPPORT_ACC_ID = int(os.getenv("SUPPORT_ACC_ID"))

# حافظه موقت برای نگهداری انتخاب‌های کاربر
user_choices = {}
def tehran_now():
    return datetime.now(ZoneInfo("Asia/Tehran"))

def to_persian_digits(n: int) -> str:
    trans = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
    return str(n).translate(trans)

# STRONG direction controls (button-safe)
RLO = "\u202E"   # Right-to-Left OVERRIDE  ✅ strongest
PDI = "\u2069"   # Pop Direction Isolate
RLM = "\u200F"   # Right-to-Left Mark

def format_amount_button(amount: int) -> str:
    if amount > 999:
        million = amount // 1000
        thousand = amount - million * 1000

        if thousand == 0:
            text = f"{to_persian_digits(million)} میلیون"
        else:
            text = f"{to_persian_digits(million)} میلیون و {to_persian_digits(thousand)} هزار"
    else:
        text = f"{to_persian_digits(amount)} هزار"

    text += " تومان"

    # ✅ FORCE RTL HARD for Telegram buttons
    return f"{RLO}{RLM}{text}{PDI}"

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
            InlineKeyboardButton(text="📞 حجم بیشتر ", url="https://t.me/freeedomarea")
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
        if telegram_id == ADMIN_ID:
            is_admin = True
        else:
            is_admin = False

        agent = await is_agent(telegram_id)
        is_agent_flag = 1 if agent or is_admin else 0

        current_count = await count_test_accounts(telegram_id, is_agent_flag)

        # LIMITS
        if agent:
            limit = 5  # daily
        elif is_admin:
            limit = 99
        else:
            limit = 2  # monthly
        
        
        if current_count >= limit:
            if agent:
                await callback.answer(
                    "⛔️ سقف دریافت اکانت تست امروز پر شده است. (۵ تا در روز)",
                    show_alert=True
                )
            elif is_admin:
                await callback.answer(
                    "⛔️ عامو بیشین چخبرته",
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
        device_android = await get_tutorials_by_device("Usage","Android")
        
        ANDROID_MESSAGE_URL = device_android[4]
        device_ios = await get_tutorials_by_device("Usage","IOS")
        IOS_MESSAGE_URL = device_ios[4]
        device_windows = await get_tutorials_by_device("Usage","Windows")
        WINDOWS_MESSAGE_URL = device_windows[4]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📘 نحوه استفاده اندروید", url=ANDROID_MESSAGE_URL)],
                [InlineKeyboardButton(text="📘 نحوه استفاده آیفون", url=IOS_MESSAGE_URL)],
                [InlineKeyboardButton(text="📘 نحوه استفاده ویندوز", url=WINDOWS_MESSAGE_URL)],
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
        return



    elif data == "charge_wallet":
        telegram_id = callback.from_user.id
        user_choices[telegram_id] = {"action": "charge_wallet", "step": 1}

        await callback.message.edit_text(
            "مقدار شارژ را وارد کنید:(بدون سه صفر)\nمثلا صد هزار تومان=100 \n حداقل شارژ پنجاه هزار تومان(50) و حداکثر ده میلیون(10000) می باشد",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="❌ بیخیال", callback_data="back_to_menu")]]
            )
        )
        

    elif data == "profile":
        telegram_id = callback.from_user.id
        userdataone = await get_user(telegram_id)
        username = callback.from_user.username
        name = callback.from_user.first_name
        phone_number= userdataone[5]
        userstats = await get_user_stats(telegram_id)
        referalcode = userstats[2]
        num_orders = userstats[3]
        #number_of_referals = ?
        marzban_accounts = await get_marzban_accounts_by_user(telegram_id)
        marzban_accounts_count = len(marzban_accounts)
        sum_transactions = userstats[4]
        num_transactions = userstats[5]
        balance = userdataone[9]
        date = tehran_now().strftime('%Y-%m-%d')
        time = tehran_now().strftime('%H:%M:%S')

        if telegram_id == ADMIN_ID:
            is_admin = True
        else:
            is_admin = False
        isAgent = await is_agent(telegram_id)
        RTL = "\u202B"  # Right-to-Left Embedding
        POP = "\u202C"  # End Direction

        TextP1 = (
            f"{RTL}<blockquote>🪪 مشخصات شما{POP}\n"
            f"{RTL}🫆 شناسه: {telegram_id}{POP}\n"
            f"{RTL}🆔 نام کاربری: @{username}{POP}\n"
            f"{RTL}👤 نام: {name}{POP}\n"
            f"{RTL}📞 شماره تلفن: {phone_number}{POP}\n"
            f"{RTL}⛓️ کد دعوت شما: <code>{referalcode}</code>{POP}</blockquote>\n\n"
        )
        TextP2 = (
            f"<blockquote>📊 تراکنش‌ها\n"
            f"🧾 تعداد سفارشات: {num_orders}\n"
            f"👥 تعداد زیرمجموعه: {0}\n"
            f"🟢 سرویس های فعال: {marzban_accounts_count}\n"
            f"💸 تراکنش کل: {sum_transactions}\n"
            f"🧮 تعداد تراکنش ها: {num_transactions}\n\n"
            f"<b>💰 موجودی: {balance }</b></blockquote>\n\n"
        )
        TextP3 = (
            f"<i>🌘 تاریخ: {date}\n"
            f"⌚ ساعت: {time}\n</i>"
        )
        Text = TextP1 + TextP2 + TextP3
        if isAgent:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    #[InlineKeyboardButton(text="💸 انتقال اعتبار", callback_data="send_credit")],
                    [InlineKeyboardButton(text="💳 شارژ کیف پول", callback_data="charge_wallet")],
                    [InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="back_to_menu")]
                ])
        else:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="💳 شارژ کیف پول", callback_data="charge_wallet")],
                    [InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="back_to_menu")]
                ])
            
        await callback.message.edit_text(text= Text,
        parse_mode="HTML",
        reply_markup=keyboard)

    elif data == "send_credit":
        telegram_id = callback.from_user.id
        isAgent = await is_agent(telegram_id)
        if not isAgent:
            return
        
        userdata = await get_user(telegram_id)
        balance = userdata[9]
        if balance < 50: 
            await callback.message.answer("برای انتقال باید حداقل 50 هزارتومان اعتبار داشته باشید.")
            return
        
        user_choices[telegram_id] = {"action": "agent_send_credit", "step": 1}

        await callback.message.edit_text(
            "مقدار اعتبار ارسالی را وارد کنید:(بدون سه صفر)\n مثلا پنجاه هزار تومان=50",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="❌ لغو", callback_data="back_to_menu")]]
            )
        )


    elif data == "apps":
        device_android = await get_tutorials_by_device("Install","Android")
        ANDROID_APP_URL = device_android[4]
        device_ios = await get_tutorials_by_device("Install","IOS")
        IOS_APP_URL = device_ios[4]
        device_windows = await get_tutorials_by_device("Install","Windows")
        WINDOWS_APP_URL = device_windows[4]
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📱 دانلود برنامه اندروید", url=ANDROID_APP_URL)],
                [InlineKeyboardButton(text="📱 دانلود برنامه آیفون", url=IOS_APP_URL)],
                [InlineKeyboardButton(text="💻 دانلود برنامه ویندوز", url=WINDOWS_APP_URL)],
                [InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="back_to_menu")]
            ])
        await callback.message.edit_text("📲 با زدن روی هرکدام از لینک های زیر میتوانید نرم افزار مورد نیاز را دانلود و سپس نصب کنید.",
        parse_mode="HTML",
        reply_markup=keyboard)

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
    


    elif data == "cancel_payment":
        user_choices.pop(callback.from_user.id, None)
        await callback.answer()                
        await callback.message.delete() 
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="back_to_menu")]
            ])
        await callback.message.answer("✅ عملیات خرید لغو شد.\nمی‌تونی هر زمان خواستی دوباره از منوی خرید اقدام کنی.",reply_markup=keyboard)
        
    elif data == "waiting_for_receipt":
        card = await get_active_card()
        card_number = card[2]
        card_owner = card[3]
        await callback.answer()
        await callback.message.delete() 
        await callback.message.answer(
            "📸 لطفاً تصویر رسید پرداخت خود را ارسال کنید.\n\n"
            f"📸 <code>{card_number}</code>\n {card_owner} \n" #this will be payment card and the name.
            "در صورت لغو، از منوی اصلی گزینه‌ی دیگری را انتخاب کنید.",
            parse_mode="HTML"
        )
        

    elif data == "pay_with_wallet":
        telegram_id = callback.from_user.id
        db_user_id = await get_user_id(telegram_id)
        
        if not db_user_id:
            await callback.answer("⚠️ ابتدا باید در ربات ثبت‌نام کنید.")
            return
        
        telegramuser = await get_user(telegram_id)
        balance = telegramuser[9]
        user_data = user_choices.get(telegram_id)
        file_id = "wallet"
        config_name = user_data.get("config_name", "بدون نام")
        duration = user_data.get("duration", 0)
        size = user_data.get("size", 0)
        price = user_data.get("price", 0)
        isAgent = user_data.get("is_agent",0)
        order_type = user_data.get("action", "buy")
        userlimit = user_data.get("user_limit", 1)
        maxdevtext = user_data.get("max_device", "نامعلوم")
        R_order_type = file_id + "_" + order_type
        if balance < price: 
            await callback.message.answer(f"امکان پرداخت وجود ندارد.\n موجودی شما:{balance}، مبلغ سفارش:{price}")
            return

        if isAgent:
            CoworkOrCust = "نماینده"
        else:
            CoworkOrCust = "کاربر"
        # ذخیره در دیتابیس
        order_id = await add_order(telegram_id, config_name, price, duration, size, file_id, R_order_type ,userlimit)
        minus_amount = (abs(price)) * -1
        await add_balance_by_telegram_id(telegram_id,minus_amount)
        await update_order_status(order_id, "approved")

        if order_type == "renew":
            
            order_type_text = "تمدید"
            account = await get_marzban_account_by_user_plan(telegram_id, config_name)
            if not account:
                await callback.answer("❌ حساب در دیتابیس یافت نشد.", show_alert=True)
                return
            acc_id = account[0]
            panel_username = account[2]
            months = int(account[8])
            size_gb = float(account[9])
            marzban_user = await get_user_by_username(panel_username)
            if not marzban_user:
                await callback.answer("❌ دریافت اطلاعات از پنل ناموفق بود.", show_alert=True)
                return

            current_expire = marzban_user.get("expire") or 0

            # محاسبه expire جدید
            
            add_seconds = months * 30 * 24 * 60 * 60
            if current_expire:
                new_expire_ts = int((datetime.fromtimestamp(current_expire, ZoneInfo("Asia/Tehran")) + timedelta(seconds=add_seconds)).timestamp())
            else:
                
                new_expire_ts = int((tehran_now()  + timedelta(seconds=add_seconds)).timestamp())

            # حجم جدید
            data_limit = int(size_gb * 1024 * 1024 * 1024)
            payload = {
                "status": "active",
                "username": panel_username,
                "note": "",
                "data_limit": data_limit,
                "data_limit_reset_strategy": "no_reset",
                "expire": new_expire_ts,

                "inbounds": {
                    "vless": ["REALITY", "TCPNONE", "VLESS+GRPC+NONE"],
                    "shadowsocks": ["Shadowsocks TCP"],
                    "trojan": ["Trojan + Tcp"],
                    "vmess": ["VMESS + TCP"]
                },

                "proxies": {
                    "vless": {"flow": ""},
                    "shadowsocks": {"method": "chacha20-ietf-poly1305"},
                    "trojan": {},
                    "vmess": {}
                }
            }
            # ارسال به مرزبان
            ok = await update_user_in_marzban(panel_username, payload)

            if not ok:
                await callback.answer("❌ خطا در تمدید سرویس.")
                await callback.bot.send_message(
                    ADMIN_ID,  
                    "خطایی در روند تمدید با موجودی رخ داد. لطفا خطاهارا بررسی کنید!")
                return

            # آپدیت دیتابیس محلی
            await update_marzban_account_after_renew(acc_id, new_expire_ts, size_gb)
            await callback.answer()
            await callback.message.delete() 
            await callback.bot.send_message(
                    LOG_CHANNEL_ID,  
                    f" <a href='tg://user?id={telegram_id}'>{CoworkOrCust}</a> تراکنش {order_type_text} حساب {panel_username} را با موجودی پرداخت کرد.")
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="back_to_menu")]
                ])
            # پیام برای کاربر
            await callback.bot.send_message(
                account[1],  # telegram_user_id
                "✅ تمدید سرویس شما با موفقیت انجام شد!",
                reply_markup=keyboard
            )
            #افزایش آمار کاربر
            try:
                await add_transaction(telegram_id,price)
                if await is_agent(telegram_id):
                    if userlimit == 3:
                        Multip = 2
                    elif userlimit == 5:
                        Multip = 3
                    else:
                        Multip = 1
                    revenue = await get_user_price_for_plan(months, size/Multip)
                    
                    revenue = revenue * Multip
                    await increment_agent_buys(telegram_id)

                    await add_renew_price(telegram_id, price)

                    # درآمد نماینده 
                    await add_agent_income(telegram_id, revenue)
            except Exception as e:
                print(f" Could'nt add stats. ERROR:{e}")


        elif order_type == "add_data":
            order_type_text = "افزایش حجم"
            duration= "-"
            account = await get_marzban_account_by_user_plan(telegram_id, config_name)
            if not account:
                await callback.answer("❌ حساب در دیتابیس یافت نشد.", show_alert=True)
                return

            acc_id = account[0]
            panel_username = account[2]
            
            # تبدیل گیگ به بایت
            add_bytes = int(size * 1024 * 1024 * 1024)

            # دریافت اطلاعات فعلی کاربر از مرزبان
            marzban_user = await get_user_by_username(panel_username)
            if not marzban_user:
                await callback.answer("❌ دریافت اطلاعات از پنل ناموفق بود.", show_alert=True)
                return

            current_limit = marzban_user.get("data_limit") or 0
            Expire = marzban_user.get("expire") or 0

            new_limit = current_limit + add_bytes

            new_limit_gb = (((new_limit / 1024) / 1024) / 1024)

            ok = await add_data_for_user_in_marzban(panel_username, new_limit, Expire)

            if not ok:
                await callback.answer("❌ خطا در اضافه‌کردن حجم.")
                await callback.bot.send_message(
                    ADMIN_ID,
                    "خطایی در روند تایید رخ داد. لطفا خطاهارا بررسی کنید!"
                )
                return

            # آپدیت دیتابیس لوکال
            await update_marzban_account_after_renew(acc_id, Expire, new_limit_gb)
            await callback.answer()
            await callback.message.delete() 
            await callback.bot.send_message(
                telegram_id,
                f"✅ {size} گیگابایت به سرویس شما اضافه شد!",
                reply_markup= InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="back_to_menu_without_del")]
            ])
            )

            await callback.bot.send_message(
                    LOG_CHANNEL_ID,  
                    f" <a href='tg://user?id={telegram_id}'>{CoworkOrCust}</a> تراکنش {order_type_text} حساب {panel_username} را با موجودی پرداخت کرد.")
            #افزایش آمار کاربر
            await add_transaction(telegram_id,price)

            if await is_agent(telegram_id):
                
                
                await add_data_added(telegram_id, price)

            
                await add_gb_added(telegram_id, size)

            
                



            return
        else:
            order_type_text = "خرید"
            tg_username = telegramuser[2] if isinstance(telegramuser, (list, tuple)) else telegramuser["username"]
            tg_phonenum = telegramuser[5] if isinstance(telegramuser, (list, tuple)) else telegramuser["phone_number"]
            if tg_username:
                prefix = tg_username
            else :
                prefix = tg_phonenum
            try:
                # ساخت یوزر در مرزبان
                days = duration * 30
                expire_timestamp = int((tehran_now() + timedelta(days)).timestamp())
                Plan_name = config_name + "-" + prefix
                data_limit = int(size)
                # تبدیل قیمت یا حجم به مشخصات پلن (موقت)
                # مثلا بر اساس نام کانفیگ، حجم و مدت مشخص کن
                sub_link = await create_user_in_marzban(username=Plan_name, data_limit_gb=data_limit, expire_days= days)
                await add_marzban_account(telegram_id,Plan_name,"Active",expire_timestamp,0,sub_link,duration,data_limit,userlimit)
                device_android = await get_tutorials_by_device("Usage","Android")
                ANDROID_MESSAGE_URL = device_android[4]
                device_ios = await get_tutorials_by_device("Usage","IOS")
                IOS_MESSAGE_URL = device_ios[4]
                device_windows = await get_tutorials_by_device("Usage","Windows")
                WINDOWS_MESSAGE_URL = device_windows[4]
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📘 نحوه استفاده اندروید", url=ANDROID_MESSAGE_URL)],
                    [InlineKeyboardButton(text="📘 نحوه استفاده آیفون", url=IOS_MESSAGE_URL)],
                    [InlineKeyboardButton(text="📘 نحوه استفاده ویندوز", url=WINDOWS_MESSAGE_URL)],
                    [InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="back_to_menu_without_del")]
                ])
                await callback.answer()
                await callback.message.delete() 
                await callback.bot.send_message(
                    telegram_id,
                    f"✅ حساب شما ساخته شد!\n\n"
                    f"🔗 <b>لینک اشتراک:</b>\n<code>{sub_link}</code>",
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
                # ارسال لینک به کاربر
                
                await callback.bot.send_message(
                    LOG_CHANNEL_ID,  
                    f" <a href='tg://user?id={telegram_id}'>{CoworkOrCust}</a> تراکنش {order_type_text} حساب {Plan_name} را با موجودی پرداخت کرد.")
            except Exception as e:
                await callback.bot.send_message(telegram_id, "⚠️ خطا در ساخت حساب در پنل. پشتیبانی در حال بررسی است.")
                await callback.bot.send_message(
                    ADMIN_ID,  
                    "خطایی در روند خرید با موجودی رخ داد. لطفا خطاهارا بررسی کنید!")
                print(f"[Marzban Error] {e}")
            #افزایش آمار کاربر
            try:
                await increase_approved_buy(telegram_id)
                await add_transaction(telegram_id,price)
                
                if await is_agent(telegram_id):
                    if userlimit == 3:
                        Multip = 2
                    elif userlimit == 5:
                        Multip = 3
                    else:
                        Multip = 1
                    revenue = await get_user_price_for_plan(duration, data_limit/Multip)
                    
                    revenue = revenue * Multip
                    await increment_agent_buys(telegram_id)

                    # جمع مبلغ خرید
                    await add_buy_price(telegram_id, price)
                    
                    # درآمد نماینده 
                    await add_agent_income(telegram_id, revenue)
            except Exception as e:
                print(f" Could'nt add stats. ERROR:{e}")
            

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

        
        await callback.message.edit_text(
            f"📌 حجم انتخاب‌شده: {gb}GB\n"
            f"💰 مبلغ: {price:,} هزار تومان\n\n"
            "خب، روش پرداختت رو انتخاب کن",
            reply_markup=Payment_keyboard(),

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
        

        await callback.message.answer(
            f"💳 مبلغ تمدید: {plan_price:,} هزار تومان\n"
            "لطفاً روش پرداخت را انتخاب کنید.",
            reply_markup=Payment_keyboard(),
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
         
        total_income_text      = format_amount_button(total_income)
        text_sum_buy_prices    = format_amount_button(sum_buy_prices)
        text_sum_of_data_added = format_amount_button(sum_of_data_added)
        text_sum_renew_prices  = format_amount_button(sum_renew_prices)

        
           
        

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=str(number_of_buys), callback_data="noop"),
                InlineKeyboardButton(text="تعداد خرید", callback_data="noop")
                
            ],
            [
                InlineKeyboardButton(text=total_income_text, callback_data="noop"),
                InlineKeyboardButton(text="درآمد کل", callback_data="noop")
            ],
            [
                InlineKeyboardButton(text=text_sum_buy_prices, callback_data="noop"),
                InlineKeyboardButton(text="جمع خریدها", callback_data="noop")
            ],
            [
                InlineKeyboardButton(text=f"{sum_of_gb_added}", callback_data="noop"),
                InlineKeyboardButton(text="حجم اضافه شده", callback_data="noop")
            ],
            [
                InlineKeyboardButton(text=text_sum_of_data_added, callback_data="noop"),
                InlineKeyboardButton(text="مبلغ حجم اضافه شده", callback_data="noop")
            ],
            [
                InlineKeyboardButton(text=text_sum_renew_prices, callback_data="noop"),
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
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="back_to_menu")]
            ])
        # notify the agent
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 رفتن به منو", callback_data="back_to_menu")]
            ])
        await callback.bot.send_message(
            tg_id,
            "درخواست همکاری شما تایید شد!\n"
            "اکنون شما به عنوان نماینده ثبت شده‌اید.",
            reply_markup=keyboard
            
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
    

    elif data == "set_tutor_links":
        admin_user = callback.from_user.id
        tutorials = await get_all_tutorials()

        kb = InlineKeyboardMarkup(inline_keyboard=[])

        kb.inline_keyboard.append([
            InlineKeyboardButton(text="نوع", callback_data="none"),
            InlineKeyboardButton(text="مبحث", callback_data="none"),
            InlineKeyboardButton(text="سیستم", callback_data="none"),
            InlineKeyboardButton(text="لینک", callback_data="none"),
            
        ])

        for t in tutorials:
            tut_id, topic, type_, device ,link = t
            if type_ == "Usage":
                type_text = "آموزش"
            elif type_ == "Install":
                type_text = "دانلود"
            if topic == "Sublink":
                topic_text = "لینک ساب"
            else:
                topic_text = str(topic)
            if link:
                message_url= link
                linktext ="Go"
                kb.inline_keyboard.append([
                InlineKeyboardButton(text=f"{type_text}", callback_data=f"changelink_{tut_id}"),
                InlineKeyboardButton(text=f"{topic_text}", callback_data="none"),
                InlineKeyboardButton(text=f"{device}", callback_data="none"),
                InlineKeyboardButton(text=f"{linktext}", url=message_url ),
                ])
            else: 
                linktext = "No"
                kb.inline_keyboard.append([
                InlineKeyboardButton(text=f"{type_text}", callback_data=f"changelink_{tut_id}"),
                InlineKeyboardButton(text=f"{topic_text}", callback_data="none"),
                InlineKeyboardButton(text=f"{device}", callback_data="none"),
                InlineKeyboardButton(text=f"{linktext}", callback_data="none" ),
                ])
            
            
            

        kb.inline_keyboard.append([
            InlineKeyboardButton(text="🔙 بازگشت", callback_data="axtar_menu")
        ]) 
        await callback.message.edit_text("🔗 لیست لینک های آموزشی:", reply_markup=kb)   

    elif data.startswith("changelink_"):
        tut_id = int(data.split("_")[1])
        admin_user = callback.from_user.id
        user_choices[admin_user] = {"action": "chnge_tutor_link", "Link_id":tut_id}
        await callback.message.edit_text(
            "📎 لینک جدید را ارسال کنید:",
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


    elif data == "admin_send_credit":
        admin_user = callback.from_user.id
        user_choices[admin_user] = {"action": "admin_send_credit", "step": 1}

        await callback.message.edit_text(
            "مقدار اعتبار ارسال را وارد کنید:(بدون سه صفر)\n پنجاه هزار تومان=50",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="❌ لغو", callback_data="axtar_menu")]]
            )
        )

    
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
        modir = callback.from_user.first_name
        await callback.message.edit_text(f"👑 سلام {modir} عزیز، خوش آمدید. پنل مخصوص شما:", reply_markup=admin_menu_keyboard())


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
    
    
    if action == "admin_send_credit":
        return await handle_admin_send_credit_input(message)

    if action == "agent_send_credit":
        return await handle_agent_send_credit_input(message)

    if action == "chnge_tutor_link":
        tut_id = user_choices[user_id].get("Link_id")
        return await handle_admin_change_tutor_link(message,tut_id)
    
    if action == "adding_card":
        return await handle_admin_add_card_input(message)

    if action == "charge_wallet":
        return await handle_user_recharge(message)

async def handle_admin_change_tutor_link(message:types.Message, link_id :int):
    user_id = message.from_user.id
    LinkToChange= link_id
    try:
        link = str(message.text)
    except:
        await message.answer("❌ خطای پردازش متن. دوباره وارد کنید:")
        return
    try:
        await update_tutorial_link(LinkToChange,link)

    except:
        await message.answer("❌ خطای عملیات در پایگاه داده!")
    await message.answer(
            "✔ لینک با موفقیت آپدیت شد.\n\n",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="🔙 بازگشت", callback_data="axtar_menu")]]
            )
        )
    return

async def handle_admin_send_credit_input(message: types.Message):
    user_id = message.from_user.id
    state = user_choices[user_id]

    step = state.get("step", 1)

    # STEP 1 → read Credit
    if step == 1:
        try:
            credit_amount = int(message.text)
        except:
            await message.answer("❌ مبلغ باید عدد باشد. دوباره وارد کنید:")
            return

        state["credit_amount"] = credit_amount
        state["step"] = 2
        await message.bot.delete_message(message.chat.id, message.message_id - 1)
        await message.answer("شناسه فرد هدف را بفرستید: \n لطفا در این مورد دقت کنید.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="❌ لغو", callback_data="axtar_menu")]]
            ))
        return

    if step == 2:
        try:
            target_id = message.text
        except:
            await message.answer("❌ خطای پردازش متن. دوباره وارد کنید:")
            return

        

        credit_amount = state["credit_amount"]
        if credit_amount>999:
            Million = math.floor(credit_amount/1000)
            Thousand = credit_amount - (Million*1000)
            if Thousand == 0:
                credit_amount_text = f"{Million} میلیون"
            else:
                credit_amount_text = f"{Million} میلیون و {Thousand}"

        else:
            credit_amount_text =f"{credit_amount} هزار تومان"
        
        try:
            await add_balance_by_telegram_id(target_id, credit_amount)

            # clear state
            user_choices.pop(user_id, None)
            await message.bot.delete_message(message.chat.id, message.message_id - 1)
            await message.answer(
                "✔ اعتبار با موفقیت ارسال شد.\n\n"
                f"📦 مقدار: {credit_amount_text}\n",
                reply_markup=InlineKeyboardMarkup(
                    
                    inline_keyboard=[
                        [InlineKeyboardButton(text="مشاهده کاربر هدف", url=f"tg://user?id={target_id}")],
                        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="axtar_menu")]
                                     ]
                )
            )
            await message.bot.send_message(
            target_id,
            f"🎁 کیف پول شما توسط مدیریت شارژ شد. \n مبلغ:{credit_amount_text} ",
            )
            return
        
        except Exception as e:
            print(f"[DEBUG] Error: {e}") 
            await message.answer(f" خطای دیتابیس:{e}")
    
async def handle_agent_send_credit_input(message: types.Message):
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    state = user_choices[user_id]

    step = state.get("step", 1)
    userdata = await get_user(user_id)
    balance = userdata[9]
    # STEP 1 → read Credit
    if step == 1:
        try:
            credit_amount = int(message.text)
        except:
            await message.answer("❌ مبلغ باید عدد باشد. دوباره وارد کنید:")
            return
        
        
        userdata = await get_user(user_id)
        balance = userdata[9]
        if balance < credit_amount:
            
            user_choices.pop(user_id, None)
            await message.answer("❌ متاسفم اما نمیتونی بیش از موجودیت ارسال کنی، روند تراکنش رو کاملا متوقف کردم. با دکمه زیر میتونی برگردی به منو!",
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="بازگشت", callback_data="back_to_menu")]]
            ))
            await message.bot.send_message(
                LOG_CHANNEL_ID,
                f"نماینده <a href='tg://user?id={user_id}'>{user_name}</a> میخواست بیش از موجودیش؛ اعتبار انتقال بده. امیدوارم که از قصد نبوده باشه!"
            )
            return
        
        
        
        state["credit_amount"] = credit_amount
        state["step"] = 2

        await message.answer("شناسه فرد هدف را بفرستید: \n لطفا در این مورد دقت کنید.",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[[InlineKeyboardButton(text="❌ لغو", callback_data="back_to_menu")]]
            ))
        return

    if step == 2:
        try:
            target_id = message.text
        except:
            await message.answer("❌ خطای پردازش متن. دوباره وارد کنید:")
            return

        
        

        credit_amount = state["credit_amount"]
        if credit_amount>999:
            Million = math.floor(credit_amount/1000)
            Thousand = credit_amount - (Million*1000)
            if Thousand == 0:
                credit_amount_text = f"{Million} میلیون"
            else:
                credit_amount_text = f"{Million} میلیون و {Thousand}"

        else:
            credit_amount_text =f"{credit_amount} هزار تومان"
        
        try:
            await transfer_balance(user_id,target_id, credit_amount)
            # clear state
            user_choices.pop(user_id, None)
            
            await message.answer(
                "✔ اعتبار با موفقیت ارسال شد.\n\n"
                f"📦 مقدار: {credit_amount_text}\n",
                reply_markup=InlineKeyboardMarkup(
                    
                    inline_keyboard=[
                        [InlineKeyboardButton(text="مشاهده کاربر هدف", url=f"tg://user?id={target_id}")],
                        [InlineKeyboardButton(text="🔙 بازگشت", callback_data="back_to_menu")]
                                     ]
                )
            )
            await message.bot.send_message(
            target_id,
            f"🎁 کیف پول شما توسط <a href='tg://user?id={user_id}'>{user_name}</a> شارژ شد. \n مبلغ:{credit_amount_text} ",
            )
            await message.bot.send_message(
                LOG_CHANNEL_ID,
                f"نماینده <a href='tg://user?id={user_id}'>{user_name}</a> برای <a href='tg://user?id={target_id}'>این کاربر</a> مقدار {credit_amount_text} اعتبار ارسال کرد!"
            )
            return
        
        except Exception as e:
            print(f"[DEBUG] Error: {e}") 
            await message.answer(f" خطای دیتابیس: با پشتیبانی تماس بگیرید.")

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
    
    card = await get_active_card()
    card_number = card[2]
    card_owner = card[3]
    
    await message.bot.delete_message(message.chat.id, message.message_id - 1)
    await message.answer(
        f"✅ نام کانفیگ: <b>{name}</b>, {max_dev} کاربره\n"
        f"⏱ مدت: {duration} ماهه\n"
        f"📦 حجم: {size} گیگ\n"
        f"💰 مبلغ: {price:,} هزار تومان\n\n"
        "از چه روشی میخوای پرداخت کنی؟",
        parse_mode="HTML",
        reply_markup=Payment_keyboard()
    )

async def handle_user_recharge(message: types.Message):
    user_id = message.from_user.id
    is_agent_user = await is_agent(user_id)
    for_agent = 1 if is_agent_user else 0
    user_choices[user_id]["is_agent"] = for_agent
    if user_id not in user_choices:
        return
    try:
        amount = int(message.text)
    except:
        await message.answer("❌ قیمت باید عددی انگلیسی باشد. دوباره وارد کنید:")
        return
    
    if amount < 50 or amount > 10000:
        await message.answer("❌ به محدوده قیمت گفته شده دقت کنید، لطفا عدد مجاز ارسال کنید:")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💳 انتقال به کارت", callback_data="waiting_for_receipt")],
        [InlineKeyboardButton(text="❌ منصرف شدم", callback_data="cancel_payment")]
    ])
    if amount>999:
        Million = math.floor(amount/1000)
        Thousand = amount - (Million*1000)
        if Thousand == 0:
            text_amount = f"{Million} میلیون"
        else:
            text_amount = f"{Million} میلیون و {Thousand}"

    else:
        text_amount =f"{amount} هزار تومان"
    
    
    user_choices[user_id]["price"] = amount
    
    await message.answer(
        f"📦 شارژ حساب \n"
        f"💰 مبلغ: {text_amount}\n\n"
        "از چه روشی میخوای پرداخت کنی؟",
        parse_mode="HTML",
        reply_markup=keyboard
    )