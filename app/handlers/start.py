# app/handlers/start.py
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.types import (
    KeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from datetime import datetime
import os

from app.services.database import add_user, get_user, set_user_joined, is_user_joined,is_agent
from app.keyboards.main_menu import main_menu_keyboard,agent_menu_keyboard

router = Router()

# کانال اجباری (از env یا پیش‌فرض)
REQUIRED_CHANNEL = os.getenv("REQUIRED_CHANNEL_ID") or "-1001850027241"


# ==============================
# 🔹 ساخت inline keyboard جوین کانال
# ==============================
def join_keyboard(channel_id: str):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 عضویت در کانال", url=f"https://t.me/{channel_id.lstrip('@')}")],
        [InlineKeyboardButton(text="✅ من عضو شدم", callback_data="check_join")]
    ])


# ==============================
# 🔹 تابع درخواست شماره
# ==============================
async def ask_for_phone(message: types.Message):
    contact_btn = KeyboardButton(text="📱 ارسال شماره من", request_contact=True)
    keyboard = ReplyKeyboardMarkup(
        keyboard=[[contact_btn]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.answer(
        "سلام 👋\nبرای شروع لطفاً روی دکمه زیر بزن تا شماره‌ت ثبت بشه:",
        reply_markup=keyboard
    )


# ==============================
# 🔹 دستور /start
# ==============================
@router.message(CommandStart())
async def start_command(message: types.Message):
    user_id = message.from_user.id
    user = await get_user(user_id)

    if REQUIRED_CHANNEL:
        try:
            member = await message.bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user_id)
            if member.status not in ["member", "administrator", "creator"]:
                await message.answer(
                    "👋 سلام!\nبرای استفاده از ربات، ابتدا در کانال زیر عضو شو 👇",
                    reply_markup=join_keyboard(REQUIRED_CHANNEL)
                )
                return
        except Exception:
            await message.answer("⚠️ خطا در بررسی عضویت، بعداً دوباره تلاش کن.")
            return

    # اگر کاربر قبلاً ثبت شده
    if user:
        telegram_id = message.from_user.id
        isAgent = await is_agent(telegram_id)
        if isAgent:
            await message.answer(
                "🌟 خوش اومدی دوباره!\nمنوی اصلی برات باز شد 👇",
                reply_markup=ReplyKeyboardRemove()
            )
            await message.answer(
                "درود ، به ربات cipher connect خوش اومدی ✨\n\nاینترنت آزاد رو با ما تجربه کنید🌐\n\n🟢 اتصال پایدار و با کیفیت \n\n⚡️پر سرعت با کمترین پینگ\n\n🔒 تضمین اتصال ایمن و مطمئن\n\n⚪️ منصفانه ترین قیمت\n\n⏱ پشتیبانی ۲۴ ساعته\n\nجهت دریافت نمایندگی حتما با پشتیبانی در ارتباط باشید ✅\n\n🆔 @freeedomarea",
                reply_markup=agent_menu_keyboard()
            )
            
        else:
            await message.answer(
                "🌟 خوش اومدی دوباره!\nمنوی اصلی برات باز شد 👇",
                reply_markup=ReplyKeyboardRemove()
            )
            await message.answer(
                "درود ،دوست عزیز! به ربات cipher connect خوش اومدی ✨\n\n"
                "🌐 اینترنت آزاد رو با ما تجربه کن!\n\n"
                "🟢 اتصال پایدار و با کیفیت\n\n"
                "⚡️ پرسرعت با کمترین پینگ\n\n"
                "🔒 اتصال ایمن و مطمئن\n\n"
                "⚪️ منصفانه‌ترین قیمت\n\n"
                "⏱ پشتیبانی ۲۴ ساعته\n\n"
                "🆔 @freeedomarea",
                reply_markup=main_menu_keyboard()
        )
    else:
        await ask_for_phone(message)


# ==============================
# 🔹 بررسی دکمه "من عضو شدم"
# ==============================
@router.callback_query(lambda c: c.data == "check_join")
async def callback_check_join(callback: types.CallbackQuery):
    user = callback.from_user
    bot = callback.bot

    try:
        member = await bot.get_chat_member(chat_id=REQUIRED_CHANNEL, user_id=user.id)
        if member.status in ("member", "administrator", "creator"):
            await callback.answer("✅ عضویت شما تایید شد!", show_alert=True)
            await callback.message.delete()

            # اجرای مجدد منطق /start بعد از تأیید عضویت
            fake_message = types.Message(
                message_id=callback.message.message_id,
                from_user=user,
                chat=callback.message.chat,
                date=callback.message.date,
                text="/start"
            )
            await start_command(fake_message)
        else:
            await callback.answer("❌ هنوز عضو کانال نیستی. لطفاً عضو شو و دوباره امتحان کن.", show_alert=True)
    except Exception:
        await callback.answer(
            "⚠️ ربات نتونست عضویت شما رو بررسی کنه. مطمئن شو ربات داخل کانال هست.",
            show_alert=True
        )


# ==============================
# 🔹 دریافت شماره کاربر
# ==============================
@router.message(F.contact)
async def get_contact(message: types.Message):
    phone = message.contact.phone_number
    user = message.from_user

    await add_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        phone_number=phone,
        register_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    await message.answer(
        f"✅ شماره‌ت ({phone}) با موفقیت ثبت شد!\n"
        "حالا منوی اصلی برات باز میشه 👇",
        reply_markup=ReplyKeyboardRemove()
    )

    await message.answer(
        "درود ،دوست عزیز! به ربات cipher connect خوش اومدی ✨\n\n"
        "🌐 اینترنت آزاد رو با ما تجربه کن!\n\n"
        "🟢 اتصال پایدار و با کیفیت\n\n"
        "⚡️ پرسرعت با کمترین پینگ\n\n"
        "🔒 اتصال ایمن و مطمئن\n\n"
        "⚪️ منصفانه‌ترین قیمت\n\n"
        "⏱ پشتیبانی ۲۴ ساعته\n\n"
        "🆔 @freeedomarea",
        reply_markup=main_menu_keyboard()
    )
