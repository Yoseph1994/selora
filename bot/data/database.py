import os
import re
import json
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent
DB_PATH = DATA_DIR / "selora_orders.db"

# Default seed catalog, styles, and portfolio when initializing an empty database
# High-resolution, aesthetic curated photography matching each custom print item
DEFAULT_PRODUCTS = [
    {
        "id": "stickers",
        "name": "🏷 Stickers",
        "price": 20.0,
        "unit": "per piece",
        "min_order": 15,
        "description": "High-quality custom printed stickers, vibrant colors and durable finish. Minimum order: 15 pieces.",
        "image_url": "https://images.unsplash.com/photo-1589384267710-7a170981ca78?auto=format&fit=crop&w=800&q=80",
        "has_ready_designs": True
    },
    {
        "id": "bookmarks",
        "name": "🔖 Bookmarks",
        "price": 50.0,
        "unit": "per piece",
        "min_order": 2,
        "description": "Beautiful custom printed bookmarks for book lovers and students. Minimum order: 2 pieces.",
        "image_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=800&q=80",
        "has_ready_designs": True
    },
    {
        "id": "business_cards",
        "name": "💼 Business Cards",
        "price": 10.0,
        "unit": "per piece",
        "min_order": 50,
        "description": "Professional high-resolution business cards for your brand and networking. Minimum order: 50 pieces.",
        "image_url": "https://images.unsplash.com/photo-1616628188859-7a11abb6fcc9?auto=format&fit=crop&w=800&q=80",
        "has_ready_designs": True
    },
    {
        "id": "polaroid",
        "name": "📸 Polaroid Prints",
        "price": None,
        "unit": "per piece",
        "min_order": 10,
        "description": "Classic vintage-style polaroid photo prints of your personal photos and memories. Minimum order: 10 pieces.",
        "image_url": "https://images.unsplash.com/photo-1526047932273-341f2a7631f9?auto=format&fit=crop&w=800&q=80",
        "has_ready_designs": False
    },
    {
        "id": "mini_notebook",
        "name": "📓 Mini Notebook",
        "price": 200.0,
        "unit": "each",
        "min_order": 1,
        "description": "Compact, portable pocket-sized notebook for quick notes and sketches.",
        "image_url": "https://images.unsplash.com/photo-1517842645767-c639042777db?auto=format&fit=crop&w=800&q=80",
        "has_ready_designs": True
    },
    {
        "id": "notebook",
        "name": "📔 Notebook",
        "price": 500.0,
        "unit": "each",
        "min_order": 1,
        "description": "Standard custom branded/aesthetic notebook with high quality paper.",
        "image_url": "https://images.unsplash.com/photo-1544816155-12df9643f363?auto=format&fit=crop&w=800&q=80",
        "has_ready_designs": True
    },
    {
        "id": "minibook_white",
        "name": "📖 Mini Book (White)",
        "price": 600.0,
        "unit": "each",
        "min_order": 1,
        "description": "Custom bound pocket minibook with elegant white cover. Personal photos album.",
        "image_url": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?auto=format&fit=crop&w=800&q=80",
        "has_ready_designs": False
    },
    {
        "id": "minibook_black",
        "name": "📖 Mini Book (Black)",
        "price": 700.0,
        "unit": "each",
        "min_order": 1,
        "description": "Sleek custom bound pocket minibook with premium black cover. Personal photos album.",
        "image_url": "https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=800&q=80",
        "has_ready_designs": False
    },
    {
        "id": "book_medium",
        "name": "📖 Medium Photo Book",
        "price": 800.0,
        "unit": "each",
        "min_order": 1,
        "description": "Medium-sized custom photo book for your personal memories with high-res binding.",
        "image_url": "https://images.unsplash.com/photo-1497633762265-9d179a990aa6?auto=format&fit=crop&w=800&q=80",
        "has_ready_designs": False
    },
    {
        "id": "book_a5",
        "name": "📖 A5 Photo Book",
        "price": 1000.0,
        "unit": "each",
        "min_order": 1,
        "description": "A5 premium custom bound photo book for personal collections and special occasions.",
        "image_url": "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?auto=format&fit=crop&w=800&q=80",
        "has_ready_designs": False
    },
    {
        "id": "book_a4",
        "name": "📖 A4 Photo Book",
        "price": 1500.0,
        "unit": "each",
        "min_order": 1,
        "description": "Large A4 luxury custom photo book for portfolios, weddings, and milestones.",
        "image_url": "https://images.unsplash.com/photo-1516979187457-637abb4f9353?auto=format&fit=crop&w=800&q=80",
        "has_ready_designs": False
    },
    {
        "id": "mug",
        "name": "☕ Mug",
        "price": 1500.0,
        "unit": "each",
        "min_order": 1,
        "description": "Custom printed ceramic mug, dishwasher and microwave safe. Great for gifts!",
        "image_url": "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?auto=format&fit=crop&w=800&q=80",
        "has_ready_designs": True
    },
    {
        "id": "puzzle",
        "name": "🧩 Puzzle",
        "price": 1500.0,
        "unit": "each",
        "min_order": 1,
        "description": "Personalized custom photo jigsaw puzzle made from your favorite photo.",
        "image_url": "https://images.unsplash.com/photo-1588702547919-26089e690ecc?auto=format&fit=crop&w=800&q=80",
        "has_ready_designs": False
    },
    {
        "id": "sticker_poster_a5",
        "name": "🟢 Sticker Poster A5",
        "price": 40.0,
        "unit": "per piece",
        "min_order": 10,
        "description": "Peel & stick wall/glass/smooth surface poster in A5 size. Minimum order: 10 pieces.",
        "image_url": "https://images.unsplash.com/photo-1579783900882-c0d3dad7b119?auto=format&fit=crop&w=800&q=80",
        "has_ready_designs": True
    },
    {
        "id": "sticker_poster_a4",
        "name": "🟢 Sticker Poster A4",
        "price": 70.0,
        "unit": "per piece",
        "min_order": 10,
        "description": "Peel & stick wall/glass/smooth surface poster in A4 size. Minimum order: 10 pieces.",
        "image_url": "https://images.unsplash.com/photo-1513519245088-0e12902e5a38?auto=format&fit=crop&w=800&q=80",
        "has_ready_designs": True
    }
]

DEFAULT_DESIGNS = [
    {
        "id": "des_stickers_1",
        "title": "Studio Ghibli Aesthetic Pack",
        "product_id": "stickers",
        "product_name": "🏷 Stickers",
        "subproduct": "Studio Ghibli Anime",
        "category": "Anime & Ghibli",
        "description": "Whimsical watercolor characters and scenes inspired by Miyazaki classics.",
        "image_url": "https://images.unsplash.com/photo-1563089145-599997674d42?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": "des_stickers_2",
        "title": "Vintage Coffee & Cozy Books",
        "product_id": "stickers",
        "product_name": "🏷 Stickers",
        "subproduct": "Vintage & Coffee",
        "category": "Vintage & Aesthetic",
        "description": "Warm muted earth tones featuring lattes, antique typewriters, and autumn leaves.",
        "image_url": "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": "des_stickers_3",
        "title": "Daily Wisdom & Self-Care Quotes",
        "product_id": "stickers",
        "product_name": "🏷 Stickers",
        "subproduct": "Typography & Quotes",
        "category": "Typography",
        "description": "Modern bold typography and uplifting affirmations in warm gold and pastel colors.",
        "image_url": "https://images.unsplash.com/photo-1555421689-491a97ff2040?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": "des_bookmarks_1",
        "title": "Dark Academia Library & Constellations",
        "product_id": "bookmarks",
        "product_name": "🔖 Bookmarks",
        "subproduct": "Dark Academia",
        "category": "Dark Academia",
        "description": "Gothic arches, golden celestial star maps, and moody Renaissance oil painting textures.",
        "image_url": "https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": "des_bookmarks_2",
        "title": "Pressed Wildflower Watercolor",
        "product_id": "bookmarks",
        "product_name": "🔖 Bookmarks",
        "subproduct": "Floral & Botanicals",
        "category": "Floral & Nature",
        "description": "Delicate botanicals with pressed lavender, chamomile, and soft pastel greenery.",
        "image_url": "https://images.unsplash.com/photo-1508615039623-a25605d2b022?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": "des_cards_1",
        "title": "Monochrome Executive Clean",
        "product_id": "business_cards",
        "product_name": "💼 Business Cards",
        "subproduct": "Modern Corporate",
        "category": "Minimalist",
        "description": "High-contrast minimalist layout ideal for tech founders, lawyers, and consultants.",
        "image_url": "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": "des_cards_2",
        "title": "Matte Black & Gold Luxury Foil",
        "product_id": "business_cards",
        "product_name": "💼 Business Cards",
        "subproduct": "Luxury & Foil",
        "category": "Luxury",
        "description": "Ultra-premium textured black cardstock simulation with elegant gold metallic accents.",
        "image_url": "https://images.unsplash.com/photo-1616628188859-7a11abb6fcc9?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": "des_polaroid_1",
        "title": "Classic White 90s Vintage Border",
        "product_id": "polaroid",
        "product_name": "📸 Polaroid Prints",
        "subproduct": "Classic Vintage",
        "category": "Vintage",
        "description": "Authentic nostalgic instant camera frame with writable bottom margin.",
        "image_url": "https://images.unsplash.com/photo-1552168324-d612d77725e3?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": "des_polaroid_2",
        "title": "Retro Film Grain & Date Stamp",
        "product_id": "polaroid",
        "product_name": "📸 Polaroid Prints",
        "subproduct": "Retro Film",
        "category": "Retro",
        "description": "Vintage orange date stamp in corner with subtle film emulsion texture.",
        "image_url": "https://images.unsplash.com/photo-1492691527719-9d1e07e534b4?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": "des_book_1",
        "title": "Timeless Wedding & Couple Chronicle",
        "product_id": "minibook_white",
        "product_name": "📖 Mini White Cover",
        "subproduct": "Wedding & Couple",
        "category": "Wedding & Romance",
        "description": "Pure white linen aesthetic with romantic typography, perfect for couples and anniversary gifts.",
        "image_url": "https://images.unsplash.com/photo-1519741497674-611481863552?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": "des_book_2",
        "title": "Noir Luxury Keepsake Portfolio",
        "product_id": "minibook_black",
        "product_name": "📖 Mini Black Cover",
        "subproduct": "Luxury Keepsake",
        "category": "Luxury Portfolio",
        "description": "Matte black cover finish for high-end photography, portfolio showcases, and moody aesthetics.",
        "image_url": "https://images.unsplash.com/photo-1495640388908-05fa85288e61?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": "des_mug_1",
        "title": "Addis Ababa Coffee Culture Ceramic",
        "product_id": "mug",
        "product_name": "☕ Custom Mug",
        "subproduct": "Ethiopian Heritage",
        "category": "Heritage & Culture",
        "description": "Traditional average and coffee ceremony artwork printed in rich ceramic glaze.",
        "image_url": "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=800&q=80"
    }
]

DEFAULT_PORTFOLIO = [
    {
        "id": "work_1",
        "title": "Aesthetic Laptop & Bottle Stickers",
        "category": "Stickers",
        "description": "Die-cut waterproof vinyl stickers with holographic and matte lamination. Tested on laptops, bottles, and phone cases.",
        "image_url": "https://images.unsplash.com/photo-1572375992501-4b0892d50c69?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": "work_2",
        "title": "Hardcover Keepsake Minibooks",
        "category": "Photo Books",
        "description": "Pocket minibooks featuring 24 full-color photographic pages on archival luster paper with foil-stamped covers.",
        "image_url": "https://images.unsplash.com/photo-1457369804613-52c61a468e7d?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": "work_3",
        "title": "Velvet Touch Luxury Bookmarks",
        "category": "Bookmarks",
        "description": "Double-sided 400gsm artboard bookmarks with custom typography, tassel ribbons, and soft-touch velvet finish.",
        "image_url": "https://images.unsplash.com/photo-1476275466078-4007374efbbe?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": "work_4",
        "title": "Executive Matte Business Cards",
        "category": "Business Cards",
        "description": "Premium 600gsm cotton business cards with spot UV gloss and rounded corners for creative agencies and professionals.",
        "image_url": "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": "work_5",
        "title": "Custom Ceramic Celebration Mugs",
        "category": "Mugs",
        "description": "Glossy high-definition dye sublimation mugs with custom illustrations, photos, and personalized names.",
        "image_url": "https://images.unsplash.com/photo-1517256064527-09c73fc73e38?auto=format&fit=crop&w=800&q=80"
    },
    {
        "id": "work_6",
        "title": "Personalized 120-Piece Photo Puzzle",
        "category": "Puzzles",
        "description": "Glossy cardboard photo puzzle in a custom presentation gift box for family anniversaries and birthdays.",
        "image_url": "https://images.unsplash.com/photo-1588702547919-26089e690ecc?auto=format&fit=crop&w=800&q=80"
    }
]

def get_db_url() -> Optional[str]:
    url = os.getenv("DATABASE_URL", "").strip()
    if url:
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url
    return None

def get_connection():
    """Return database connection and a boolean indicating if it's PostgreSQL."""
    url = get_db_url()
    if url and PSYCOPG2_AVAILABLE:
        conn = psycopg2.connect(url)
        return conn, True
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn, False

def q(query: str, is_pg: bool) -> str:
    """Format query placeholder for SQLite (?) vs Postgres (%s)."""
    if is_pg:
        return query.replace("?", "%s")
    return query

def fetch_all(cursor, is_pg: bool) -> List[Dict[str, Any]]:
    if is_pg:
        cols = [desc[0] for desc in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]
    return [dict(row) for row in cursor.fetchall()]

def fetch_one(cursor, is_pg: bool) -> Optional[Dict[str, Any]]:
    row = cursor.fetchone()
    if not row:
        return None
    if is_pg:
        cols = [desc[0] for desc in cursor.description]
        return dict(zip(cols, row))
    return dict(row)

def init_db():
    """Initialize database tables and run migrations if columns are missing."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    if is_pg:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id SERIAL PRIMARY KEY,
                order_code TEXT UNIQUE,
                user_id BIGINT,
                full_name TEXT,
                username TEXT,
                items TEXT,
                deadline TEXT,
                delivery_type TEXT,
                delivery_location TEXT,
                notes TEXT,
                phone TEXT,
                recipient_name TEXT,
                has_attachment INTEGER DEFAULT 0,
                payment_screenshot_file_id TEXT,
                payment_screenshot_filename TEXT,
                payment_status TEXT DEFAULT 'pending_review',
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS customers (
                user_id BIGINT PRIMARY KEY,
                full_name TEXT,
                username TEXT,
                first_seen TEXT,
                last_seen TEXT,
                total_orders INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL,
                unit TEXT DEFAULT 'per piece',
                min_order INTEGER DEFAULT 1,
                description TEXT,
                image_url TEXT,
                has_ready_designs INTEGER DEFAULT 1,
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS designs (
                id TEXT PRIMARY KEY,
                product_id TEXT,
                product_name TEXT,
                subproduct TEXT,
                category TEXT,
                title TEXT,
                description TEXT,
                image_url TEXT,
                created_at TEXT
            );
            CREATE TABLE IF NOT EXISTS portfolio (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT,
                description TEXT,
                image_url TEXT,
                created_at TEXT
            );
            ALTER TABLE orders ADD COLUMN IF NOT EXISTS phone TEXT;
            ALTER TABLE orders ADD COLUMN IF NOT EXISTS recipient_name TEXT;
            ALTER TABLE orders ADD COLUMN IF NOT EXISTS customer_files TEXT;
            ALTER TABLE orders ADD COLUMN IF NOT EXISTS rejection_reason TEXT;
            ALTER TABLE orders ADD COLUMN IF NOT EXISTS deadline_date TEXT;
            ALTER TABLE customers ADD COLUMN IF NOT EXISTS language TEXT DEFAULT 'en';
        """)
        conn.commit()
    else:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_code TEXT UNIQUE,
                user_id INTEGER,
                full_name TEXT,
                username TEXT,
                items TEXT,
                deadline TEXT,
                delivery_type TEXT,
                delivery_location TEXT,
                notes TEXT,
                has_attachment INTEGER DEFAULT 0,
                payment_screenshot_file_id TEXT,
                payment_screenshot_filename TEXT,
                payment_status TEXT DEFAULT 'pending_review',
                status TEXT DEFAULT 'pending',
                created_at TEXT,
                updated_at TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                username TEXT,
                first_seen TEXT,
                last_seen TEXT,
                total_orders INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                price REAL,
                unit TEXT DEFAULT 'per piece',
                min_order INTEGER DEFAULT 1,
                description TEXT,
                image_url TEXT,
                has_ready_designs INTEGER DEFAULT 1,
                created_at TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS designs (
                id TEXT PRIMARY KEY,
                product_id TEXT,
                product_name TEXT,
                subproduct TEXT,
                category TEXT,
                title TEXT,
                description TEXT,
                image_url TEXT,
                created_at TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT,
                description TEXT,
                image_url TEXT,
                created_at TEXT
            )
        """)
        conn.commit()

        # Migration: check if new columns exist for existing tables
        cursor.execute("PRAGMA table_info(orders)")
        columns = [row[1] for row in cursor.fetchall()]

        new_cols = {
            "payment_screenshot_file_id": "TEXT",
            "payment_screenshot_filename": "TEXT",
            "payment_status": "TEXT DEFAULT 'pending_review'",
            "updated_at": "TEXT",
            "phone": "TEXT",
            "recipient_name": "TEXT",
            "customer_files": "TEXT DEFAULT '[]'",
            "rejection_reason": "TEXT",
            "deadline_date": "TEXT"
        }

        for col, col_type in new_cols.items():
            if col not in columns:
                try:
                    cursor.execute(f"ALTER TABLE orders ADD COLUMN {col} {col_type}")
                    logger.info(f"Migrated column {col} in orders table.")
                except Exception as e:
                    logger.warning(f"Column migration notice for {col}: {e}")

        cursor.execute("PRAGMA table_info(customers)")
        cust_cols = [row[1] for row in cursor.fetchall()]
        if "language" not in cust_cols:
            try:
                cursor.execute("ALTER TABLE customers ADD COLUMN language TEXT DEFAULT 'en'")
            except Exception:
                pass

        conn.commit()

    # Sync/Upsert products with default catalog and high-res photography
    try:
        if is_pg:
            sql_prod = """
                INSERT INTO products (id, name, price, unit, min_order, description, image_url, has_ready_designs, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    name = EXCLUDED.name,
                    price = EXCLUDED.price,
                    unit = EXCLUDED.unit,
                    min_order = EXCLUDED.min_order,
                    description = EXCLUDED.description,
                    image_url = EXCLUDED.image_url,
                    has_ready_designs = EXCLUDED.has_ready_designs;
            """
        else:
            sql_prod = """
                INSERT INTO products (id, name, price, unit, min_order, description, image_url, has_ready_designs, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    price = excluded.price,
                    unit = excluded.unit,
                    min_order = excluded.min_order,
                    description = excluded.description,
                    image_url = excluded.image_url,
                    has_ready_designs = excluded.has_ready_designs;
            """
        for p in DEFAULT_PRODUCTS:
            cursor.execute(sql_prod, (
                p["id"],
                p["name"],
                p.get("price"),
                p.get("unit", "per piece"),
                p.get("min_order", 1),
                p.get("description", ""),
                p.get("image_url", ""),
                1 if p.get("has_ready_designs", True) else 0,
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
        conn.commit()
        logger.info("Synced products table in database with verified catalog.")
    except Exception as e:
        logger.error(f"Product sync notice: {e}")
        if is_pg:
            conn.rollback()

    # Sync/Upsert designs with curated styles
    try:
        if is_pg:
            sql_des = """
                INSERT INTO designs (id, product_id, product_name, subproduct, category, title, description, image_url, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    product_id = EXCLUDED.product_id,
                    product_name = EXCLUDED.product_name,
                    subproduct = EXCLUDED.subproduct,
                    category = EXCLUDED.category,
                    title = EXCLUDED.title,
                    description = EXCLUDED.description,
                    image_url = EXCLUDED.image_url;
            """
        else:
            sql_des = """
                INSERT INTO designs (id, product_id, product_name, subproduct, category, title, description, image_url, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    product_id = excluded.product_id,
                    product_name = excluded.product_name,
                    subproduct = excluded.subproduct,
                    category = excluded.category,
                    title = excluded.title,
                    description = excluded.description,
                    image_url = excluded.image_url;
            """
        for d in DEFAULT_DESIGNS:
            cursor.execute(sql_des, (
                d["id"],
                d.get("product_id", ""),
                d.get("product_name", ""),
                d.get("subproduct", ""),
                d.get("category", ""),
                d.get("title", ""),
                d.get("description", ""),
                d.get("image_url", ""),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
        conn.commit()
        logger.info("Synced designs table in database with default styles.")
    except Exception as e:
        logger.error(f"Design sync notice: {e}")
        if is_pg:
            conn.rollback()

    # Sync/Upsert portfolio showcase works
    try:
        if is_pg:
            sql_port = """
                INSERT INTO portfolio (id, title, category, description, image_url, created_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    title = EXCLUDED.title,
                    category = EXCLUDED.category,
                    description = EXCLUDED.description,
                    image_url = EXCLUDED.image_url;
            """
        else:
            sql_port = """
                INSERT INTO portfolio (id, title, category, description, image_url, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    title = excluded.title,
                    category = excluded.category,
                    description = excluded.description,
                    image_url = excluded.image_url;
            """
        for item in DEFAULT_PORTFOLIO:
            cursor.execute(sql_port, (
                item["id"],
                item.get("title", ""),
                item.get("category", ""),
                item.get("description", ""),
                item.get("image_url", ""),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
        conn.commit()
        logger.info("Synced portfolio table in database with showcase items.")
    except Exception as e:
        logger.error(f"Portfolio sync notice: {e}")
        if is_pg:
            conn.rollback()

    # Sanitize existing orders if notes had REJECTED REASON appended historically
    try:
        cursor.execute(q("SELECT order_code, notes, rejection_reason FROM orders WHERE notes LIKE '%REJECTED REASON:%'", is_pg))
        polluted_rows = cursor.fetchall()
        for prow in polluted_rows:
            ocode = prow[0] if not is_pg else prow["order_code"]
            onotes = prow[1] if not is_pg else prow["notes"]
            oreason = prow[2] if not is_pg else prow["rejection_reason"]
            import re
            m = re.search(r"REJECTED\s*REASON:\s*(.+)$", onotes or "", re.IGNORECASE)
            ext_reason = m.group(1).strip() if m else ""
            cleaned = re.sub(r"(?:\s*\|\s*)?REJECTED\s*REASON:.*$", "", onotes or "", flags=re.IGNORECASE).strip()
            final_reason = oreason or ext_reason
            cursor.execute(q("UPDATE orders SET notes = ?, rejection_reason = ? WHERE order_code = ?", is_pg), (cleaned, final_reason, ocode))
        conn.commit()
    except Exception as e:
        logger.warning(f"Notice during notes sanitization: {e}")

    conn.close()

def get_setting(key: str, default: str = "") -> str:
    """Retrieve a persistent setting from the database."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    cursor.execute(q("SELECT value FROM settings WHERE key = ?", is_pg), (key,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return default

def set_setting(key: str, value: str):
    """Save or update a persistent setting in the database."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    if is_pg:
        cursor.execute("""
            INSERT INTO settings (key, value) VALUES (%s, %s)
            ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
        """, (key, value))
    else:
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()

def get_admin_credentials() -> tuple[str, str]:
    """Return the active dashboard admin username and password."""
    import config
    username = get_setting("admin_username", "") or config.DASHBOARD_USERNAME
    password = get_setting("admin_password", "") or config.DASHBOARD_PASSWORD
    return username, password

def update_admin_credentials(new_username: str, new_password: str):
    """Update admin username and password persistently in DB and sync to .env if present."""
    set_setting("admin_username", new_username)
    set_setting("admin_password", new_password)

    # Sync to local .env file if it exists
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if env_file.exists():
        try:
            import re
            content = env_file.read_text(encoding="utf-8")
            if "DASHBOARD_USERNAME=" in content:
                content = re.sub(r"^DASHBOARD_USERNAME=.*$", f"DASHBOARD_USERNAME={new_username}", content, flags=re.MULTILINE)
            else:
                content += f"\nDASHBOARD_USERNAME={new_username}"
            if "DASHBOARD_PASSWORD=" in content:
                content = re.sub(r"^DASHBOARD_PASSWORD=.*$", f"DASHBOARD_PASSWORD={new_password}", content, flags=re.MULTILINE)
            else:
                content += f"\nDASHBOARD_PASSWORD={new_password}"
            env_file.write_text(content, encoding="utf-8")
            logger.info("Updated DASHBOARD credentials in .env file.")
        except Exception as e:
            logger.warning(f"Could not update .env file: {e}")

def normalize_deadline_to_iso(val: str) -> str:
    """Normalize arbitrary deadline strings to ISO YYYY-MM-DD."""
    if not val:
        return ""
    val = val.strip()
    m = re.search(r"(\d{4}-\d{2}-\d{2})", val)
    if m:
        return m.group(1)

    clean_val = val.split("(")[0].strip()
    now = datetime.now()
    cur_year = now.year

    for fmt in ["%b %d, %Y", "%Y-%m-%d", "%Y/%m/%d", "%a, %d %b %Y"]:
        try:
            return datetime.strptime(clean_val, fmt).strftime("%Y-%m-%d")
        except ValueError:
            pass

    for fmt in ["%a, %b %d", "%b %d"]:
        try:
            dt = datetime.strptime(f"{cur_year} {clean_val}", f"%Y {fmt}")
            if dt.date() < now.date() - timedelta(days=30):
                dt = dt.replace(year=cur_year + 1)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            pass

    return ""

def get_daily_booked_capacities() -> Dict[str, Dict[str, int]]:
    """Return dictionary of ISO date (YYYY-MM-DD) -> {'total': int, 'rush': int} for all active orders."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT deadline, deadline_date, notes, status, payment_status
            FROM orders
            WHERE status NOT IN ('completed', 'cancelled')
        """)
        rows = cursor.fetchall()
        capacities: Dict[str, Dict[str, int]] = {}
        for row in rows:
            r = dict(row) if hasattr(row, "keys") else (row if isinstance(row, dict) else {})
            dl = r.get("deadline") if r else (row[0] if len(row) > 0 else "")
            dl_date = (r.get("deadline_date") if r else (row[1] if len(row) > 1 else "")) or ""
            notes = ((r.get("notes") if r else (row[2] if len(row) > 2 else "")) or "").lower()

            iso_date = dl_date or normalize_deadline_to_iso(dl)
            if not iso_date:
                continue

            if iso_date not in capacities:
                capacities[iso_date] = {"total": 0, "rush": 0}

            capacities[iso_date]["total"] += 1
            if "rush" in notes or "urgent" in notes or "200 etb" in notes or "2-day" in notes:
                capacities[iso_date]["rush"] += 1

        return capacities
    except Exception as e:
        logger.error(f"Error fetching daily booked capacities: {e}")
        return {}
    finally:
        conn.close()

def check_date_capacity(target_date_iso: str, is_rush: bool = False, max_daily: int = 100, max_rush: int = 50) -> tuple[bool, str]:
    """Validate whether a target date is available, not Sunday, and within capacity limits."""
    try:
        target_d = datetime.strptime(target_date_iso, "%Y-%m-%d").date()
    except Exception:
        return False, "Invalid date format."

    # Sunday is studio rest day (no production or completion scheduled)
    if target_d.weekday() == 6:
        return False, "Sunday is our studio rest day. We do not schedule production or completion on Sundays."

    today = date.today()
    if target_d <= today:
        return False, "Past and same-day deadlines are not allowed. Please select an upcoming working day."

    capacities = get_daily_booked_capacities()
    day_stats = capacities.get(target_date_iso, {"total": 0, "rush": 0})

    if day_stats["total"] >= max_daily:
        return False, f"This date is fully booked ({day_stats['total']}/{max_daily} orders reached). Please choose the next open day."

    if is_rush and day_stats["rush"] >= max_rush:
        return False, f"Urgent rush capacity for this date is full ({day_stats['rush']}/{max_rush} rush orders). Please select standard turnaround or the next available rush slot."

    return True, "Available"

def get_earliest_available_date(is_rush: bool = False, max_daily: int = 100, max_rush: int = 50) -> date:
    """Find the earliest available production completion date skipping Sundays and full days."""
    today = date.today()
    capacities = get_daily_booked_capacities()

    working_days = []
    curr = today
    # Buffer: tomorrow (working day +1) is file prep/drying buffer
    while len(working_days) < 35:
        curr += timedelta(days=1)
        if curr.weekday() != 6: # Skip Sunday
            working_days.append(curr)

    # For Urgent Rush: starts from 2nd working day (index 1)
    # For Standard: starts from 3rd working day (index 2)
    start_idx = 1 if is_rush else 2

    for d in working_days[start_idx:]:
        iso = d.isoformat()
        stats = capacities.get(iso, {"total": 0, "rush": 0})
        if stats["total"] >= max_daily:
            continue
        if is_rush and stats["rush"] >= max_rush:
            continue
        return d

    return working_days[start_idx]

def save_order(
    user_id: int,
    full_name: str,
    username: Optional[str],
    items: str,
    deadline: str,
    delivery_type: str,
    delivery_location: str,
    notes: str,
    has_attachment: bool = False,
    payment_screenshot_file_id: Optional[str] = None,
    payment_screenshot_filename: Optional[str] = None,
    payment_status: str = "pending_review",
    status: str = "pending",
    phone: Optional[str] = None,
    recipient_name: Optional[str] = None,
    customer_files: Optional[str] = "[]"
) -> str:
    """Save order to database and return generated order code (e.g. SP-1001)."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    deadline_iso = normalize_deadline_to_iso(deadline)

    insert_sql = """
        INSERT INTO orders (
            user_id, full_name, username, items, deadline, deadline_date,
            delivery_type, delivery_location, notes, has_attachment,
            payment_screenshot_file_id, payment_screenshot_filename,
            payment_status, status, created_at, updated_at,
            phone, recipient_name, customer_files
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        user_id, full_name, username or "", items, deadline, deadline_iso,
        delivery_type, delivery_location, notes, 1 if has_attachment else 0,
        payment_screenshot_file_id, payment_screenshot_filename,
        payment_status, status, created_at, created_at,
        phone or "", recipient_name or full_name, customer_files or "[]"
    )

    if is_pg:
        cursor.execute(q(insert_sql, True) + " RETURNING id", params)
        order_id = cursor.fetchone()[0]
    else:
        cursor.execute(insert_sql, params)
        order_id = cursor.lastrowid

    order_code = f"SP-{1000 + order_id}"

    cursor.execute(q("UPDATE orders SET order_code = ? WHERE id = ?", is_pg), (order_code, order_id))

    cust_sql = """
        INSERT INTO customers (user_id, full_name, username, first_seen, last_seen, total_orders)
        VALUES (?, ?, ?, ?, ?, 1)
        ON CONFLICT (user_id) DO UPDATE SET
            full_name = EXCLUDED.full_name,
            username = EXCLUDED.username,
            last_seen = EXCLUDED.last_seen,
            total_orders = customers.total_orders + 1
    """
    cursor.execute(q(cust_sql, is_pg), (user_id, full_name, username or "", created_at, created_at))

    conn.commit()
    conn.close()
    return order_code

def update_order_payment(order_code: str, payment_status: str, order_status: Optional[str] = None) -> bool:
    """Update payment status and optionally order status."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if order_status:
        if payment_status == "approved":
            cursor.execute(q("""
                UPDATE orders
                SET payment_status = ?, status = ?, rejection_reason = NULL, updated_at = ?
                WHERE order_code = ?
            """, is_pg), (payment_status, order_status, updated_at, order_code))
        else:
            cursor.execute(q("""
                UPDATE orders
                SET payment_status = ?, status = ?, updated_at = ?
                WHERE order_code = ?
            """, is_pg), (payment_status, order_status, updated_at, order_code))
    else:
        if payment_status == "approved":
            cursor.execute(q("""
                UPDATE orders
                SET payment_status = ?, rejection_reason = NULL, updated_at = ?
                WHERE order_code = ?
            """, is_pg), (payment_status, updated_at, order_code))
        else:
            cursor.execute(q("""
                UPDATE orders
                SET payment_status = ?, updated_at = ?
                WHERE order_code = ?
            """, is_pg), (payment_status, updated_at, order_code))

    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def update_order_status(order_code: str, status: str) -> bool:
    """Update overall order status (e.g. pending, approved, in_production, ready_for_delivery, completed, cancelled)."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(q("""
        UPDATE orders
        SET status = ?, updated_at = ?
        WHERE order_code = ?
    """, is_pg), (status, updated_at, order_code))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def update_order_delivery(order_code: str, delivery_type: str, delivery_location: str) -> bool:
    """Update delivery method and location for an order."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(q("""
        UPDATE orders
        SET delivery_type = ?, delivery_location = ?, updated_at = ?
        WHERE order_code = ?
    """, is_pg), (delivery_type, delivery_location, updated_at, order_code))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def get_order_by_code(order_code: str) -> Optional[Dict[str, Any]]:
    """Retrieve full details of an order by code."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    cursor.execute(q("SELECT * FROM orders WHERE order_code = ?", is_pg), (order_code,))
    result = fetch_one(cursor, is_pg)
    conn.close()
    return result

def get_order_by_receipt_filename(filename: str) -> Optional[Dict[str, Any]]:
    """Retrieve order matching a payment screenshot filename."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    cursor.execute(q("SELECT * FROM orders WHERE payment_screenshot_filename = ?", is_pg), (filename,))
    result = fetch_one(cursor, is_pg)
    conn.close()
    return result

def get_order_by_customer_file(filename: str) -> Optional[Dict[str, Any]]:
    """Retrieve order containing a specific customer uploaded file."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    cursor.execute(q("SELECT * FROM orders WHERE customer_files LIKE ?", is_pg), (f"%{filename}%",))
    result = fetch_one(cursor, is_pg)
    conn.close()
    return result

def get_recent_orders(limit: int = 15) -> List[Dict[str, Any]]:
    """Fetch the most recent orders."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    cursor.execute(q("SELECT * FROM orders ORDER BY id DESC LIMIT ?", is_pg), (limit,))
    results = fetch_all(cursor, is_pg)
    conn.close()
    return results

def get_all_orders(status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch all orders, optionally filtered by status."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    if status_filter == "in_production":
        cursor.execute(q("""
            SELECT * FROM orders 
            WHERE (status = 'in_production' OR payment_status = 'approved')
              AND status NOT IN ('rejected', 'reuploaded', 'completed', 'cancelled')
              AND payment_status NOT IN ('rejected', 'reuploaded')
            ORDER BY id DESC
        """, is_pg))
    elif status_filter == "reuploaded":
        cursor.execute(q("""
            SELECT * FROM orders 
            WHERE status = 'reuploaded' OR payment_status = 'reuploaded'
            ORDER BY id DESC
        """, is_pg))
    elif status_filter == "rejected":
        cursor.execute(q("""
            SELECT * FROM orders 
            WHERE status = 'rejected' OR payment_status = 'rejected'
            ORDER BY id DESC
        """, is_pg))
    elif status_filter and status_filter != "all":
        cursor.execute(q("SELECT * FROM orders WHERE status = ? OR payment_status = ? ORDER BY id DESC", is_pg), (status_filter, status_filter))
    else:
        cursor.execute("SELECT * FROM orders ORDER BY id DESC")
    results = fetch_all(cursor, is_pg)
    conn.close()
    return results

def get_stats() -> Dict[str, Any]:
    """Get overall business statistics."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM orders")
    total_orders = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders WHERE payment_status = 'pending_review' AND status NOT IN ('rejected', 'reuploaded')")
    pending_approvals = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders WHERE (status = 'approved' OR status = 'in_production') AND status NOT IN ('rejected', 'reuploaded', 'completed', 'cancelled')")
    approved_orders = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'completed'")
    completed_orders = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM customers")
    total_customers = cursor.fetchone()[0]

    conn.close()
    return {
        "total_orders": total_orders,
        "pending_approvals": pending_approvals,
        "approved_orders": approved_orders,
        "completed_orders": completed_orders,
        "total_customers": total_customers
    }

def export_orders_to_csv(filepath: Path) -> Path:
    """Export all orders to a CSV file."""
    import csv
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT order_code, created_at, full_name, username, items, deadline,
               delivery_type, delivery_location, notes, payment_status, status
        FROM orders ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    headers = [
        "Order Code", "Date & Time", "Customer Name", "Username",
        "Items Ordered", "Deadline", "Delivery Method", "Location/Contact",
        "Notes", "Payment Status", "Order Status"
    ]

    with open(filepath, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        writer.writerows(rows)

    return filepath

def get_sales_analytics() -> Dict[str, Any]:
    """Compute comprehensive sales analytics from orders and product catalog."""
    import re
    conn, is_pg = get_connection()
    cursor = conn.cursor()

    # Fetch all non-cancelled, non-rejected orders
    cursor.execute("""
        SELECT order_code, items, notes, status, payment_status, created_at
        FROM orders
        WHERE status NOT IN ('cancelled', 'rejected')
          AND payment_status NOT IN ('rejected')
        ORDER BY created_at ASC
    """)
    rows = fetch_all(cursor, is_pg)
    conn.close()

    # Load product prices for fallback calculation
    products_data = get_products_data()
    price_map = {}
    for p in products_data.get("products", []):
        pid = p.get("id", "")
        pname = p.get("name", "").lower().replace("🏷 ", "").replace("🔖 ", "").replace("💼 ", "").replace("📸 ", "").replace("📓 ", "").replace("📔 ", "").replace("📖 ", "").replace("☕ ", "").replace("🧩 ", "").replace("🟢 ", "").strip()
        price_val = p.get("price")
        if price_val is not None:
            price_map[pid] = float(price_val)
            price_map[pname] = float(price_val)

    total_revenue = 0.0
    total_deposits_collected = 0.0
    completed_revenue = 0.0
    order_count = 0
    product_sales = {}      # product_name -> {"qty": int, "revenue": float}
    daily_revenue = {}       # "YYYY-MM-DD" -> float
    status_counts = {"pending_review": 0, "in_production": 0, "ready_for_delivery": 0, "completed": 0, "reuploaded": 0}

    for row in rows:
        notes = row.get("notes", "") or ""
        items_str = row.get("items", "") or ""
        status = row.get("status", "")
        pay_status = row.get("payment_status", "")
        created = row.get("created_at", "")

        # Parse total and deposit from notes: "Deposit: 150 ETB (Total: 300 ETB)"
        order_total = 0.0
        order_deposit = 0.0

        total_match = re.search(r"Total:\s*([\d,]+(?:\.\d+)?)\s*ETB", notes, re.IGNORECASE)
        deposit_match = re.search(r"Deposit:\s*([\d,]+(?:\.\d+)?)\s*ETB", notes, re.IGNORECASE)

        if total_match:
            order_total = float(total_match.group(1).replace(",", ""))
        if deposit_match:
            order_deposit = float(deposit_match.group(1).replace(",", ""))

        # Fallback: parse items like "15x Stickers" and compute from price_map
        if order_total == 0 and items_str:
            qty_match = re.match(r"(\d+)\s*x\s*(.+)", items_str, re.IGNORECASE)
            if qty_match:
                qty = int(qty_match.group(1))
                product_name = qty_match.group(2).strip().lower()
                for key, price in price_map.items():
                    if key in product_name or product_name in key:
                        order_total = qty * price
                        order_deposit = order_total * 0.5
                        break

        total_revenue += order_total
        order_count += 1

        # Only count deposit as collected if payment approved or further
        if pay_status == "approved" or status in ("in_production", "ready_for_delivery", "completed"):
            total_deposits_collected += order_deposit

        if status == "completed":
            completed_revenue += order_total

        # Product breakdown
        prod_display = items_str.strip() or "Unknown"
        if prod_display not in product_sales:
            product_sales[prod_display] = {"qty": 0, "revenue": 0.0}
        # Parse quantity
        qty_m = re.match(r"(\d+)\s*x", items_str, re.IGNORECASE)
        product_sales[prod_display]["qty"] += int(qty_m.group(1)) if qty_m else 1
        product_sales[prod_display]["revenue"] += order_total

        # Daily revenue
        if created:
            day = created[:10]  # "YYYY-MM-DD"
            daily_revenue[day] = daily_revenue.get(day, 0.0) + order_total

        # Status counts
        effective_status = status
        if pay_status == "pending_review" and status not in ("reuploaded",):
            effective_status = "pending_review"
        elif pay_status == "approved" and status == "in_production":
            effective_status = "in_production"

        if effective_status in status_counts:
            status_counts[effective_status] += 1

    pending_balance = total_revenue - total_deposits_collected
    aov = (total_revenue / order_count) if order_count > 0 else 0.0

    # Sort daily revenue by date
    sorted_days = sorted(daily_revenue.keys())
    daily_labels = sorted_days
    daily_values = [daily_revenue[d] for d in sorted_days]

    # Top products by revenue
    sorted_products = sorted(product_sales.items(), key=lambda x: x[1]["revenue"], reverse=True)
    product_labels = [p[0] for p in sorted_products[:10]]
    product_revenues = [p[1]["revenue"] for p in sorted_products[:10]]
    product_quantities = [p[1]["qty"] for p in sorted_products[:10]]

    return {
        "total_revenue": round(total_revenue, 2),
        "total_deposits_collected": round(total_deposits_collected, 2),
        "pending_balance": round(pending_balance, 2),
        "completed_revenue": round(completed_revenue, 2),
        "order_count": order_count,
        "aov": round(aov, 2),
        "daily_labels": daily_labels,
        "daily_values": daily_values,
        "product_labels": product_labels,
        "product_revenues": product_revenues,
        "product_quantities": product_quantities,
        "status_counts": status_counts,
    }

# Product catalog management (Stored directly in SQL Database)
def get_products_data() -> Dict[str, Any]:
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(q("SELECT id, name, price, unit, min_order, description, image_url, has_ready_designs FROM products ORDER BY id", is_pg))
        rows = fetch_all(cursor, is_pg)
        products = []
        for r in rows:
            products.append({
                "id": r["id"],
                "name": r["name"],
                "price": float(r["price"]) if r["price"] is not None else None,
                "unit": r["unit"],
                "min_order": int(r["min_order"]) if r["min_order"] is not None else 1,
                "description": r["description"] or "",
                "image_url": r["image_url"] or f"/product-images/{r['id']}.png",
                "has_ready_designs": bool(r["has_ready_designs"])
            })
        if not products:
            return {"products": DEFAULT_PRODUCTS}
        return {"products": products}
    except Exception as e:
        logger.error(f"Error reading products from DB: {e}")
        return {"products": DEFAULT_PRODUCTS}
    finally:
        conn.close()

def update_product_price(product_id: str, new_price: float) -> bool:
    """Update a product's price dynamically in the database."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(q("UPDATE products SET price = ? WHERE id = ?", is_pg), (new_price, product_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Failed to update product price in DB: {e}")
        return False
    finally:
        conn.close()

def update_product_image(product_id: str, image_url: str) -> bool:
    """Update a product's image URL dynamically in the database."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(q("UPDATE products SET image_url = ? WHERE id = ?", is_pg), (image_url, product_id))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Failed to update product image in DB: {e}")
        return False
    finally:
        conn.close()

def add_product(
    name: str,
    price: float,
    unit: str = "per piece",
    description: str = "",
    min_order: Optional[int] = None,
    image_url: Optional[str] = None,
    product_id: Optional[str] = None,
    has_ready_designs: bool = True
) -> Dict[str, Any]:
    """Add a new product to the database."""
    import re
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    try:
        if not product_id:
            clean = re.sub(r"[^\w\s-]", "", name.lower()).strip()
            base_id = re.sub(r"[-\s]+", "_", clean) or "item"
            product_id = base_id
            counter = 1
            cursor.execute(q("SELECT id FROM products WHERE id = ?", is_pg), (product_id,))
            while cursor.fetchone():
                product_id = f"{base_id}_{counter}"
                counter += 1
                cursor.execute(q("SELECT id FROM products WHERE id = ?", is_pg), (product_id,))

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        min_ord = int(min_order) if min_order and int(min_order) > 1 else 1
        img = image_url or f"/product-images/{product_id}.png"
        has_ready_int = 1 if has_ready_designs else 0

        cursor.execute(
            q("INSERT INTO products (id, name, price, unit, min_order, description, image_url, has_ready_designs, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", is_pg),
            (product_id, name.strip(), float(price) if price is not None else 0.0, unit.strip() or "each", min_ord, description.strip(), img, has_ready_int, created_at)
        )
        conn.commit()

        new_item = {
            "id": product_id,
            "name": name.strip(),
            "price": float(price) if price is not None else 0.0,
            "unit": unit.strip() or "each",
            "min_order": min_ord,
            "description": description.strip() or f"High quality custom printed {name.strip()} from Selora Prints.",
            "image_url": img,
            "has_ready_designs": bool(has_ready_designs)
        }

        logger.info(f"Successfully added new product to DB: {product_id} ({name})")
        return new_item
    except Exception as e:
        logger.error(f"Failed to add product to DB: {e}")
        raise e
    finally:
        conn.close()

def delete_product(product_id: str) -> bool:
    """Remove a product from database by ID."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(q("DELETE FROM products WHERE id = ?", is_pg), (product_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Failed to delete product from DB: {e}")
        return False
    finally:
        conn.close()

def get_orders_by_user(user_id: int) -> List[Dict[str, Any]]:
    """Retrieve all orders placed by a specific customer."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    cursor.execute(q("SELECT * FROM orders WHERE user_id = ? ORDER BY id DESC", is_pg), (user_id,))
    results = fetch_all(cursor, is_pg)
    conn.close()
    return results

def get_all_customers_user_ids() -> List[int]:
    """Retrieve all distinct customer user IDs for announcements."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT user_id FROM customers WHERE user_id IS NOT NULL")
    rows = cursor.fetchall()
    conn.close()
    return [r[0] for r in rows if r[0]]

# -------------------------------------------------------------
# DYNAMIC DESIGNS & SUBPRODUCTS MANAGEMENT (Stored in SQL DB)
# -------------------------------------------------------------

def get_designs_data() -> Dict[str, Any]:
    """Fetch all designs from designs table in DB."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(q("SELECT id, product_id, product_name, subproduct, category, title, description, image_url FROM designs ORDER BY id", is_pg))
        rows = fetch_all(cursor, is_pg)
        designs = []
        for r in rows:
            designs.append({
                "id": r["id"],
                "product_id": r.get("product_id") or "",
                "product_name": r.get("product_name") or "",
                "subproduct": r.get("subproduct") or "",
                "category": r.get("category") or r.get("subproduct") or "Curated",
                "title": r.get("title") or "",
                "description": r.get("description") or "",
                "image_url": r.get("image_url") or f"/designs-images/{r['id']}.png"
            })
        if not designs:
            return {"designs": DEFAULT_DESIGNS}
        return {"designs": designs}
    except Exception as e:
        logger.error(f"Error reading designs from DB: {e}")
        return {"designs": DEFAULT_DESIGNS}
    finally:
        conn.close()

def get_designs(product_id: Optional[str] = None, subproduct: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch designs filtered optionally by product_id and/or subproduct from DB."""
    data = get_designs_data()
    designs = data.get("designs", [])
    if product_id and product_id != "all":
        designs = [d for d in designs if d.get("product_id") == product_id]
    if subproduct and subproduct != "all":
        designs = [d for d in designs if d.get("subproduct", "").lower() == subproduct.lower()]
    return designs

def get_design_by_id(design_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single design by its ID from DB."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(q("SELECT id, product_id, product_name, subproduct, category, title, description, image_url FROM designs WHERE id = ?", is_pg), (design_id,))
        r = fetch_one(cursor, is_pg)
        if not r:
            return None
        return {
            "id": r["id"],
            "product_id": r.get("product_id") or "",
            "product_name": r.get("product_name") or "",
            "subproduct": r.get("subproduct") or "",
            "category": r.get("category") or r.get("subproduct") or "Curated",
            "title": r.get("title") or "",
            "description": r.get("description") or "",
            "image_url": r.get("image_url") or f"/designs-images/{r['id']}.png"
        }
    except Exception as e:
        logger.error(f"Error fetching design {design_id}: {e}")
        return None
    finally:
        conn.close()

def add_design(
    title: str,
    product_id: str,
    subproduct: str,
    description: str = "",
    image_url: str = "",
    product_name: Optional[str] = None,
    design_id: Optional[str] = None
) -> Dict[str, Any]:
    """Add a new design to designs table in DB."""
    import re
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    try:
        if not design_id:
            clean = re.sub(r"[^\w\s-]", "", title.lower()).strip()
            clean_slug = re.sub(r'[-\s]+', '_', clean)
            base_id = f"des_{product_id}_{clean_slug}" if clean_slug else f"des_{int(datetime.now().timestamp())}"
            design_id = base_id
            counter = 1
            cursor.execute(q("SELECT id FROM designs WHERE id = ?", is_pg), (design_id,))
            while cursor.fetchone():
                design_id = f"{base_id}_{counter}"
                counter += 1
                cursor.execute(q("SELECT id FROM designs WHERE id = ?", is_pg), (design_id,))

        if not product_name:
            cursor.execute(q("SELECT name FROM products WHERE id = ?", is_pg), (product_id,))
            p_row = cursor.fetchone()
            if p_row:
                product_name = p_row[0] if not is_pg else p_row["name"]
            else:
                product_name = product_id.replace("_", " ").title()

        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        img = image_url or f"/designs-images/{design_id}.png"
        cat = subproduct.strip() or "Curated"

        cursor.execute(
            q("INSERT INTO designs (id, product_id, product_name, subproduct, category, title, description, image_url, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", is_pg),
            (design_id, product_id.strip(), product_name.strip(), subproduct.strip(), cat, title.strip(), description.strip(), img, created_at)
        )
        conn.commit()

        new_design = {
            "id": design_id,
            "title": title.strip(),
            "product_id": product_id.strip(),
            "product_name": product_name.strip(),
            "subproduct": subproduct.strip(),
            "category": cat,
            "description": description.strip(),
            "image_url": img,
            "created_at": created_at
        }

        return new_design
    except Exception as e:
        logger.error(f"Failed to add design to DB: {e}")
        raise e
    finally:
        conn.close()

def delete_design(design_id: str) -> bool:
    """Delete a design by ID from DB."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(q("DELETE FROM designs WHERE id = ?", is_pg), (design_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Failed to delete design from DB: {e}")
        return False
    finally:
        conn.close()

def get_design_categories() -> Dict[str, List[str]]:
    """Return dictionary mapping product_ids to unique subproduct names."""
    data = get_designs_data()
    mapping: Dict[str, set] = {}
    for d in data.get("designs", []):
        pid = d.get("product_id")
        sub = d.get("subproduct")
        if pid and sub:
            mapping.setdefault(pid, set()).add(sub)
    return {k: sorted(list(v)) for k, v in mapping.items()}

# ─── USER LANGUAGE PREFERENCE ─────────────────────────────────

def get_user_language(user_id: int) -> Optional[str]:
    """Retrieve saved language preference ('en' or 'am')."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    cursor.execute(q("SELECT language FROM customers WHERE user_id = ?", is_pg), (user_id,))
    row = fetch_one(cursor, is_pg)
    conn.close()
    if row and row.get("language"):
        return row["language"]
    return None

def set_user_language(user_id: int, lang: str, full_name: str = "", username: str = ""):
    """Save or update customer's preferred language."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if is_pg:
        cursor.execute("""
            INSERT INTO customers (user_id, full_name, username, first_seen, last_seen, language)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET language = EXCLUDED.language, last_seen = EXCLUDED.last_seen;
        """, (user_id, full_name, username or "", now, now, lang))
    else:
        cursor.execute("""
            INSERT INTO customers (user_id, full_name, username, first_seen, last_seen, language)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET language = excluded.language, last_seen = excluded.last_seen;
        """, (user_id, full_name, username or "", now, now, lang))
    conn.commit()
    conn.close()

# ─── PORTFOLIO / OUR WORKS (Stored in SQL DB) ─────────────────

def get_portfolio_items() -> List[Dict[str, Any]]:
    """Get list of showcased past works from database."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(q("SELECT id, title, category, description, image_url, created_at FROM portfolio ORDER BY id DESC", is_pg))
        rows = fetch_all(cursor, is_pg)
        items = []
        for r in rows:
            items.append({
                "id": r["id"],
                "title": r.get("title") or "",
                "category": r.get("category") or "Merch",
                "description": r.get("description") or "",
                "image_url": r.get("image_url") or "",
                "created_at": r.get("created_at") or ""
            })
        if not items:
            return DEFAULT_PORTFOLIO
        return items
    except Exception as e:
        logger.error(f"Error fetching portfolio from DB: {e}")
        return DEFAULT_PORTFOLIO
    finally:
        conn.close()

def save_portfolio_items(items: List[Dict[str, Any]]):
    pass

def add_portfolio_item(title: str, category: str, description: str, image_url: str) -> Dict[str, Any]:
    """Add a new past work item to portfolio table in DB."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    new_id = f"work_{int(datetime.now().timestamp())}"
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        cursor.execute(
            q("INSERT INTO portfolio (id, title, category, description, image_url, created_at) VALUES (?, ?, ?, ?, ?, ?)", is_pg),
            (new_id, title.strip(), category.strip(), description.strip(), image_url.strip(), created_at)
        )
        conn.commit()

        return {
            "id": new_id,
            "title": title.strip(),
            "category": category.strip(),
            "description": description.strip(),
            "image_url": image_url.strip(),
            "created_at": created_at
        }
    except Exception as e:
        logger.error(f"Failed to add portfolio item to DB: {e}")
        raise e
    finally:
        conn.close()

def delete_portfolio_item(item_id: str) -> bool:
    """Delete a past work from portfolio table in DB."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(q("DELETE FROM portfolio WHERE id = ?", is_pg), (item_id,))
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Failed to delete portfolio item from DB: {e}")
        return False
    finally:
        conn.close()

def update_order_artwork(order_code: str, customer_files: str) -> bool:
    """Update customer artwork files after re-upload and mark status as reuploaded."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(q("""
        UPDATE orders
        SET customer_files = ?, status = 'reuploaded', updated_at = ?
        WHERE order_code = ?
    """, is_pg), (customer_files, updated_at, order_code))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

def update_order_receipt(order_code: str, file_id: str, filename: str) -> bool:
    """Update customer deposit receipt after re-upload and mark payment_status as reuploaded."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(q("""
        UPDATE orders
        SET payment_screenshot_file_id = ?, payment_screenshot_filename = ?,
            payment_status = 'reuploaded', updated_at = ?
        WHERE order_code = ?
    """, is_pg), (file_id, filename, updated_at, order_code))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

# ─── TELEGRAM BUSINESS CONNECTION STORAGE ─────────────────────

BUSINESS_CONN_FILE = DATA_DIR / "business_connection.json"

def save_business_connection(conn_id: str, user_id: int, is_enabled: bool = True):
    try:
        with open(BUSINESS_CONN_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "connection_id": conn_id,
                "user_id": user_id,
                "is_enabled": is_enabled,
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save business connection: {e}")

def get_business_connection() -> Optional[Dict[str, Any]]:
    if not BUSINESS_CONN_FILE.exists():
        return None
    try:
        with open(BUSINESS_CONN_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if data.get("is_enabled") and data.get("connection_id"):
                return data
            return None
    except Exception:
        return None

# ─── ORDER REJECTION WITH REASON ──────────────────────────────

def update_order_rejection(order_code: str, reason: str) -> bool:
    """Mark order rejected and record reason in rejection_reason column without corrupting customer notes."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(q("""
        UPDATE orders
        SET status = 'rejected', payment_status = 'rejected',
            rejection_reason = ?,
            updated_at = ?
        WHERE order_code = ?
    """, is_pg), (reason, updated_at, order_code))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

# Initialize DB on import
init_db()
