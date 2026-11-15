import os
import json
import sqlite3
import logging
from pathlib import Path
from datetime import datetime
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
PRODUCTS_FILE = DATA_DIR / "products.json"

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
            ALTER TABLE orders ADD COLUMN IF NOT EXISTS phone TEXT;
            ALTER TABLE orders ADD COLUMN IF NOT EXISTS recipient_name TEXT;
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
            "recipient_name": "TEXT"
        }

        for col, col_type in new_cols.items():
            if col not in columns:
                try:
                    cursor.execute(f"ALTER TABLE orders ADD COLUMN {col} {col_type}")
                    logger.info(f"Migrated column {col} in orders table.")
                except Exception as e:
                    logger.warning(f"Column migration notice for {col}: {e}")

        conn.commit()
    conn.close()

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
    recipient_name: Optional[str] = None
) -> str:
    """Save order to database and return generated order code (e.g. SP-1001)."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    insert_sql = """
        INSERT INTO orders (
            user_id, full_name, username, items, deadline,
            delivery_type, delivery_location, notes, has_attachment,
            payment_screenshot_file_id, payment_screenshot_filename,
            payment_status, status, created_at, updated_at,
            phone, recipient_name
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        user_id, full_name, username or "", items, deadline,
        delivery_type, delivery_location, notes, 1 if has_attachment else 0,
        payment_screenshot_file_id, payment_screenshot_filename,
        payment_status, status, created_at, created_at,
        phone or "", recipient_name or full_name
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
        cursor.execute(q("""
            UPDATE orders
            SET payment_status = ?, status = ?, updated_at = ?
            WHERE order_code = ?
        """, is_pg), (payment_status, order_status, updated_at, order_code))
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
    """Update overall order status (e.g. pending, approved, in_production, completed, cancelled)."""
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

def get_order_by_code(order_code: str) -> Optional[Dict[str, Any]]:
    """Retrieve full details of an order by code."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    cursor.execute(q("SELECT * FROM orders WHERE order_code = ?", is_pg), (order_code,))
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
    if status_filter and status_filter != "all":
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

    cursor.execute("SELECT COUNT(*) FROM orders WHERE payment_status = 'pending_review'")
    pending_approvals = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM orders WHERE status = 'approved' OR status = 'in_production'")
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

# Product catalog management
def get_products_data() -> Dict[str, Any]:
    try:
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading products.json: {e}")
        return {"products": []}

def update_product_price(product_id: str, new_price: float) -> bool:
    """Update a product's price dynamically in products.json."""
    try:
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        found = False
        for p in data.get("products", []):
            if p["id"] == product_id:
                p["price"] = new_price
                found = True
                break

        if found:
            with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to update product price: {e}")
        return False

def update_product_image(product_id: str, image_url: str) -> bool:
    """Update a product's image URL dynamically in products.json."""
    try:
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        found = False
        for p in data.get("products", []):
            if p["id"] == product_id:
                p["image_url"] = image_url
                found = True
                break

        if found:
            with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to update product image: {e}")
        return False

def add_product(
    name: str,
    price: float,
    unit: str = "per piece",
    description: str = "",
    min_order: Optional[int] = None,
    image_url: Optional[str] = None,
    product_id: Optional[str] = None
) -> Dict[str, Any]:
    """Add a new product to products.json catalog."""
    import re
    try:
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        products = data.setdefault("products", [])

        if not product_id:
            # Generate clean alphanumeric slug
            clean = re.sub(r"[^\w\s-]", "", name.lower()).strip()
            base_id = re.sub(r"[-\s]+", "_", clean) or "item"
            product_id = base_id
            counter = 1
            existing_ids = {p["id"] for p in products}
            while product_id in existing_ids:
                product_id = f"{base_id}_{counter}"
                counter += 1

        new_item = {
            "id": product_id,
            "name": name.strip(),
            "price": float(price) if price is not None else 0.0,
            "unit": unit.strip() or "each",
            "description": description.strip() or f"High quality custom printed {name.strip()} from Selora Prints.",
            "image_url": image_url or f"/product-images/{product_id}.png"
        }
        if min_order and int(min_order) > 1:
            new_item["min_order"] = int(min_order)

        products.append(new_item)

        with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"Successfully added new product: {product_id} ({name})")
        return new_item
    except Exception as e:
        logger.error(f"Failed to add product: {e}")
        raise e

def delete_product(product_id: str) -> bool:
    """Remove a product from products.json by ID."""
    try:
        with open(PRODUCTS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        products = data.get("products", [])
        initial_len = len(products)
        data["products"] = [p for p in products if p["id"] != product_id]

        if len(data["products"]) < initial_len:
            with open(PRODUCTS_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Successfully deleted product: {product_id}")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to delete product: {e}")
        return False

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

# Initialize DB on import
init_db()
