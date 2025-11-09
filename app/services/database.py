# app/services/database.py
import aiosqlite
import os
from datetime import datetime

DB_PATH = "data/database.db"

async def init_db():
    """ساخت دیتابیس و جدول users در اولین اجرای ربات"""
    os.makedirs("data", exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
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
        await db.commit()


async def add_user(telegram_id: int, username: str, first_name: str,
                   last_name: str, phone_number: str ,register_date:str| None):
    """افزودن یا به‌روزرسانی کاربر در دیتابیس"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (telegram_id, username, first_name, last_name, phone_number, register_date)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username=excluded.username,
                first_name=excluded.first_name,
                last_name=excluded.last_name,
                phone_number=excluded.phone_number
        """, (telegram_id, username, first_name, last_name, phone_number, register_date))
        await db.commit()


async def get_user(telegram_id: int):
    """گرفتن اطلاعات کاربر از دیتابیس"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cursor.fetchone()
        return row


async def set_user_joined(telegram_id: int, joined: bool):
    """ثبت وضعیت عضویت در کانال"""
    joined_val = 1 if joined else 0
    joined_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") if joined else None
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET is_joined = ?, joined_at = ? WHERE telegram_id = ?",
            (joined_val, joined_at, telegram_id)
        )
        await db.commit()


async def is_user_joined(telegram_id: int) -> bool:
    """بررسی اینکه کاربر عضو کانال اجباری شده یا نه"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT is_joined FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cursor.fetchone()
        return bool(row[0]) if row else False

async def set_marzban_username(telegram_id: int, marzban_username: str):
    """ذخیره نام کاربری پنل مرزبان برای این کاربر"""
    import aiosqlite
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET marzban_username = ? WHERE telegram_id = ?",
            (marzban_username, telegram_id)
        )
        await db.commit()


async def get_marzban_username(telegram_id: int):
    """برگرداندن marzban_username اگر قبلاً ذخیره شده باشد"""
    import aiosqlite
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT marzban_username FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row and row[0] else None


async def get_user_by_marzban(marzban_username: str):
    """پیدا کردن اطلاعات تلگرام از روی marzban username"""
    import aiosqlite
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT * FROM users WHERE marzban_username = ?",
            (marzban_username,)
        )
        row = await cursor.fetchone()
        return row


