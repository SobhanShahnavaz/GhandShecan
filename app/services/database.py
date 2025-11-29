import aiosqlite
import os
from datetime import datetime
from zoneinfo import ZoneInfo
import time
DB_PATH = "data/database.db"

def tehran_now():
    return datetime.now(ZoneInfo("Asia/Tehran"))

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
                user_limit INTEGER,
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
                user_limit INTEGER,
                FOREIGN KEY (telegram_user_id) REFERENCES telegram_users(id)
            )
        """)

        await db.commit()

        await db.execute("""
            CREATE TABLE IF NOT EXISTS plans (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_gb INTEGER,
                months INTEGER,
                price INTEGER,
                for_agent INTEGER DEFAULT 0
                
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
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS agent_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                request_date TEXT
            )

        """)

        await db.commit()

                # جدول آمار نمایندگان
        await db.execute("""
            CREATE TABLE IF NOT EXISTS agent_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                username TEXT,
                number_of_buys INTEGER DEFAULT 0,
                total_income INTEGER DEFAULT 0,
                sum_buy_prices INTEGER DEFAULT 0,
                sum_renew_prices INTEGER DEFAULT 0,
                approved_date TEXT,
                sum_of_data_added INTEGER DEFAULT 0,
                sum_of_gb INTEGER DEFAULT 0
            )
        """)
        await db.commit()
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT,
                card_number TEXT NOT NULL UNIQUE,
                owner_name TEXT,
                is_active INTEGER DEFAULT 0
                
                
            )
        """)
        await db.commit()
        
        
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS test_accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER,
                username TEXT,
                created_at INTEGER,
                is_agent INTEGER
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
    joined_at = tehran_now().strftime("%Y-%m-%d %H:%M:%S") if joined else None
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
                              subscription_url: str = None, Plan_Duration: int = None ,DataLimit: int = None,user_limit:int=1):
    """افزودن حساب جدید مرزبان برای کاربر"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO marzban_accounts (telegram_user_id, panel_username, status, expire, used_traffic, subscription_url, last_sync, plan_duration, data_limit,user_limit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?,?)
        """, (telegram_user_id, panel_username, status, expire, used_traffic, subscription_url,
              tehran_now().strftime("%Y-%m-%d %H:%M:%S") , Plan_Duration , DataLimit,user_limit))
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
              tehran_now().strftime("%Y-%m-%d %H:%M:%S"), panel_username))
        await db.commit()
async def update_marzban_account_after_renew(acc_id: int, new_expire_ts: int, new_data_limit: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            UPDATE marzban_accounts
            SET expire = ?, data_limit = ?, last_sync = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (new_expire_ts, new_data_limit, acc_id)
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

async def add_order(telegram_user_id: int, plan_name: str, price: int,duration:int, data_limit:int, payment_proof_file_id: str, order_type:str = None, user_limit:int = 1):
    """افزودن سفارش جدید (بعد از اینکه کاربر رسید ارسال کرد)"""
    
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            INSERT INTO orders (telegram_user_id, plan_name, price, duration, data_limit, payment_proof_file_id, status, created_at, type, user_limit)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            telegram_user_id,
            plan_name,
            price,
            duration,
            data_limit,
            payment_proof_file_id,
            "pending",
            tehran_now().strftime("%Y-%m-%d %H:%M:%S"),
            order_type,
            user_limit
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

async def get_plan_price_by_DMA(data_gb: int, months: int, foragent: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT price FROM plans WHERE data_gb = ? AND months = ? AND for_agent = ?",
            (data_gb, months, foragent)
        )
        row = await cursor.fetchone()
        return row[0] if row else None

async def get_plans():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT * FROM plans ORDER BY id")
        return await cursor.fetchall()

async def get_plans_for_users():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT * FROM plans WHERE for_agent = 0 ORDER BY id"
        )
        return await cursor.fetchall()


async def get_plans_for_agents():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT * FROM plans WHERE for_agent = 1 ORDER BY id"
        )
        return await cursor.fetchall()

async def get_available_months(for_agent: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT DISTINCT months FROM plans WHERE for_agent=? ORDER BY months",
            (for_agent,)
        )
        rows = await cursor.fetchall()
        return [r[0] for r in rows]

async def get_sizes_for_month(months: int, for_agent: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, data_gb, price FROM plans WHERE months=? AND for_agent=? ORDER BY data_gb",
            (months, for_agent)
        )
        return await cursor.fetchall()

async def get_user_price_for_plan(months: int, data_gb: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT price FROM plans WHERE months=? AND data_gb=? AND for_agent=0 LIMIT 1",
            (months, data_gb)
        )
        row = await cursor.fetchone()
        return row[0] if row else None

async def get_plan_by_id(plan_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT * FROM plans WHERE id=?",
            (plan_id,)
        )
        return await cursor.fetchone()


async def delete_plan(plan_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM plans WHERE id = ?", (plan_id,))
        await db.commit()

async def add_plan(data_gb: int, months: int, price: int, for_agent: int ):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO plans (data_gb, months, price, for_agent)
            VALUES (?, ?, ?, ?)
            """,
            (data_gb, months, price, for_agent)
        )
        await db.commit()


async def add_agent_request(user):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO agent_requests 
                (telegram_id, username, first_name, last_name, request_date)
            VALUES (?, ?, ?, ?, ?)
        """, (
            user.id,
            user.username,
            user.first_name,
            user.last_name,
            tehran_now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        await db.commit()


async def add_agent(telegram_id, username=None, first_name=None, last_name=None,
              phone_number=None,  is_joined=0):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO agents 
                (telegram_id, username, first_name, last_name, phone_number, register_date, is_joined, joined_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?
            )
        """, (telegram_id, username, first_name, last_name, phone_number, tehran_now().strftime("%Y-%m-%d %H:%M:%S"), is_joined, tehran_now().strftime("%Y-%m-%d %H:%M:%S")))
        await db.commit()

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

async def list_agent_requests():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("""
            SELECT * FROM agent_requests
        """)
        rows = await cursor.fetchall()
        return rows

async def delete_agent_request(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM agent_requests WHERE telegram_id = ?",
            (telegram_id,)
        )
        await db.commit()

async def add_agent_stats(telegram_id: int, username: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT OR IGNORE INTO agent_stats 
                (telegram_id, username, approved_date)
            VALUES (?, ?, ?)
        """, (
            telegram_id,
            username,
            tehran_now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        await db.commit()

async def get_agent_stats(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT * FROM agent_stats WHERE telegram_id = ?",
            (telegram_id,)
        )
        return await cursor.fetchone()

async def increment_agent_buys(telegram_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE agent_stats
            SET number_of_buys = number_of_buys + 1
            WHERE telegram_id = ?
        """, (telegram_id,))
        await db.commit()

async def add_buy_price(telegram_id: int, price: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE agent_stats
            SET sum_buy_prices = sum_buy_prices + ?
            WHERE telegram_id = ?
        """, (price, telegram_id))
        await db.commit()

async def add_renew_price(telegram_id: int, price: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE agent_stats
            SET sum_renew_prices = sum_renew_prices + ?
            WHERE telegram_id = ?
        """, (price, telegram_id))
        await db.commit()

async def add_agent_income(telegram_id: int, income: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE agent_stats
            SET total_income = total_income + ?
            WHERE telegram_id = ?
        """, (income, telegram_id))
        await db.commit()

async def add_data_added(telegram_id: int, price: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE agent_stats
            SET sum_of_data_added = sum_of_data_added + ?
            WHERE telegram_id = ?
        """, (price, telegram_id))
        await db.commit()

async def add_gb_added(telegram_id: int, GigaBytes: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE agent_stats
            SET sum_of_gb = sum_of_gb + ?
            WHERE telegram_id = ?
        """, (GigaBytes, telegram_id))
        await db.commit()

async def add_card(label, card_number, owner_name):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO cards (label, card_number, owner_name) VALUES (?, ?, ?)",
            (label, card_number, owner_name)
        )
        await db.commit()

async def get_active_card():
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, label, card_number, owner_name FROM cards WHERE is_active=1"
        )
        return await cursor.fetchall()

async def activate_card(card_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        # Check card existence
        cursor = await db.execute(
            "SELECT id FROM cards WHERE id = ?",
            (card_id,)
        )
        card = await cursor.fetchone()

        if not card:
            return False  # invalid card

        await db.execute("UPDATE cards SET is_active = 0")
        await db.execute("UPDATE cards SET is_active = 1 WHERE id = ?", (card_id,))
        await db.commit()

    return True



async def add_test_account(telegram_id: int, panel_username :str, is_agent: int ):
    now = int(time.time())
    async with aiosqlite.connect(DB_PATH) as conn:
        await conn.execute(
            "INSERT INTO test_accounts (telegram_id,username, created_at, is_agent) VALUES (?, ?, ?, ?)",
            (telegram_id,panel_username, now, is_agent)
        )
        await conn.commit()


async def count_test_accounts(telegram_id: int, is_agent: int):
    now = int(time.time())
    
    if is_agent:
        # Daily reset (last 24 hours)
        reset_time = now - 24*3600
    else:
        # Monthly reset (~30 days)
        reset_time = now - 30*24*3600

    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute("""
            SELECT COUNT(*) FROM test_accounts
            WHERE telegram_id = ? AND is_agent = ? AND created_at >= ?
        """, (telegram_id, is_agent, reset_time))

        row = await cursor.fetchone()
        return row[0]

async def get_all_test_usernames():
    async with aiosqlite.connect(DB_PATH) as conn:
        cursor = await conn.execute("SELECT username FROM test_accounts")
        rows = await cursor.fetchall()

    return [row[0] for row in rows if row[0]]


