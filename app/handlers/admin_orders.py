from aiogram import Router, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.services.database import update_order_status, get_order_by_id, get_user , add_marzban_account,get_marzban_account_by_user_plan,update_marzban_account_after_renew
from app.services.marzban_api import create_user_in_marzban,get_user_by_username,update_user_in_marzban,add_data_for_user_in_marzban
import os
from datetime import datetime, timedelta
from app.services.database import add_data_added,add_agent_income,increment_agent_buys,add_buy_price,is_agent
from app.services.database import get_user_price_for_plan,add_renew_price,add_gb_added
router = Router()

ORDERS_CHANNEL_ID = int(os.getenv("ORDERS_CHANNEL_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))
HELP_MESSAGE_URL = "https://t.me/wvpnw/556"

@router.callback_query(lambda c: c.data.startswith("order_approve_"))
async def approve_order(callback: types.CallbackQuery):
    
    
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
    order_type = order[9] if isinstance(order, (list, tuple)) else order["type"]
    
    if order_type == "renew":
        telegram_user_id  = order[1] if isinstance(order, (list, tuple)) else order["acc_id"]
        plan_name = order[2] if isinstance(order, (list, tuple)) else order["plan_name"]
        price = order[3] if isinstance(order, (list, tuple)) else order["price"]
        size_of_gg_in_order = order[5] if isinstance(order, (list, tuple)) else order["data_limit"]
        devicelimit = order[10] if isinstance(order, (list, tuple)) else order["user_limit"]
        # گرفتن اطلاعات حساب از دیتابیس
        account = await get_marzban_account_by_user_plan(telegram_user_id, plan_name)
        if not account:
            await callback.answer("❌ حساب در دیتابیس یافت نشد.", show_alert=True)
            return
        acc_id = account[0]
        panel_username = account[2]
        months = int(account[8])
        size_gb = float(account[9])
        
        # گرفتن اطلاعات فعلی از پنل
        marzban_user = await get_user_by_username(panel_username)
        if not marzban_user:
            await callback.answer("❌ دریافت اطلاعات از پنل ناموفق بود.", show_alert=True)
            return

        current_expire = marzban_user.get("expire") or 0

        # محاسبه expire جدید
        
        add_seconds = months * 30 * 24 * 60 * 60
        if current_expire:
            new_expire_ts = int((datetime.fromtimestamp(current_expire) + timedelta(seconds=add_seconds)).timestamp())
        else:
            
            new_expire_ts = int((datetime.utcnow() + timedelta(seconds=add_seconds)).timestamp())

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
                "خطایی در روند تایید رخ داد. لطفا خطاهارا بررسی کنید!")
            return

        # آپدیت دیتابیس محلی
        await update_marzban_account_after_renew(acc_id, new_expire_ts, size_gb)
        
        await callback.bot.send_message(
                ADMIN_ID,  
                "سفارش با موفقیت تأیید شد ✅")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="back_to_menu")]
            ])
        # پیام برای کاربر
        await callback.bot.send_message(
            account[1],  # telegram_user_id
            "✅ تمدید سرویس شما با موفقیت انجام شد!",
            reply_markup=keyboard
        )
        if await is_agent(user_id):
            if devicelimit == 3:
                Multip = 2
            elif devicelimit == 5:
                Multip = 3
            else:
                Multip = 1
            revenue = await get_user_price_for_plan(months, size_of_gg_in_order/Multip)
            
            revenue = revenue * Multip
            await increment_agent_buys(user_id)

            await add_renew_price(user_id, price)

            # درآمد نماینده 
            await add_agent_income(user_id, revenue)
        try:
            if callback.message.chat.type == "private":
                await callback.message.delete()
        except Exception as e:
            print(f"[DEBUG] Couldn't delete message: {e}")
        # If it was Add Data
    elif order_type == "add_data":
        telegram_user_id = order[1]
        plan_name = order[2]
        gb_to_add = order[5]   # this is the "size" field
        price = order[3]

        account = await get_marzban_account_by_user_plan(telegram_user_id, plan_name)
        if not account:
            await callback.answer("❌ حساب در دیتابیس یافت نشد.", show_alert=True)
            return

        acc_id = account[0]
        panel_username = account[2]
        
        # تبدیل گیگ به بایت
        add_bytes = int(gb_to_add * 1024 * 1024 * 1024)

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

        await callback.bot.send_message(
            telegram_user_id,
            f"✅ {gb_to_add} گیگابایت به سرویس شما اضافه شد!"
        )

        await callback.bot.send_message(
            ADMIN_ID,
            "سفارش اضافه‌حجم با موفقیت تأیید شد ✅"
        )
        if await is_agent(user_id):
            
            
            await add_data_added(user_id, price)

          
            await add_gb_added(user_id, gb_to_add)

         
            

        try:
            await callback.message.delete()
        except:
            pass

        return

    #if it was Buy
    else:
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
            devicelimit = order[10] if isinstance(order, (list, tuple)) else order["user_limit"]
            
            days = duration * 30
            expire_timestamp = int((datetime.utcnow() + timedelta(days)).timestamp())
            # تبدیل قیمت یا حجم به مشخصات پلن (موقت)
            # مثلا بر اساس نام کانفیگ، حجم و مدت مشخص کن
            sub_link = await create_user_in_marzban(username=Plan_name, data_limit_gb=data_limit, expire_days= days)
            await add_marzban_account(user_id,Plan_name,"Active",expire_timestamp,0,sub_link,duration,data_limit,devicelimit)
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📘 نحوه استفاده از لینک", url=HELP_MESSAGE_URL)],
                [InlineKeyboardButton(text="🔙 بازگشت به منو", callback_data="back_to_menu_without_del")]
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
        if await is_agent(user_id):
            if devicelimit == 3:
                Multip = 2
            elif devicelimit == 5:
                Multip = 3
            else:
                Multip = 1
            revenue = await get_user_price_for_plan(duration, data_limit/Multip)
            
            revenue = revenue * Multip
            await increment_agent_buys(user_id)

            # جمع مبلغ خرید
            await add_buy_price(user_id, price)

            # درآمد نماینده 
            await add_agent_income(user_id, revenue)
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
    
