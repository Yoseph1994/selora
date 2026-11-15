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
CUSTOMER_UPLOADS_DIR = BASE_DIR.parent / "data" / "customer_uploads"
CUSTOMER_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
PRODUCT_IMAGES_DIR = BASE_DIR.parent / "data" / "products_images"
PRODUCT_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
DESIGNS_IMAGES_DIR = BASE_DIR.parent / "data" / "designs_images"
DESIGNS_IMAGES_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="Selora Prints Dashboard")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Mount static directories
app.mount("/product-images", StaticFiles(directory=str(PRODUCT_IMAGES_DIR)), name="product_images")
app.mount("/designs-images", StaticFiles(directory=str(DESIGNS_IMAGES_DIR)), name="designs_images")

# Smart On-Demand Static & Cloud Handlers
@app.get("/receipts/{filename}")
async def serve_receipt(filename: str):
    """Serve payment receipt, downloading on demand from Telegram if container restarted."""
    dest_path = RECEIPTS_DIR / filename
    if dest_path.exists():
        return FileResponse(dest_path)

    # Fallback to Telegram Bot API
    order = database.get_order_by_receipt_filename(filename)
    if order and order.get("payment_screenshot_file_id") and config.BOT_TOKEN:
        file_id = order["payment_screenshot_file_id"]
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://api.telegram.org/bot{config.BOT_TOKEN}/getFile?file_id={file_id}") as info_resp:
                    if info_resp.status == 200:
                        tg_info = await info_resp.json()
                        if tg_info.get("ok"):
                            file_path = tg_info["result"]["file_path"]
                            dl_url = f"https://api.telegram.org/file/bot{config.BOT_TOKEN}/{file_path}"
                            async with session.get(dl_url) as dl_resp:
                                if dl_resp.status == 200:
                                    content = await dl_resp.read()
                                    with open(dest_path, "wb") as f:
                                        f.write(content)
                                    return FileResponse(dest_path)
        except Exception as e:
            logger.error(f"Failed to fetch receipt on demand from Telegram: {e}")

    raise HTTPException(status_code=404, detail="Receipt image not found")

@app.get("/customer-uploads/{filename}")
async def serve_customer_upload(filename: str):
    """Serve customer artwork, downloading on demand from Telegram if container restarted."""
    dest_path = CUSTOMER_UPLOADS_DIR / filename
    if dest_path.exists():
        return FileResponse(dest_path)

    # Fallback to Telegram Bot API
    order = database.get_order_by_customer_file(filename)
    if order and order.get("customer_files") and config.BOT_TOKEN:
        try:
            import json
            files_list = json.loads(order["customer_files"])
            file_id = None
            for item in files_list:
                if item.get("filename") == filename:
                    file_id = item.get("file_id")
                    break

            if file_id:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"https://api.telegram.org/bot{config.BOT_TOKEN}/getFile?file_id={file_id}") as info_resp:
                        if info_resp.status == 200:
                            tg_info = await info_resp.json()
                            if tg_info.get("ok"):
                                file_path = tg_info["result"]["file_path"]
                                dl_url = f"https://api.telegram.org/file/bot{config.BOT_TOKEN}/{file_path}"
                                async with session.get(dl_url) as dl_resp:
                                    if dl_resp.status == 200:
                                        content = await dl_resp.read()
                                        with open(dest_path, "wb") as f:
                                            f.write(content)
                                        return FileResponse(dest_path)
        except Exception as e:
            logger.error(f"Failed to fetch customer upload on demand: {e}")

    raise HTTPException(status_code=404, detail="Customer artwork not found")

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

class RejectRequest(BaseModel):
    reason: str

class WebappOrderRequest(BaseModel):
    user_id: int
    full_name: str
    username: Optional[str] = ""
    items: str
    deadline: str
    delivery_type: str
    delivery_location: str
    notes: Optional[str] = "Placed via WebApp"
    phone: Optional[str] = ""
    recipient_name: Optional[str] = ""

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
        status="pending",
        phone=payload.phone or "",
        recipient_name=payload.recipient_name or payload.full_name
    )

    if payload.user_id:
        phone_txt = f"\n📞 *Phone:* `{payload.phone}`" if payload.phone else ""
        recip_txt = f"\n👤 *Recipient:* {payload.recipient_name}" if payload.recipient_name else ""
        customer_msg = (
            f"🎉 *Order Placed via Selora Store App!* 💛\n\n"
            f"🔖 *Order Code:* `{order_code}`\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"🏷 *Items:* {payload.items}\n"
            f"🗓 *Need by:* {payload.deadline}{recip_txt}{phone_txt}\n"
            f"🚚 *Delivery:* {payload.delivery_type} ({payload.delivery_location})\n"
            "━━━━━━━━━━━━━━━━━━━━\n\n"
            "💳 *Pre-Payment (50% Deposit):*\n"
            f"• *CBE:* `{config.PAYMENT_CBE_ACCOUNT}` ({config.PAYMENT_CBE_NAME})\n"
            f"• *Telebirr:* `{config.PAYMENT_TELEBIRR}` ({config.PAYMENT_TELEBIRR_NAME})\n\n"
            "📸 *Please transfer the 50% deposit and send a screenshot of your payment receipt right here in this chat to confirm your order!*"
        )
        await send_telegram_notification(payload.user_id, customer_msg)

    if config.ADMIN_CHAT_ID:
        phone_line = f"\n📞 *Driver Contact Phone:* [{payload.phone}](tel:{payload.phone})" if payload.phone else ""
        recip_line = f"\n📦 *Recipient:* *{payload.recipient_name}*" if payload.recipient_name else ""
        admin_text = (
            f"🚨 *NEW APP ORDER RECEIVED! — {order_code}*\n"
            f"👤 *Customer:* {payload.full_name} (@{payload.username or 'none'})\n"
            f"🆔 *User ID:* `{payload.user_id}`{recip_line}{phone_line}\n"
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

async def send_telegram_notification(user_id: int, message_text: str, reply_markup: Optional[dict] = None):
    """Send Telegram message to customer when action is taken from the dashboard."""
    if not config.BOT_TOKEN or not user_id:
        return
    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": user_id,
        "text": message_text,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
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
    designs = database.get_designs()
    design_categories = database.get_design_categories()

    portfolio = database.get_portfolio_items()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "stats": stats,
            "orders": orders,
            "products": products,
            "designs": designs,
            "design_categories": design_categories,
            "portfolio": portfolio,
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

@app.post("/api/orders/{order_code}/ready", dependencies=[Depends(require_api_auth)])
async def mark_order_ready(order_code: str):
    order = database.get_order_by_code(order_code)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    database.update_order_status(order_code, "ready_for_delivery")

    recip = order.get('recipient_name') or order.get('full_name') or 'Customer'
    phone = order.get('phone') or 'N/A'

    dm_text = (
        "🎉 *Great News! Your Order is Printed & Ready to Ship!* 💛\n\n"
        f"🔖 *Order Code:* `{order_code}`\n"
        f"🏷 *Items:* {order.get('items', '')}\n"
        f"👤 *Recipient:* {recip} (`{phone}`)\n"
        "─────────────────────\n"
        "Your custom prints have finished drying & binding. Please choose how you would like to receive your package:\n\n"
        "• 🏪 *Free Store Pickup:* Pick up in person at our Ledeta store (Free of charge).\n"
        "• 🚚 *Doorstep Taxi Delivery:* Dispatched directly to your door via Yango / Feres / RIDE.\n\n"
        "⚠️ *Delivery Fee Notice:*\n"
        "The delivery fee depends on transportation distance and taxi rate (all inclusive, including Yango/Feres/RIDE) and is typically *300 – 1,000 ETB* depending on your location in Addis Ababa, paid directly to the driver upon delivery. If you prefer to avoid the fee, you are warmly welcome to visit our Ledeta office for free pickup!\n\n"
        "👉 *Tap an option below to proceed:*"
    )
    markup = {
        "inline_keyboard": [
            [{"text": "🏪 Free Store Pickup (Ledeta)", "callback_data": f"post_del:pickup:{order_code}"}],
            [{"text": "🚚 Doorstep Taxi Delivery (300-1,000 ETB)", "callback_data": f"post_del:taxi:{order_code}"}]
        ]
    }
    await send_telegram_notification(order["user_id"], dm_text, reply_markup=markup)
    return {"success": True, "message": f"Order {order_code} marked ready and delivery DM sent to customer"}

@app.post("/api/orders/{order_code}/complete", dependencies=[Depends(require_api_auth)])
async def complete_order(order_code: str):
    order = database.get_order_by_code(order_code)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    database.update_order_status(order_code, "completed")

    customer_msg = (
        "✨ *Your Order Has Been Fulfilled!* 💛\n\n"
        f"🔖 *Order Code:* `{order_code}`\n\n"
        "Your order has been successfully picked up or delivered!\n"
        "Thank you so much for choosing Selora Prints. We hope you love your prints! ✨\n\n"
        f"Any questions or feedback? Chat with us anytime: @{config.ADMIN_USERNAME} 🙏"
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

@app.post("/api/orders/{order_code}/reject", dependencies=[Depends(require_api_auth)])
async def reject_order_api(order_code: str, payload: RejectRequest):
    order = database.get_order_by_code(order_code)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    reason = payload.reason.strip() or "Artwork is low resolution or compressed. Please upload an uncompressed File/Document (📎)."
    database.update_order_rejection(order_code, reason)

    dm_text = (
        "⚠️ *Update Regarding Your Selora Prints Order*\n\n"
        f"🔖 *Order Code:* `{order_code}`\n"
        f"🏷 *Items:* {order.get('items', '')}\n"
        "─────────────────────\n"
        "Our production team reviewed your order and submitted files:\n\n"
        f"❌ *Reason:* {reason}\n\n"
        "👉 *Please tap below to send a revised high-resolution file:*"
    )
    markup = {
        "inline_keyboard": [
            [{"text": "📎 Re-upload Artwork (File/Doc)", "callback_data": f"reupload_art:{order_code}"}],
            [{"text": "💳 Re-upload Payment Receipt", "callback_data": f"reupload_rcpt:{order_code}"}]
        ]
    }
    if config.ADMIN_USERNAME:
        markup["inline_keyboard"].append([
            {"text": "💬 Contact Support", "url": f"https://t.me/{config.ADMIN_USERNAME}"}
        ])
    await send_telegram_notification(order["user_id"], dm_text, reply_markup=markup)
    return {"success": True, "message": f"Order {order_code} rejected and customer notified via DM"}

@app.post("/api/products/add", dependencies=[Depends(require_api_auth)])
async def add_product_api(
    name: str = Form(...),
    price: float = Form(...),
    unit: str = Form("each"),
    min_order: Optional[int] = Form(None),
    description: str = Form(""),
    image: Optional[UploadFile] = File(None),
    has_ready_designs: Optional[str] = Form("true")
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

    has_ready = str(has_ready_designs).lower() in ("true", "1", "yes", "on")

    try:
        new_item = database.add_product(
            name=name,
            price=price,
            unit=unit,
            description=description,
            min_order=min_order,
            image_url=image_url,
            has_ready_designs=has_ready
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

        # Overwrite canonical product file so Telegram and Dashboard find it immediately
        try:
            canonical_path = PRODUCT_IMAGES_DIR / f"{product_id}{ext}"
            shutil.copyfile(dest_path, canonical_path)
            # Ensure a PNG copy exists for Telegram fallback
            if ext != ".png":
                try:
                    from PIL import Image
                    with Image.open(dest_path) as im:
                        im.convert("RGB").save(PRODUCT_IMAGES_DIR / f"{product_id}.png", "PNG")
                except Exception:
                    pass
        except Exception as err:
            logger.warning(f"Could not update canonical product image: {err}")

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

# -------------------------------------------------------------
# DYNAMIC DESIGNS & SUBPRODUCTS API
# -------------------------------------------------------------

@app.get("/api/designs")
async def get_designs_api(product_id: Optional[str] = None, subproduct: Optional[str] = None):
    """Retrieve all designs, optionally filtered by product_id and/or subproduct."""
    designs = database.get_designs(product_id=product_id, subproduct=subproduct)
    categories = database.get_design_categories()
    return {"designs": designs, "categories": categories}

@app.post("/api/designs/add", dependencies=[Depends(require_api_auth)])
async def add_design_api(
    title: str = Form(...),
    product_id: str = Form(...),
    subproduct: str = Form(...),
    description: str = Form(""),
    image: UploadFile = File(...)
):
    """Add a new custom design/subproduct to designs.json and save image."""
    import time
    import re
    if not title.strip():
        raise HTTPException(status_code=400, detail="Design title is required")
    if not product_id.strip():
        raise HTTPException(status_code=400, detail="Product selection is required")

    clean_title = re.sub(r"[^\w\s-]", "", title.lower()).strip()
    slug = re.sub(r"[-\s]+", "_", clean_title) or "design"
    design_id = f"des_{product_id}_{slug}_{int(time.time())}"

    ext = Path(image.filename).suffix.lower() if image and image.filename else ".png"
    if ext not in [".jpg", ".jpeg", ".png", ".webp", ".svg"]:
        ext = ".png"

    filename = f"{design_id}{ext}"
    dest_path = DESIGNS_IMAGES_DIR / filename

    try:
        with open(dest_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)

        # Ensure a PNG copy exists for Telegram fallback
        png_filename = f"{design_id}.png"
        png_path = DESIGNS_IMAGES_DIR / png_filename
        if ext != ".png":
            try:
                from PIL import Image
                with Image.open(dest_path) as im:
                    im.convert("RGB").save(png_path, "PNG")
            except Exception as e:
                logger.warning(f"Could not convert design to PNG: {e}")
                png_filename = filename

        new_design = database.add_design(
            title=title.strip(),
            product_id=product_id.strip(),
            subproduct=subproduct.strip() or "Standard",
            description=description.strip(),
            image_url=f"/designs-images/{png_filename}",
            design_id=design_id
        )
        return {"success": True, "design": new_design}
    except Exception as e:
        logger.error(f"Failed to add design: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save design: {str(e)}")

@app.delete("/api/designs/{design_id}", dependencies=[Depends(require_api_auth)])
async def delete_design_api(design_id: str):
    """Delete a design by ID."""
    success = database.delete_design(design_id)
    if not success:
        raise HTTPException(status_code=404, detail="Design not found")

    # Clean up static files
    for ext in [".png", ".jpg", ".jpeg", ".webp"]:
        f = DESIGNS_IMAGES_DIR / f"{design_id}{ext}"
        if f.exists():
            try:
                f.unlink()
            except Exception:
                pass

    return {"success": True, "message": f"Design {design_id} deleted successfully"}

# ─── PORTFOLIO / OUR WORKS ENDPOINTS ─────────────────────────

@app.get("/api/portfolio", dependencies=[Depends(require_api_auth)])
async def get_portfolio_api():
    """Retrieve all showcase portfolio works."""
    return {"items": database.get_portfolio_items()}

@app.post("/api/portfolio/add", dependencies=[Depends(require_api_auth)])
async def add_portfolio_api(
    title: str = Form(...),
    category: str = Form("Custom Prints"),
    description: str = Form(""),
    image: Optional[UploadFile] = File(None)
):
    """Add a new finished work to the portfolio showcase."""
    import time
    if not title.strip():
        raise HTTPException(status_code=400, detail="Title is required")

    image_url = "/product-images/stickers.png"
    if image and image.filename:
        ext = Path(image.filename).suffix.lower()
        if ext in [".jpg", ".jpeg", ".png", ".webp", ".svg"]:
            filename = f"work_{int(time.time())}{ext}"
            dest_path = PRODUCT_IMAGES_DIR / filename
            try:
                with open(dest_path, "wb") as buffer:
                    shutil.copyfileobj(image.file, buffer)
                image_url = f"/product-images/{filename}"
            except Exception as e:
                logger.error(f"Error saving portfolio image: {e}")

    item = database.add_portfolio_item(
        title=title.strip(),
        category=category.strip(),
        description=description.strip(),
        image_url=image_url
    )
    return {"success": True, "item": item}

@app.delete("/api/portfolio/{item_id}", dependencies=[Depends(require_api_auth)])
async def delete_portfolio_api(item_id: str):
    """Delete a showcase item from portfolio."""
    success = database.delete_portfolio_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Portfolio item not found")
    return {"success": True, "message": f"Portfolio item {item_id} deleted"}
