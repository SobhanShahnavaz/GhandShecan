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
                plan_duration INTEGER,
                data_limit INTEGER,
                FOREIGN KEY (telegram_user_id) REFERENCES telegram_users(id) ON DELETE CASCADE
            )
        """)
        await db.commit()

        # جدول سفارش‌ها (پرداخت‌ها)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_user_id INTEGER,
                plan_name TEXT,
                price INTEGER,
                duration INTEGER,
                data_limit INTEGER,
                payment_proof_file_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                type TEXT,
                FOREIGN KEY (telegram_user_id) REFERENCES telegram_users(id)
            )
        """)

        await db.commit()

        await db.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_gb INTEGER,
                months INTEGER,
                price INTEGER
            )
        """)

        await db.commit()

        await db.execute("""
            CREATE TABLE IF NOT EXISTS agents (
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
                              subscription_url: str = None, Plan_Duration: int = None ,DataLimit: int = None):
    """افزودن حساب جدید مرزبان برای کاربر"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO marzban_accounts (telegram_user_id, panel_username, status, expire, used_traffic, subscription_url, last_sync, plan_duration, data_limit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (telegram_user_id, panel_username, status, expire, used_traffic, subscription_url,
              datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") , Plan_Duration , DataLimit))
        await db.commit()

async def get_marzban_accounts_by_user(telegram_user_id: int):
    """دریافت تمام حساب‌های مرزبان مرتبط با کاربر تلگرام"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT * FROM marzban_accounts WHERE telegram_user_id = ?", (telegram_user_id,))
        rows = await cursor.fetchall()
        return rows
async def get_marzban_account_by_id(ID: int):
    """دریافت تمام حساب‌های مرزبان مرتبط با کاربر تلگرام"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT * FROM marzban_accounts WHERE id = ?", (ID,))
        rows = await cursor.fetchone()
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
async def update_marzban_account_after_renew(acc_id: int, new_expire_ts: int, new_data_limit: int, used_traffic: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE marzban_accounts
            SET expire = ?, data_limit = ?, used_traffic = ?, last_sync = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_expire_ts, new_data_limit, used_traffic, acc_id)
        )
        await db.commit()

async def get_marzban_account_by_user_plan(telegram_user_id: int, plan_name: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            """
            SELECT * FROM marzban_accounts
            WHERE telegram_user_id = ? AND panel_username = ?
            LIMIT 1
            """,
            (telegram_user_id, plan_name)
        )
        row = await cursor.fetchone()
        return row


async def delete_marzban_account(Account_id: str):
    """حذف یک حساب مرزبان"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM marzban_accounts WHERE id = ?", (Account_id,))
        await db.commit()

# 🧾 جدول سفارش‌ها (پرداخت‌ها)

async def add_order(telegram_user_id: int, plan_name: str, price: int,duration:int, data_limit:int, payment_proof_file_id: str, order_type:str = None):
    """افزودن سفارش جدید (بعد از اینکه کاربر رسید ارسال کرد)"""
    from datetime import datetime
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO orders (telegram_user_id, plan_name, price, duration, data_limit, payment_proof_file_id, status, created_at, type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            telegram_user_id,
            plan_name,
            price,
            duration,
            data_limit,
            payment_proof_file_id,
            "pending",
            datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            order_type
        ))
        await db.commit()
        return cursor.lastrowid 


async def get_pending_orders():
    """دریافت همه سفارش‌های در حالت pending (برای ادمین)"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT * FROM orders WHERE status = 'pending' ORDER BY created_at DESC
        """)
        rows = await cursor.fetchall()
        return rows


async def get_orders_by_user(telegram_user_id: int):
    """دریافت تمام سفارش‌های یک کاربر خاص"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT * FROM orders WHERE telegram_user_id = ? ORDER BY created_at DESC
        """, (telegram_user_id,))
        rows = await cursor.fetchall()
        return rows


async def get_order_by_id(order_id: int):
    """دریافت اطلاعات یک سفارش خاص"""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT * FROM orders WHERE id = ?", (order_id,))
        row = await cursor.fetchone()
        return row


async def update_order_status(order_id: int, new_status: str):
    """به‌روزرسانی وضعیت سفارش (مثلاً به approved یا rejected)"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE orders
            SET status = ?
            WHERE id = ?
        """, (new_status, order_id))
        await db.commit()

async def get_plan_price(data_gb: int, months: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT price FROM plans WHERE data_gb = ? AND months = ?",
            (data_gb, months)
        )
        row = await cursor.fetchone()
        return row[0] if row else None


async def add_agent(telegram_id, username=None, first_name=None, last_name=None,
              phone_number=None, register_date=None, is_joined=0, joined_at=None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO agents 
                (telegram_id, username, first_name, last_name, phone_number, register_date, is_joined, joined_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?
            )
        """, (telegram_id, username, first_name, last_name, phone_number, register_date, is_joined, joined_at))
        db.commit()

async def get_agent(telegram_id):
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute("SELECT * FROM agents WHERE telegram_id = ?", (telegram_id,))
        row = await cursor.fetchone()
        return row

async def is_agent(telegram_id):
    return await get_agent(telegram_id) is not None


async def list_agents():
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute("SELECT * FROM agents ORDER BY id DESC")
        row = await cursor.fetchall()
        return row

async def remove_agent(telegram_id):
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute("DELETE FROM agents WHERE telegram_id = ?", (telegram_id,))
        conn.commit()

