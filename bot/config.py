import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Load .env file
load_dotenv(BASE_DIR / ".env")

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "").strip()
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "").strip().lstrip("@")
SUPPORT_USERNAME = os.getenv("SUPPORT_USERNAME", "Keb_g").strip().lstrip("@")

STORE_NAME = os.getenv("STORE_NAME", "Selora Prints")
STORE_LOCATION = os.getenv("STORE_LOCATION", "Ledeta, Addis Ababa")
YANGO_DELIVERY_NOTE = os.getenv(
    "YANGO_DELIVERY_NOTE", 
    "Delivered by Yango across Addis Ababa (delivery fee paid by the customer upon receipt)."
)
STORE_PICKUP_NOTE = os.getenv(
    "STORE_PICKUP_NOTE", 
    "Free pickup directly from our store in Ledeta."
)

# Payment configuration (50% Pre-payment)
PAYMENT_CBE_ACCOUNT = os.getenv("PAYMENT_CBE_ACCOUNT", "1000056873639").strip()
PAYMENT_CBE_NAME = os.getenv("PAYMENT_CBE_NAME", os.getenv("PAYMENT_ACCOUNT_NAME", "Nani Asmelash")).strip()

PAYMENT_TELEBIRR = os.getenv("PAYMENT_TELEBIRR", "0906287728").strip()
PAYMENT_TELEBIRR_NAME = os.getenv("PAYMENT_TELEBIRR_NAME", "Kebron Girma").strip()

PAYMENT_DEPOSIT_PERCENT = int(os.getenv("PAYMENT_DEPOSIT_PERCENT", "50"))

# Daily Production Capacity & Rush Scheduling (One-man print shop rules)
MAX_DAILY_ORDERS = int(os.getenv("MAX_DAILY_ORDERS", "100"))
MAX_DAILY_RUSH_ORDERS = int(os.getenv("MAX_DAILY_RUSH_ORDERS", "50"))
RUSH_ORDER_FEE = int(os.getenv("RUSH_ORDER_FEE", "200"))

# Dynamic Web Dashboard & Authentication
DASHBOARD_HOST = os.getenv("DASHBOARD_HOST", "0.0.0.0").strip()
DASHBOARD_PORT = int(os.getenv("PORT", os.getenv("DASHBOARD_PORT", "8000")))
DASHBOARD_PUBLIC_URL = os.getenv("DASHBOARD_PUBLIC_URL", "https://selora-ck7t.onrender.com").strip()
DASHBOARD_USERNAME = os.getenv("DASHBOARD_USERNAME", "admin").strip()
DASHBOARD_PASSWORD = os.getenv("DASHBOARD_PASSWORD", "selora2026").strip()
SECRET_KEY = os.getenv("SECRET_KEY", "selora_prints_secret_key_2026_xyz").strip()
