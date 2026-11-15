import os
import hmac
import hashlib
import logging
import shutil
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import HTMLResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import aiohttp

from data import database
import config

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
RECEIPTS_DIR = BASE_DIR.parent / "data" / "receipts"
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
PRODUCT_IMAGES_DIR = BASE_DIR.parent / "data" / "products_images"
PRODUCT_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Selora Prints Dashboard")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Mount static directories
app.mount("/receipts", StaticFiles(directory=str(RECEIPTS_DIR)), name="receipts")
app.mount("/product-images", StaticFiles(directory=str(PRODUCT_IMAGES_DIR)), name="product_images")

AUTH_COOKIE_NAME = "selora_auth_session"

def get_auth_token() -> str:
    """Generate signed HMAC token for the dashboard session."""
    data = f"{config.DASHBOARD_USERNAME}:{config.DASHBOARD_PASSWORD}".encode("utf-8")
    return hmac.new(config.SECRET_KEY.encode("utf-8"), data, hashlib.sha256).hexdigest()

def is_authenticated(request: Request) -> bool:
    """Check if the incoming request has a valid authentication session."""
    cookie_val = request.cookies.get(AUTH_COOKIE_NAME)
    if not cookie_val:
        return False
    return hmac.compare_digest(cookie_val, get_auth_token())

def require_api_auth(request: Request):
    """Dependency to protect all API endpoints."""
    if not is_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required. Please log in.")

class PriceUpdateRequest(BaseModel):
    price: float

class WebappOrderRequest(BaseModel):
    user_id: int
    full_name: str
    username: Optional[str] = ""
    items: str
    deadline: str
    delivery_type: str
    delivery_location: str
    notes: Optional[str] = "Placed via WebApp"

@app.get("/app", response_class=HTMLResponse)
async def webapp_store(request: Request):
    """Telegram Mini App visual storefront."""
    products_data = database.get_products_data()
    return templates.TemplateResponse(
        request=request,
        name="webapp.html",
        context={
            "products": products_data.get("products", []),
            "store_name": config.STORE_NAME,
            "cbe_account": config.PAYMENT_CBE_ACCOUNT,
            "cbe_name": config.PAYMENT_CBE_NAME,
            "telebirr": config.PAYMENT_TELEBIRR,
            "telebirr_name": config.PAYMENT_TELEBIRR_NAME
        }
    )

@app.post("/api/webapp/order")
async def webapp_submit_order(payload: WebappOrderRequest):
    """Handle orders submitted via Telegram Mini App."""
    order_code = database.save_order(
        user_id=payload.user_id,
        full_name=payload.full_name,
        username=payload.username,
        items=payload.items,
        deadline=payload.deadline,
        delivery_type=payload.delivery_type,
        delivery_location=payload.delivery_location,
        notes=payload.notes,
        has_attachment=False,
        payment_status="pending_review",
        status="pending"
    )

    if payload.user_id:
        customer_msg = (
            f"🎉 *Order Placed via Selora Store App!* 💛\n\n"
            f"🔖 *Order Code:* `{order_code}`\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"🏷 *Items:* {payload.items}\n"
            f"🗓 *Need by:* {payload.deadline}\n"
            f"🚚 *Delivery:* {payload.delivery_type} ({payload.delivery_location})\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "💳 *Pre-Payment (50% Deposit):*\n"
            f"• *CBE:* `{config.PAYMENT_CBE_ACCOUNT}` ({config.PAYMENT_CBE_NAME})\n"
            f"• *Telebirr:* `{config.PAYMENT_TELEBIRR}` ({config.PAYMENT_TELEBIRR_NAME})\n\n"
            "📸 *Please transfer the 50% deposit and send a screenshot of your payment receipt right here in this chat to confirm your order!*"
        )
        await send_telegram_notification(payload.user_id, customer_msg)

    if config.ADMIN_CHAT_ID:
        admin_text = (
            f"🚨 *NEW APP ORDER RECEIVED! — {order_code}*\n"
            f"👤 *Customer:* {payload.full_name} (@{payload.username or 'none'})\n"
            f"🆔 *User ID:* `{payload.user_id}`\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"🏷 *Items:* {payload.items}\n"
            f"🗓 *Need by:* {payload.deadline}\n"
            f"🚚 *Delivery:* {payload.delivery_type}\n"
            f"📍 *Location:* {payload.delivery_location}\n"
            f"📝 *Notes:* {payload.notes}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Customer has been notified to send their 50% deposit receipt screenshot here in chat."
        )
        await send_telegram_notification(int(config.ADMIN_CHAT_ID), admin_text)

    return {"success": True, "order_code": order_code}

async def send_telegram_notification(user_id: int, message_text: str):
    """Send Telegram message to customer when action is taken from the dashboard."""
    if not config.BOT_TOKEN:
        return
    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": user_id,
        "text": message_text,
        "parse_mode": "Markdown"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status != 200:
                    logger.warning(f"Telegram notification returned status {resp.status}")
    except Exception as e:
        logger.error(f"Failed to send Telegram notification to {user_id}: {e}")

# Authentication Routes
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if is_authenticated(request):
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={"error": None, "username": "admin"}
    )

@app.post("/login", response_class=HTMLResponse)
async def login_action(
    request: Request,
    username: str = Form(""),
    password: str = Form("")
):
    if username == config.DASHBOARD_USERNAME and password == config.DASHBOARD_PASSWORD:
        response = RedirectResponse(url="/", status_code=303)
        # Set 30-day secure cookie
        response.set_cookie(
            key=AUTH_COOKIE_NAME,
            value=get_auth_token(),
            max_age=86400 * 30,
            httponly=True,
            samesite="lax"
        )
        return response

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "error": "Invalid username or password. Please try again.",
            "username": username
        },
        status_code=401
    )

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie(AUTH_COOKIE_NAME)
    return response

@app.get("/orders/{order_code}/receipt", response_class=HTMLResponse)
async def view_order_receipt(order_code: str, request: Request):
    """View official printable customer order receipt / invoice."""
    order = database.get_order_by_code(order_code)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return templates.TemplateResponse(
        request=request,
        name="receipt.html",
        context={"order": order, "store_name": config.STORE_NAME}
    )

# Main Dashboard View
@app.get("/", response_class=HTMLResponse)
async def dashboard_index(request: Request):
    if not is_authenticated(request):
        return RedirectResponse(url="/login", status_code=303)

    stats = database.get_stats()
    orders = database.get_all_orders()
    products_data = database.get_products_data()
    products = products_data.get("products", [])

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "stats": stats,
            "orders": orders,
            "products": products,
            "store_name": config.STORE_NAME
        }
    )

# Protected API Routes
@app.get("/api/orders", dependencies=[Depends(require_api_auth)])
async def get_orders_api():
    """Returns latest orders and stats for live dashboard polling."""
    return {
        "orders": database.get_all_orders(),
        "stats": database.get_stats()
    }

@app.post("/api/orders/{order_code}/approve", dependencies=[Depends(require_api_auth)])
async def approve_order(order_code: str):
    order = database.get_order_by_code(order_code)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    database.update_order_payment(order_code, payment_status="approved", order_status="in_production")

    # Notify customer via Telegram
    customer_msg = (
        "🎉 *Payment Verified & Order Confirmed!* 💛\n\n"
        f"🔖 *Order Code:* `{order_code}`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷 *Items:* {order.get('items')}\n"
        f"🗓 *Deadline:* {order.get('deadline')}\n"
        f"🚚 *Delivery:* {order.get('delivery_type')} ({order.get('delivery_location')})\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "✅ *Your 50% deposit has been approved!* We have officially started production on your order.\n\n"
        "We will notify you as soon as your prints are ready for pickup/delivery! ✨"
    )
    await send_telegram_notification(order["user_id"], customer_msg)
    return {"success": True, "message": f"Order {order_code} approved and in production"}

@app.post("/api/orders/{order_code}/complete", dependencies=[Depends(require_api_auth)])
async def complete_order(order_code: str):
    order = database.get_order_by_code(order_code)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    database.update_order_status(order_code, "completed")

    customer_msg = (
        "✨ *Your Order is Ready!* 💛\n\n"
        f"🔖 *Order Code:* `{order_code}`\n\n"
        "Good news! Your order has been completed and is ready for pickup or delivery.\n\n"
        f"📍 *Method:* {order.get('delivery_type')} ({order.get('delivery_location')})\n\n"
        f"Thank you for choosing Selora Prints! If you have any questions, chat with the owner @{config.ADMIN_USERNAME} 🙏"
    )
    await send_telegram_notification(order["user_id"], customer_msg)
    return {"success": True, "message": f"Order {order_code} marked completed"}

@app.post("/api/orders/{order_code}/cancel", dependencies=[Depends(require_api_auth)])
async def cancel_order_api(order_code: str):
    order = database.get_order_by_code(order_code)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    database.update_order_status(order_code, "cancelled")
    return {"success": True, "message": f"Order {order_code} cancelled"}

@app.post("/api/products/add", dependencies=[Depends(require_api_auth)])
async def add_product_api(
    name: str = Form(...),
    price: float = Form(...),
    unit: str = Form("each"),
    min_order: Optional[int] = Form(None),
    description: str = Form(""),
    image: Optional[UploadFile] = File(None)
):
    """Add a new product to the catalog, with optional design photo upload."""
    import time
    import re
    if not name.strip():
        raise HTTPException(status_code=400, detail="Product name is required")

    clean_name = re.sub(r"[^\w\s-]", "", name.lower()).strip()
    slug = re.sub(r"[-\s]+", "_", clean_name) or "product"

    image_url = None
    if image and image.filename:
        ext = Path(image.filename).suffix.lower()
        if ext in [".jpg", ".jpeg", ".png", ".webp", ".svg"]:
            filename = f"{slug}_{int(time.time())}{ext}"
            dest_path = PRODUCT_IMAGES_DIR / filename
            try:
                with open(dest_path, "wb") as buffer:
                    shutil.copyfileobj(image.file, buffer)
                image_url = f"/product-images/{filename}"
            except Exception as e:
                logger.error(f"Error saving uploaded design: {e}")

    try:
        new_item = database.add_product(
            name=name,
            price=price,
            unit=unit,
            description=description,
            min_order=min_order,
            image_url=image_url
        )
        return {"success": True, "product": new_item}
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/products/{product_id}", dependencies=[Depends(require_api_auth)])
async def delete_product_api(product_id: str):
    """Delete a product from the catalog."""
    success = database.delete_product(product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"success": True, "message": f"Product {product_id} removed from catalog"}

@app.post("/api/products/{product_id}/price", dependencies=[Depends(require_api_auth)])
async def update_product_price_api(product_id: str, payload: PriceUpdateRequest):
    success = database.update_product_price(product_id, payload.price)
    if not success:
        raise HTTPException(status_code=400, detail="Product not found or invalid price")
    return {"success": True, "product_id": product_id, "new_price": payload.price}

@app.post("/api/products/{product_id}/image", dependencies=[Depends(require_api_auth)])
async def upload_product_image_api(product_id: str, file: UploadFile = File(...)):
    """Upload a new custom design/product photo directly from the dashboard."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded")

    ext = Path(file.filename).suffix.lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp", ".svg"]:
        raise HTTPException(status_code=400, detail="Invalid image format. Please upload JPG, PNG, WEBP, or SVG.")

    filename = f"{product_id}_{int(os.times().system * 1000)}{ext}"
    dest_path = PRODUCT_IMAGES_DIR / filename

    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        image_url = f"/product-images/{filename}"
        success = database.update_product_image(product_id, image_url)
        if not success:
            raise HTTPException(status_code=404, detail="Product not found")

        return {"success": True, "product_id": product_id, "image_url": image_url}
    except Exception as e:
        logger.error(f"Failed to save product image: {e}")
        raise HTTPException(status_code=500, detail="Failed to save image")

@app.get("/api/export-csv", dependencies=[Depends(require_api_auth)])
async def export_csv():
    temp_csv = BASE_DIR.parent / "data" / "selora_orders_export.csv"
    database.export_orders_to_csv(temp_csv)
    return FileResponse(
        path=temp_csv,
        filename="selora_orders.csv",
        media_type="text/csv"
    )
