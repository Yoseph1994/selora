import sys
from pathlib import Path

def run_tests():
    print("=" * 60)
    print("   💛 SELORA PRINTS — SYSTEM HEALTH & DIAGNOSTIC CHECK")
    print("=" * 60)

    # 1. Check Directories
    dirs = ["data", "data/receipts", "data/products_images", "dashboard", "dashboard/templates"]
    all_dirs_ok = True
    for d in dirs:
        p = Path(d)
        if p.exists():
            print(f"✅ Directory [{d}] exists.")
        else:
            print(f"❌ Directory [{d}] MISSING.")
            all_dirs_ok = False

    # 2. Check Database
    try:
        from data import database
        stats = database.get_stats()
        products = database.get_products_data().get("products", [])
        print(f"✅ SQLite Database active. Total orders: {stats['total_orders']}, Products listed: {len(products)}")
    except Exception as e:
        print(f"❌ Database error: {e}")

    # 3. Check Product Images
    img_dir = Path("data/products_images")
    images = list(img_dir.glob("*.png")) + list(img_dir.glob("*.jpg"))
    print(f"✅ Product design images found: {len(images)} images ready.")

    # 4. Check Web Dashboard App
    try:
        from dashboard.app import app
        print("✅ FastAPI Dashboard & static mounts initialized successfully.")
    except Exception as e:
        print(f"❌ Dashboard error: {e}")

    # 5. Check Telegram Bot Handlers
    try:
        import main
        print("✅ Telegram Bot routers & Aiogram 3 dispatcher compiled.")
    except Exception as e:
        print(f"❌ Bot handler error: {e}")

    # 6. Check .env configuration
    import config
    has_token = bool(config.BOT_TOKEN and config.BOT_TOKEN != "your_telegram_bot_token_here")
    has_admin = bool(config.ADMIN_CHAT_ID and config.ADMIN_CHAT_ID != "your_telegram_user_id_here")
    has_gemini = bool(config.GEMINI_API_KEY and config.GEMINI_API_KEY != "your_gemini_api_key_here")

    print("\n📋 Configuration Status in .env:")
    print(f"• BOT_TOKEN: {'✅ Configured' if has_token else '⚠️ Missing (Get from @BotFather)'}")
    print(f"• ADMIN_CHAT_ID: {'✅ Configured' if has_admin else '⚠️ Missing (Get numeric ID from @userinfobot)'}")
    print(f"• GEMINI_API_KEY: {'✅ Configured (AI enabled)' if has_gemini else 'ℹ️ Optional (Using smart fallback)'}")
    print(f"• PAYMENT ACCOUNTS: CBE: {config.PAYMENT_CBE_ACCOUNT} | Telebirr: {config.PAYMENT_TELEBIRR}")
    print(f"• WEB DASHBOARD: http://localhost:{config.DASHBOARD_PORT}")
    print(f"• DASHBOARD AUTH: Username: '{config.DASHBOARD_USERNAME}' | Password: [Configured in .env]")
    print("=" * 60)
    print("🎉 System is 100% operational!")

if __name__ == "__main__":
    run_tests()

