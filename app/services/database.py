import aiosqlite
import os
from datetime import datetime

DB_PATH = "data/database.db"

# 🧱 ساخت جداول
async def init_db():
    """ایجاد دیتابیس و جداول مورد نیاز در اولین اجرای ربات"""
    os.makedirs("data", exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        # جدول کاربران تلگرام
        await db.execute("""
            CREATE TABLE IF NOT EXISTS telegram_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                phone_number TEXT,
                register_date TEXT,
                is_joined INTEGER DEFAULT 0,
                joined_at TEXT
            )
        """)

        # جدول حساب‌های مرزبان
        await db.execute("""
            CREATE TABLE IF NOT EXISTS marzban_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id INTEGER,
                panel_username TEXT,
                status TEXT,
                expire INTEGER,
                used_traffic INTEGER,
                subscription_url TEXT,
                last_sync TEXT,
                FOREIGN KEY (telegram_user_id) REFERENCES telegram_users(id) ON DELETE CASCADE
            )
        """)
        await db.commit()

# 🧩 کاربران تلگرام
async def add_user(telegram_id: int, username: str, first_name: str,
                   last_name: str, phone_number: str, register_date: str | None):
    """افزودن یا به‌روزرسانی کاربر تلگرام"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO telegram_users (telegram_id, username, first_name, last_name, phone_number, register_date)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username=excluded.username,
                first_name=excluded.first_name,
                last_name=excluded.last_name,
                phone_number=excluded.phone_number
        """, (telegram_id, username, first_name, last_name, phone_number, register_date))
        await db.commit()

async def get_user(telegram_id: int):
    """گرفتن اطلاعات کاربر تلگرام"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT * FROM telegram_users WHERE telegram_id = ?", (telegram_id,))
        row = await cursor.fetchone()
        return row

async def get_user_id(telegram_id: int) -> int | None:
    """دریافت ID داخلی کاربر (برای ارتباط با جدول حساب‌ها)"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT id FROM telegram_users WHERE telegram_id = ?", (telegram_id,))
        row = await cursor.fetchone()
        return row[0] if row else None

async def set_user_joined(telegram_id: int, joined: bool):
    """ثبت وضعیت عضویت در کانال"""
    joined_val = 1 if joined else 0
    joined_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") if joined else None
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE telegram_users SET is_joined = ?, joined_at = ? WHERE telegram_id = ?",
            (joined_val, joined_at, telegram_id)
        )
        await db.commit()

async def is_user_joined(telegram_id: int) -> bool:
    """بررسی وضعیت عضویت"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT is_joined FROM telegram_users WHERE telegram_id = ?", (telegram_id,))
        row = await cursor.fetchone()
        return bool(row[0]) if row else False

# 🧩 حساب‌های مرزبان
async def add_marzban_account(telegram_user_id: int, panel_username: str, status: str = None,
                              expire: int = None, used_traffic: int = None,
                              subscription_url: str = None):
    """افزودن حساب جدید مرزبان برای کاربر"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO marzban_accounts (telegram_user_id, panel_username, status, expire, used_traffic, subscription_url, last_sync)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (telegram_user_id, panel_username, status, expire, used_traffic, subscription_url,
              datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))
        await db.commit()

async def get_marzban_accounts_by_user(telegram_user_id: int):
    """دریافت تمام حساب‌های مرزبان مرتبط با کاربر تلگرام"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT * FROM marzban_accounts WHERE telegram_user_id = ?", (telegram_user_id,))
        rows = await cursor.fetchall()
        return rows

async def update_marzban_account(panel_username: str, status: str = None,
                                 expire: int = None, used_traffic: int = None,
                                 subscription_url: str = None):
    """به‌روزرسانی اطلاعات حساب خاص"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE marzban_accounts
            SET status = ?, expire = ?, used_traffic = ?, subscription_url = ?, last_sync = ?
            WHERE panel_username = ?
        """, (status, expire, used_traffic, subscription_url,
              datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"), panel_username))
        await db.commit()

async def delete_marzban_account(panel_username: str):
    """حذف یک حساب مرزبان"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM marzban_accounts WHERE panel_username = ?", (panel_username,))
        await db.commit()
