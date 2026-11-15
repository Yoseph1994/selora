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
DESIGNS_FILE = DATA_DIR / "designs.json"
PORTFOLIO_FILE = DATA_DIR / "portfolio.json"

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
            ALTER TABLE orders ADD COLUMN IF NOT EXISTS customer_files TEXT;
            ALTER TABLE orders ADD COLUMN IF NOT EXISTS rejection_reason TEXT;
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
            "rejection_reason": "TEXT"
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
    recipient_name: Optional[str] = None,
    customer_files: Optional[str] = "[]"
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
            phone, recipient_name, customer_files
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    params = (
        user_id, full_name, username or "", items, deadline,
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
    product_id: Optional[str] = None,
    has_ready_designs: bool = True
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
            "image_url": image_url or f"/product-images/{product_id}.png",
            "has_ready_designs": bool(has_ready_designs)
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

# -------------------------------------------------------------
# DYNAMIC DESIGNS & SUBPRODUCTS MANAGEMENT
# -------------------------------------------------------------

def get_designs_data() -> Dict[str, Any]:
    """Load raw designs data from designs.json."""
    if not DESIGNS_FILE.exists():
        return {"designs": []}
    try:
        with open(DESIGNS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading designs.json: {e}")
        return {"designs": []}

def get_designs(product_id: Optional[str] = None, subproduct: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch designs filtered optionally by product_id and/or subproduct."""
    data = get_designs_data()
    designs = data.get("designs", [])
    if product_id and product_id != "all":
        designs = [d for d in designs if d.get("product_id") == product_id]
    if subproduct and subproduct != "all":
        designs = [d for d in designs if d.get("subproduct", "").lower() == subproduct.lower()]
    return designs

def get_design_by_id(design_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single design by its ID."""
    data = get_designs_data()
    for d in data.get("designs", []):
        if d.get("id") == design_id:
            return d
    return None

def add_design(
    title: str,
    product_id: str,
    subproduct: str,
    description: str = "",
    image_url: str = "",
    product_name: Optional[str] = None,
    design_id: Optional[str] = None
) -> Dict[str, Any]:
    """Add a new design or subproduct design to designs.json."""
    import re
    data = get_designs_data()
    designs = data.setdefault("designs", [])

    if not design_id:
        clean = re.sub(r"[^\w\s-]", "", title.lower()).strip()
        base_id = f"des_{product_id}_{re.sub(r'[-\s]+', '_', clean)}" or f"des_{int(datetime.now().timestamp())}"
        design_id = base_id
        counter = 1
        existing_ids = {d.get("id") for d in designs}
        while design_id in existing_ids:
            design_id = f"{base_id}_{counter}"
            counter += 1

    if not product_name:
        prod_data = get_products_data()
        for p in prod_data.get("products", []):
            if p["id"] == product_id:
                product_name = p["name"]
                break
        if not product_name:
            product_name = product_id.replace("_", " ").title()

    new_design = {
        "id": design_id,
        "title": title.strip(),
        "product_id": product_id.strip(),
        "product_name": product_name.strip(),
        "subproduct": subproduct.strip(),
        "description": description.strip(),
        "image_url": image_url or f"/designs-images/{design_id}.png",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    designs.append(new_design)

    with open(DESIGNS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    logger.info(f"Added new design: {design_id} - {title} ({subproduct})")
    return new_design

def delete_design(design_id: str) -> bool:
    """Delete a design by ID."""
    data = get_designs_data()
    designs = data.get("designs", [])
    initial_len = len(designs)
    data["designs"] = [d for d in designs if d.get("id") != design_id]

    if len(data["designs"]) < initial_len:
        with open(DESIGNS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Deleted design: {design_id}")
        return True
    return False

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

# ─── PORTFOLIO / OUR WORKS ────────────────────────────────────

def get_portfolio_items() -> List[Dict[str, Any]]:
    """Get list of showcased past works."""
    if not PORTFOLIO_FILE.exists():
        return []
    try:
        with open(PORTFOLIO_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("items", [])
    except Exception:
        return []

def save_portfolio_items(items: List[Dict[str, Any]]):
    with open(PORTFOLIO_FILE, "w", encoding="utf-8") as f:
        json.dump({"items": items}, f, indent=2, ensure_ascii=False)

def add_portfolio_item(title: str, category: str, description: str, image_url: str) -> Dict[str, Any]:
    items = get_portfolio_items()
    new_id = f"work_{int(datetime.now().timestamp())}"
    item = {
        "id": new_id,
        "title": title.strip(),
        "category": category.strip(),
        "description": description.strip(),
        "image_url": image_url,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    items.append(item)
    save_portfolio_items(items)
    return item

def delete_portfolio_item(item_id: str) -> bool:
    items = get_portfolio_items()
    new_items = [i for i in items if i.get("id") != item_id]
    if len(new_items) < len(items):
        save_portfolio_items(new_items)
        return True
    return False

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
    """Mark order rejected and record reason in notes and rejection_reason column."""
    conn, is_pg = get_connection()
    cursor = conn.cursor()
    updated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rejection_text = f"REJECTED REASON: {reason}"
    cursor.execute(q("""
        UPDATE orders
        SET status = 'rejected', payment_status = 'rejected',
            rejection_reason = ?,
            notes = CASE WHEN notes IS NULL OR notes = '' THEN ? ELSE notes || ' | ' || ? END,
            updated_at = ?
        WHERE order_code = ?
    """, is_pg), (reason, rejection_text, rejection_text, updated_at, order_code))
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return success

# Initialize DB on import
init_db()
