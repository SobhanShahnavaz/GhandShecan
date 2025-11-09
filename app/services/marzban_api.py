import os
import aiohttp
import asyncio
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

MARZBAN_URL = os.getenv("BASE_URL")
MARZBAN_USER = os.getenv("MARZBAN_API_UN")
MARZBAN_PASS = os.getenv("MARZBAN_API_PSW")


_cached_token = None
_token_expiry = None


async def _request_token():
    """
    درخواست توکن جدید از Marzban API
    """
    global _cached_token, _token_expiry
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                f"{MARZBAN_URL}/api/admin/token",
                data={"username": MARZBAN_USER, "password": MARZBAN_PASS},
                timeout=10
            ) as resp:
                data = await resp.json()
                if resp.status == 200 and "access_token" in data:
                    _cached_token = data["access_token"]
                    # توکن معمولاً 24 ساعته است → تاریخ انقضا
                    _token_expiry = datetime.now() + timedelta(hours=23)
                    print("✅ Token refreshed successfully.")
                    return _cached_token
                else:
                    print(f"❌ Token request failed: {resp.status} -> {data}")
                    return None
        except Exception as e:
            print(f"🔥 Token request exception: {e}")
            return None


async def _get_valid_token():
    """
    اگر توکن معتبر است، همان را برگردان.
    اگر منقضی شده، دوباره بساز.
    """
    global _cached_token, _token_expiry
    if _cached_token and _token_expiry and datetime.now() < _token_expiry:
        return _cached_token
    else:
        return await _request_token()


async def get_users():
    """
    دریافت لیست کاربران از پنل مارزبان
    """
    token = await _get_valid_token()
    if not token:
        print("❌ No valid token available.")
        return None

    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{MARZBAN_URL}/api/users", headers=headers) as resp:
                data = await resp.json()
                if resp.status == 200:
                    print(f"✅ Users fetched: {len(data.get('users', []))} users.")
                    return data
                elif resp.status == 401:
                    print("⚠️ Token expired, refreshing...")
                    await _request_token()
                    return await get_users()  # دوباره تلاش کن
                else:
                    print(f"❌ Users request failed: {resp.status} -> {data}")
                    return None
        except Exception as e:
            print(f"🔥 Users request exception: {e}")
            return None


async def get_user_by_username(username: str):
    """
    تلاش می‌کند اطلاعات کاربر را با /api/users/{username} بگیرد.
    اگر پیدا نشد، از /api/users (لیست) فیلتر می‌کند.
    """
    token = await _get_valid_token()
    if not token:
        print("❌ No valid token available.")
        return None

    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}
    url_direct = f"{MARZBAN_URL}/api/users/{username}"

    async with aiohttp.ClientSession() as session:
        try:
            # --- تلاش مستقیم با username ---
            async with session.get(url_direct, headers=headers, timeout=10) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    print(f"✅ User '{username}' fetched directly.")
                    return data
                elif resp.status == 404:
                    print(f"⚠️ Direct fetch failed, trying fallback search...")
                elif resp.status == 401:
                    print("⚠️ Token expired, refreshing...")
                    await _request_token()
                    return await get_user_by_username(username)

            # --- Fallback: از کل لیست پیدا کن ---
            async with session.get(f"{MARZBAN_URL}/api/users", headers=headers, timeout=10) as resp2:
                if resp2.status == 200:
                    data = await resp2.json()
                    users = data.get("users", [])
                    for u in users:
                        if u.get("username", "").lower() == username.lower():
                            print(f"✅ User '{username}' found via fallback search.")
                            return u
                    print(f"❌ User '{username}' not found in fallback list.")
                    return None
                else:
                    print(f"❌ Fallback request failed: {resp2.status}")
                    return None

        except Exception as e:
            print(f"🔥 Exception in get_user_by_username: {e}")
            return None



# === برای تست مستقیم اجرا کن ===
if __name__ == "__main__":
    async def test():
        print("🔹 Testing Marzban API connection...\n")
        users = await get_users()
        if users:
            for u in users.get("users", [])[:5]:
                print(f"👤 {u['username']} | status: {u['status']}")

    asyncio.run(test())
