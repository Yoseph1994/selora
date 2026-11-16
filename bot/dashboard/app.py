import os
import re
import time
import json
import hmac
import hashlib
import logging
import shutil
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form, Depends, Response
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

# Mount Next.js Telegram Mini App
MINIAPP_CANDIDATES = [
    BASE_DIR.parent.parent / "miniapp" / "out",
    BASE_DIR.parent / "miniapp_out",
    BASE_DIR.parent / "miniapp" / "out",
    BASE_DIR / "miniapp_out"
]
MINIAPP_OUT_DIR = None
for candidate in MINIAPP_CANDIDATES:
    if candidate.exists() and (candidate / "index.html").exists():
        MINIAPP_OUT_DIR = candidate
        break

if MINIAPP_OUT_DIR:
    @app.get("/miniapp")
    async def miniapp_noslash():
        return RedirectResponse(url="/miniapp/", status_code=301)

    @app.get("/miniapp/")
    async def miniapp_slash_index():
        return FileResponse(MINIAPP_OUT_DIR / "index.html")

    app.mount("/miniapp", StaticFiles(directory=str(MINIAPP_OUT_DIR), html=True), name="miniapp")
else:
    @app.get("/miniapp")
    @app.get("/miniapp/")
    async def miniapp_fallback(request: Request):
        return await webapp_store(request)

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
    user, pwd = database.get_admin_credentials()
    data = f"{user}:{pwd}".encode("utf-8")
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

class CredentialsUpdateRequest(BaseModel):
    current_password: str
    new_username: str
    new_password: str

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

@app.get("/app")
async def webapp_store(request: Request):
    """Telegram Mini App visual storefront."""
    products_data = database.get_products_data()
    designs_data = database.get_designs_data()
    return templates.TemplateResponse(
        request=request,
        name="webapp.html",
        context={
            "products": products_data.get("products", []),
            "designs": designs_data.get("designs", []),
            "portfolio": database.get_portfolio_items(),
            "store_name": config.STORE_NAME,
            "cbe_account": config.PAYMENT_CBE_ACCOUNT,
            "cbe_name": config.PAYMENT_CBE_NAME,
            "telebirr": config.PAYMENT_TELEBIRR,
            "telebirr_name": config.PAYMENT_TELEBIRR_NAME,
            "max_daily_orders": getattr(config, "MAX_DAILY_ORDERS", 100),
            "max_daily_rush_orders": getattr(config, "MAX_DAILY_RUSH_ORDERS", 50),
            "rush_order_fee": getattr(config, "RUSH_ORDER_FEE", 200),
            "support_username": getattr(config, "SUPPORT_USERNAME", "Keb_g")
        }
    )

@app.post("/api/webapp/order")
async def webapp_submit_order(payload: WebappOrderRequest):
    """Handle orders submitted via Telegram Mini App."""
    deadline_iso = database.normalize_deadline_to_iso(payload.deadline)
    if deadline_iso:
        is_rush = "rush" in (payload.notes or "").lower() or "urgent" in (payload.notes or "").lower()
        is_valid, msg = database.check_date_capacity(
            deadline_iso,
            is_rush=is_rush,
            max_daily=getattr(config, "MAX_DAILY_ORDERS", 100),
            max_rush=getattr(config, "MAX_DAILY_RUSH_ORDERS", 50)
        )
        if not is_valid:
            raise HTTPException(status_code=400, detail=msg)

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
            f"🚨 *NEW APP ORDER RECEIVED! : {order_code}*\n"
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

@app.get("/api/webapp/config")
async def webapp_get_config():
    """Retrieve active store config, payment accounts, products, designs, and portfolio from DB."""
    products_data = database.get_products_data()
    designs_data = database.get_designs_data()
    portfolio_data = database.get_portfolio_items()
    return {
        "ok": True,
        "store": {
            "store_name": config.STORE_NAME,
            "cbe_account": config.PAYMENT_CBE_ACCOUNT,
            "cbe_name": config.PAYMENT_CBE_NAME,
            "telebirr": config.PAYMENT_TELEBIRR,
            "telebirr_name": config.PAYMENT_TELEBIRR_NAME,
            "location": "Ledeta, Addis Ababa",
            "max_daily_orders": getattr(config, "MAX_DAILY_ORDERS", 100),
            "max_daily_rush_orders": getattr(config, "MAX_DAILY_RUSH_ORDERS", 50),
            "rush_order_fee": getattr(config, "RUSH_ORDER_FEE", 200),
            "support_username": getattr(config, "SUPPORT_USERNAME", "Keb_g")
        },
        "products": products_data.get("products", []),
        "designs": designs_data.get("designs", []),
        "portfolio": portfolio_data
    }

@app.get("/api/webapp/calendar-availability")
async def webapp_calendar_availability():
    """Retrieve date capacities, Sunday rest day status, and earliest available production dates."""
    max_daily = getattr(config, "MAX_DAILY_ORDERS", 100)
    max_rush = getattr(config, "MAX_DAILY_RUSH_ORDERS", 50)
    rush_fee = getattr(config, "RUSH_ORDER_FEE", 200)

    capacities = database.get_daily_booked_capacities()
    std_earliest = database.get_earliest_available_date(is_rush=False, max_daily=max_daily, max_rush=max_rush)
    rush_earliest = database.get_earliest_available_date(is_rush=True, max_daily=max_daily, max_rush=max_rush)

    return {
        "ok": True,
        "capacities": capacities,
        "max_daily_orders": max_daily,
        "max_daily_rush_orders": max_rush,
        "rush_order_fee": rush_fee,
        "earliest_standard_iso": std_earliest.isoformat(),
        "earliest_rush_iso": rush_earliest.isoformat()
    }

@app.get("/api/webapp/track/{order_code}")
async def webapp_track_order(order_code: str):
    """Retrieve real order tracking status for Mini App."""
    clean_code = order_code.strip().upper()
    order = database.get_order_by_code(clean_code)
    if not order:
        return {"ok": False, "error": f"No order found matching '{clean_code}'"}
    enrich_order_data(order)
    return {
        "ok": True,
        "order": {
            "order_code": order["order_code"],
            "status": order["status"],
            "payment_status": order.get("payment_status", "pending_review"),
            "items": order["items"],
            "deadline": order["deadline"],
            "delivery_type": order["delivery_type"],
            "delivery_location": order["delivery_location"],
            "recipient_name": order.get("recipient_name") or order.get("full_name"),
            "phone": order.get("phone") or "",
            "notes": order.get("notes") or "",
            "created_at": order["created_at"],
            "rejection_reason": order.get("rejection_reason") or "",
            "custom_instructions": order.get("custom_instructions") or "",
            "artwork_files": order.get("artwork_files") or []
        }
    }

@app.get("/api/webapp/my-orders/{user_id}")
async def webapp_my_orders(user_id: int):
    """Retrieve active (non-completed) orders for the customer."""
    try:
        user_orders = database.get_orders_by_user(user_id)
        active_list = []
        for o in user_orders:
            enrich_order_data(o)
            st = (o.get("status") or "pending").lower()
            # Ignore completed or cancelled orders
            if st in ("completed", "cancelled"):
                continue
            active_list.append({
                "order_code": o.get("order_code"),
                "status": o.get("status", "pending"),
                "payment_status": o.get("payment_status", "pending_review"),
                "items": o.get("items", ""),
                "deadline": o.get("deadline", ""),
                "delivery_type": o.get("delivery_type", ""),
                "delivery_location": o.get("delivery_location", ""),
                "total_price": o.get("total_price", 0),
                "deposit_amount": o.get("deposit_amount", 0),
                "rejection_reason": o.get("rejection_reason") or "",
                "created_at": o.get("created_at", "")
            })
        return {"ok": True, "orders": active_list[:10]}
    except Exception as e:
        logger.error(f"Error fetching user active orders: {e}")
        return {"ok": False, "orders": []}

@app.post("/api/webapp/order/{order_code}/reupload-receipt")
async def webapp_reupload_receipt(
    order_code: str,
    receipt_file: UploadFile = File(...),
    notes: Optional[str] = Form("")
):
    """Allow customer in Mini App to re-upload deposit proof if order was rejected."""
    clean_code = order_code.strip().upper()
    order = database.get_order_by_code(clean_code)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {clean_code} not found")

    ext = Path(receipt_file.filename).suffix or ".jpg"
    rec_name = f"reupload_rec_{clean_code}_{int(time.time())}{ext}"
    rec_path = RECEIPTS_DIR / rec_name
    content = await receipt_file.read()
    with open(rec_path, "wb") as f:
        f.write(content)

    database.update_order_receipt(clean_code, file_id="", filename=rec_name)

    # Notify admin with new receipt photo and approval buttons
    if config.ADMIN_CHAT_ID:
        admin_text = (
            f"🔄 *UPDATED PAYMENT RECEIPT RE-UPLOADED! : {clean_code}*\n"
            f"👤 *Customer:* {order.get('full_name')} (@{order.get('username') or 'none'})\n"
            f"🏷 *Items:* {order.get('items')}\n"
            f"📞 *Phone:* {order.get('phone')}\n"
            f"📝 *Customer Note:* {notes.strip() if notes else 'Updated receipt attached'}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👉 Please verify the new payment receipt below:"
        )
        approval_keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ Approve 50% Deposit", "callback_data": f"pay_approve:{clean_code}"},
                    {"text": "❌ Reject Again", "callback_data": f"pay_reject:{clean_code}"}
                ],
                [
                    {"text": "💬 DM Customer", "url": f"tg://user?id={order.get('user_id')}"},
                    {"text": "🌐 View on Dashboard", "url": config.DASHBOARD_PUBLIC_URL}
                ]
            ]
        }
        await send_telegram_photo(int(config.ADMIN_CHAT_ID), rec_path, admin_text, approval_keyboard)

    # Notify customer via DM
    if order.get("user_id"):
        cust_text = (
            f"✓ *Updated Receipt Received for Order `{clean_code}`!*\n\n"
            "Our studio team has been notified and is verifying your updated payment proof. You will be notified once verified!"
        )
        await send_telegram_notification(order["user_id"], cust_text)

    return {"ok": True, "message": "Receipt re-uploaded successfully", "order_code": clean_code}

@app.post("/api/webapp/order/{order_code}/reupload-artwork")
async def webapp_reupload_artwork(
    order_code: str,
    artwork_file: Optional[UploadFile] = File(None),
    artwork_files: Optional[list[UploadFile]] = File(None),
    notes: Optional[str] = Form("")
):
    """Allow customer in Mini App to re-upload print artwork files if order was rejected."""
    clean_code = order_code.strip().upper()
    order = database.get_order_by_code(clean_code)
    if not order:
        raise HTTPException(status_code=404, detail=f"Order {clean_code} not found")

    files_to_process = []
    if artwork_files and isinstance(artwork_files, list):
        files_to_process.extend(artwork_files)
    if artwork_file and hasattr(artwork_file, "filename") and artwork_file.filename and artwork_file not in files_to_process:
        files_to_process.append(artwork_file)

    if not files_to_process:
        raise HTTPException(status_code=400, detail="No artwork files provided")

    new_files_list = []
    for f in files_to_process:
        ext = Path(f.filename).suffix or ".jpg"
        clean_base = re.sub(r'[^a-zA-Z0-9_\-]', '_', Path(f.filename).stem)[:30]
        art_name = f"reupload_art_{clean_code}_{int(time.time())}_{clean_base}_{len(new_files_list)}{ext}"
        art_path = CUSTOMER_UPLOADS_DIR / art_name
        content = await f.read()
        with open(art_path, "wb") as out_f:
            out_f.write(content)
        new_files_list.append({
            "filename": art_name,
            "file_id": None,
            "type": "customer_artwork",
            "original_name": f.filename,
            "url": f"/customer-uploads/{art_name}"
        })

    database.update_order_artwork(clean_code, customer_files=json.dumps(new_files_list))

    # Notify admin
    if config.ADMIN_CHAT_ID:
        admin_text = (
            f"🔄 *UPDATED ARTWORK RE-UPLOADED! : {clean_code}*\n"
            f"👤 *Customer:* {order.get('full_name')} (@{order.get('username') or 'none'})\n"
            f"🏷 *Items:* {order.get('items')}\n"
            f"📎 *Files:* {len(new_files_list)} new file(s) attached\n"
            f"📝 *Customer Note:* {notes.strip() if notes else 'Updated artwork files uploaded'}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "👉 Please review the updated artwork in the Selora Dashboard."
        )
        markup = {
            "inline_keyboard": [
                [
                    {"text": "💬 DM Customer", "url": f"tg://user?id={order.get('user_id')}"},
                    {"text": "🌐 View on Dashboard", "url": config.DASHBOARD_PUBLIC_URL}
                ]
            ]
        }
        await send_telegram_notification(int(config.ADMIN_CHAT_ID), admin_text, markup)

    # Notify customer via DM
    if order.get("user_id"):
        cust_text = (
            f"✓ *Updated Artwork Received for Order `{clean_code}`!*\n\n"
            "Our studio team has received your updated print file(s) and is reviewing them for production."
        )
        await send_telegram_notification(order["user_id"], cust_text)

    return {"ok": True, "message": "Artwork re-uploaded successfully", "order_code": clean_code}

@app.post("/api/webapp/order-full")
async def webapp_submit_order_full(
    user_id: int = Form(...),
    full_name: str = Form(...),
    username: Optional[str] = Form(""),
    items: str = Form(...),
    deadline: str = Form(...),
    delivery_type: str = Form(...),
    delivery_location: str = Form(...),
    notes: Optional[str] = Form(""),
    phone: Optional[str] = Form(""),
    recipient_name: Optional[str] = Form(""),
    total_price: Optional[float] = Form(0.0),
    deposit_amount: Optional[float] = Form(0.0),
    rush_fee: Optional[float] = Form(0.0),
    design_fee: Optional[float] = Form(0.0),
    design_note: Optional[str] = Form(""),
    payment_method: Optional[str] = Form("CBE"),
    transaction_ref: Optional[str] = Form(""),
    artwork_file: Optional[UploadFile] = File(None),
    artwork_files: Optional[list[UploadFile]] = File(None),
    receipt_file: Optional[UploadFile] = File(None)
):
    """Handle full order submission with in-app artwork and receipt proof uploads matching bot business logic."""
    deadline_iso = database.normalize_deadline_to_iso(deadline)
    if deadline_iso:
        is_rush = bool(rush_fee and rush_fee > 0)
        is_valid, msg = database.check_date_capacity(
            deadline_iso,
            is_rush=is_rush,
            max_daily=getattr(config, "MAX_DAILY_ORDERS", 100),
            max_rush=getattr(config, "MAX_DAILY_RUSH_ORDERS", 50)
        )
        if not is_valid:
            raise HTTPException(status_code=400, detail=msg)

    customer_files_list = []
    has_attachment = False

    # 1. Process customer artwork (single or multiple files, e.g. Polaroids)
    files_to_process = []
    if artwork_files and isinstance(artwork_files, list):
        files_to_process.extend(artwork_files)
    if artwork_file and hasattr(artwork_file, "filename") and artwork_file.filename and artwork_file not in files_to_process:
        files_to_process.append(artwork_file)

    for f in files_to_process:
        if f and f.filename:
            try:
                ext = Path(f.filename).suffix or ".jpg"
                clean_base = re.sub(r'[^a-zA-Z0-9_\-]', '_', Path(f.filename).stem)[:30]
                art_name = f"art_{int(time.time())}_{clean_base}_{len(customer_files_list)}{ext}"
                art_path = CUSTOMER_UPLOADS_DIR / art_name
                content = await f.read()
                with open(art_path, "wb") as out_f:
                    out_f.write(content)
                customer_files_list.append({
                    "filename": art_name,
                    "file_id": None,
                    "type": "customer_artwork",
                    "original_name": f.filename,
                    "url": f"/customer-uploads/{art_name}"
                })
                has_attachment = True
            except Exception as e:
                logger.error(f"Failed to save customer artwork file {f.filename}: {e}")

    # 2. Process payment receipt
    receipt_filename = None
    if receipt_file and hasattr(receipt_file, "filename") and receipt_file.filename:
        try:
            ext = Path(receipt_file.filename).suffix or ".jpg"
            clean_base = re.sub(r'[^a-zA-Z0-9_\-]', '_', Path(receipt_file.filename).stem)[:30]
            rec_name = f"rec_{int(time.time())}_{clean_base}{ext}"
            rec_path = RECEIPTS_DIR / rec_name
            content = await receipt_file.read()
            with open(rec_path, "wb") as f:
                f.write(content)
            receipt_filename = rec_name
        except Exception as e:
            logger.error(f"Failed to save payment receipt file: {e}")

    # 3. Construct clean notes (Customer Customization Instructions)
    note_parts = []
    if design_note:
        note_parts.append(f"Design: {design_note}")
    if notes and notes.strip():
        note_parts.append(f"Custom Note: {notes.strip()}")
    if transaction_ref and transaction_ref.strip():
        note_parts.append(f"Ref: {transaction_ref.strip()}")
    if total_price:
        note_parts.append(f"Total: {total_price:.0f} ETB (Deposit: {deposit_amount:.0f} ETB)")
    full_notes = " | ".join(note_parts)

    # 4. Save to database
    order_code = database.save_order(
        user_id=user_id,
        full_name=full_name,
        username=username or "",
        items=items,
        deadline=deadline,
        delivery_type=delivery_type,
        delivery_location=delivery_location,
        notes=full_notes,
        has_attachment=has_attachment,
        payment_screenshot_file_id=None,
        payment_screenshot_filename=receipt_filename,
        payment_status="pending_review",
        status="pending",
        phone=phone or "",
        recipient_name=recipient_name or full_name,
        customer_files=json.dumps(customer_files_list)
    )

    # 5. Customer Notification (Exact match to bot/handlers/order.py lines 1378-1397)
    if user_id:
        recip_disp = recipient_name or full_name
        phone_disp = phone or "N/A"
        loc_disp = delivery_location or "Store Pickup"

        customer_msg = (
            "─────────────────────\n"
            "       ✦  Order Confirmed  ✦\n"
            "─────────────────────\n\n"
            f"🔖 *Order Code:* `{order_code}`\n\n"
            f"▸ *Items:* {items}\n"
            f"▸ *Total:* {total_price:.0f} ETB\n"
            f"▸ *Deposit:* {deposit_amount:.0f} ETB\n"
            f"▸ *Deadline:* {deadline}\n"
            f"▸ *Recipient:* {recip_disp}\n"
            f"▸ *Phone:* {phone_disp}\n"
            f"▸ *Delivery:* {delivery_type} ({loc_disp})\n\n"
            "─────────────────────\n"
            "Status: *Pending Review*\n"
            "_We're verifying your deposit; you'll be notified once approved and production begins._"
        )
        if config.ADMIN_USERNAME:
            customer_msg += f"\n\nQuestions? @{config.ADMIN_USERNAME}"
        await send_telegram_notification(user_id, customer_msg)

    # 6. Admin Notification (Exact match to bot/handlers/order.py lines 1400-1449)
    if config.ADMIN_CHAT_ID:
        rush_badge = "\n⚡ *PRIORITY:* URGENT 2-DAY RUSH (+200 ETB)" if (rush_fee and rush_fee > 0) else ""
        design_badge = f"\n🎨 *DESIGN:* {design_note}" if design_note else ""

        phone_val = phone or "N/A"
        recip_val = recipient_name or full_name
        maps_val = None
        if "https://maps.google.com" in delivery_location:
            m = re.search(r"(https?://maps\.google\.com[^\s|]+)", delivery_location)
            if m:
                maps_val = m.group(1)
        nav_line = f"\n🗺️ *Driver Navigation Link (RIDE / Yango / Feres):*\n[📍 Open GPS Coordinates in Google Maps]({maps_val})" if maps_val else ""

        timestamp = time.strftime("%Y-%m-%d %H:%M")
        username_str = f"@{username}" if username else "no username"

        admin_text = (
            f"🚨 *NEW ORDER & PAYMENT SUBMITTED! : {order_code}*{rush_badge}{design_badge}\n"
            f"⏰ *Time:* {timestamp}\n"
            f"👤 *Customer:* [{full_name}](tg://user?id={user_id}) ({username_str})\n"
            f"🆔 *Telegram ID:* `{user_id}`\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 *Recipient:* *{recip_val}*\n"
            f"📞 *Driver Call Phone:* [{phone_val}](tel:{phone_val})\n"
            f"🚚 *Method:* {delivery_type}\n"
            f"📍 *Location:* {delivery_location}{nav_line}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"🏷 *Items:* {items}\n"
            f"💰 *Total:* `{total_price:.0f} ETB` | *50% Deposit:* `{deposit_amount:.0f} ETB`\n"
            f"🗓 *Needed By:* {deadline}\n"
            f"📝 *Details:* {full_notes}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "💰 *Payment Receipt Attached Below.* Please verify and tap an action:"
        )

        approval_keyboard = {
            "inline_keyboard": [
                [
                    {"text": "✅ Approve 50% Deposit", "callback_data": f"pay_approve:{order_code}"},
                    {"text": "❌ Reject", "callback_data": f"pay_reject:{order_code}"}
                ],
                [
                    {"text": "💬 DM Customer", "url": f"tg://user?id={user_id}"},
                    {"text": "🌐 View on Dashboard", "url": config.DASHBOARD_PUBLIC_URL}
                ]
            ]
        }

        # Send photo with receipt if available, or fallback to text message
        if receipt_filename and (RECEIPTS_DIR / receipt_filename).exists():
            await send_telegram_photo(int(config.ADMIN_CHAT_ID), RECEIPTS_DIR / receipt_filename, admin_text, approval_keyboard)
        else:
            await send_telegram_notification(int(config.ADMIN_CHAT_ID), admin_text, approval_keyboard)

    return {"ok": True, "success": True, "order_code": order_code}


async def send_telegram_photo(chat_id: int, photo_path: Path, caption: str, reply_markup: Optional[dict] = None):
    """Send photo with caption and inline keyboard to Telegram (e.g. for admin receipt verification)."""
    if not config.BOT_TOKEN or not chat_id or not photo_path.exists():
        return
    url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendPhoto"
    data = aiohttp.FormData()
    data.add_field("chat_id", str(chat_id))
    data.add_field("caption", caption[:1024])
    data.add_field("parse_mode", "Markdown")
    if reply_markup:
        data.add_field("reply_markup", json.dumps(reply_markup))
    try:
        with open(photo_path, "rb") as f:
            data.add_field("photo", f.read(), filename=photo_path.name)
        async with aiohttp.ClientSession() as session:
            async with session.post(url, data=data) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    logger.warning(f"Telegram sendPhoto failed with status {resp.status}: {text}")
    except Exception as e:
        logger.error(f"Error sending photo to Telegram: {e}")


async def send_telegram_notification(user_id: int, message_text: str, reply_markup: Optional[dict] = None):
    """Send Telegram message to customer via bot DM and additionally via Telegram Business account."""
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

            # Additionally send via connected Telegram Business Account
            b_conn = database.get_business_connection()
            if b_conn and b_conn.get("connection_id"):
                b_payload = {
                    "chat_id": user_id,
                    "business_connection_id": b_conn["connection_id"],
                    "text": message_text,
                    "parse_mode": "Markdown"
                }
                if reply_markup:
                    b_payload["reply_markup"] = reply_markup
                try:
                    async with session.post(url, json=b_payload) as b_resp:
                        if b_resp.status == 200:
                            logger.info(f"Notification also delivered via Telegram Business connection to {user_id}")
                        else:
                            logger.warning(f"Telegram Business notification returned status {b_resp.status}")
                except Exception as be:
                    logger.warning(f"Could not send via Telegram Business connection: {be}")
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
        context={"error": None, "username": ""}
    )

@app.post("/login", response_class=HTMLResponse)
async def login_action(
    request: Request,
    username: str = Form(""),
    password: str = Form("")
):
    admin_user, admin_pwd = database.get_admin_credentials()
    if username == admin_user and password == admin_pwd:
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

def enrich_order_data(o: dict) -> dict:
    """Enrich raw database order record with explicitly parsed columns for the production staff."""
    import re
    import json
    raw_notes = o.get("notes") or ""

    # Strip any historical rejection strings from customer customization notes
    cleaned_notes = re.sub(r"(?:\s*\|\s*)?REJECTED\s*REASON:.*$", "", raw_notes, flags=re.IGNORECASE).strip()
    cleaned_notes = re.sub(r"(?:\s*\|\s*)?Rejection\s*Reason:.*$", "", cleaned_notes, flags=re.IGNORECASE).strip()

    # 1. Custom Notes / Special Customer Instructions (What the customer requested)
    custom_m = re.search(r"Custom Note:\s*([^|]+)", cleaned_notes, re.IGNORECASE)
    if custom_m:
        ci = custom_m.group(1).strip()
        o["custom_instructions"] = "" if ci.lower() in ("none", "null", "n/a", "") else ci
    else:
        # Check if freeform text was provided that isn't a system tag
        parts = [p.strip() for p in cleaned_notes.split("|") if p.strip()]
        cust_parts = []
        for p in parts:
            if not re.match(r"^(Deposit|Total|GPS|Ready Design|Design Note|Design|Paid via|Payment|Ref|Payment Method)\b", p, re.IGNORECASE):
                p_lower = p.lower()
                if (
                    p_lower not in ("none", "null", "n/a", "placed via webapp")
                    and not p_lower.startswith(("customer artwork", "ready design", "selora custom design", "paid via", "payment", "cbe", "telebirr"))
                ):
                    cust_parts.append(p)
        o["custom_instructions"] = " | ".join(cust_parts) if cust_parts else ""

    # 2. Rejection reason (Kept strictly separate from customer instructions)
    rej_reason = (o.get("rejection_reason") or "").strip()
    if not rej_reason:
        rej_m = re.search(r"REJECTED\s*REASON:\s*(.+)$", raw_notes, re.IGNORECASE)
        if rej_m:
            rej_reason = rej_m.group(1).strip()
    o["rejection_reason"] = rej_reason

    # 3. Design template name
    design_m = re.search(r"Ready Design:\s*([^|]+)", cleaned_notes, re.IGNORECASE)
    o["design_name"] = design_m.group(1).strip() if design_m else ""

    # 4. Financial breakdown (Total, Deposit, Balance)
    tot_m = re.search(r"Total:\s*([\d,]+(?:\.\d+)?)\s*ETB", cleaned_notes, re.IGNORECASE)
    dep_m = re.search(r"Deposit:\s*([\d,]+(?:\.\d+)?)\s*ETB", cleaned_notes, re.IGNORECASE)
    o["total_etb"] = float(tot_m.group(1).replace(",", "")) if tot_m else None
    o["deposit_etb"] = float(dep_m.group(1).replace(",", "")) if dep_m else None
    if o["total_etb"] is not None and o["deposit_etb"] is not None:
        o["balance_etb"] = max(0.0, o["total_etb"] - o["deposit_etb"])
    else:
        o["balance_etb"] = None

    # 5. Customer uploaded artwork files list
    cust_files_raw = o.get("customer_files") or "[]"
    try:
        f_list = json.loads(cust_files_raw)
        o["artwork_files"] = f_list if isinstance(f_list, list) else []
    except Exception:
        o["artwork_files"] = []

    # 6. GPS Pin URL
    gps_m = re.search(r"GPS:\s*(https?://[^\s|]+)", cleaned_notes)
    o["gps_url"] = gps_m.group(1).strip() if gps_m else ""

    return o

# Main Dashboard View
@app.get("/", response_class=HTMLResponse)
async def dashboard_index(request: Request):
    if not is_authenticated(request):
        return RedirectResponse(url="/login", status_code=303)

    stats = database.get_stats()
    raw_orders = database.get_all_orders()
    orders = [enrich_order_data(o) for o in raw_orders]
    products_data = database.get_products_data()
    products = products_data.get("products", [])
    designs = database.get_designs()
    design_categories = database.get_design_categories()

    portfolio = database.get_portfolio_items()
    analytics = database.get_sales_analytics()
    admin_username, _ = database.get_admin_credentials()

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
            "analytics": analytics,
            "store_name": config.STORE_NAME,
            "admin_username": admin_username
        }
    )

# Protected API Routes
@app.get("/api/orders", dependencies=[Depends(require_api_auth)])
async def get_orders_api():
    """Returns latest orders and stats for live dashboard polling."""
    raw_orders = database.get_all_orders()
    return {
        "orders": [enrich_order_data(o) for o in raw_orders],
        "stats": database.get_stats()
    }

@app.get("/api/analytics", dependencies=[Depends(require_api_auth)])
async def get_analytics_api():
    """Returns sales analytics data for charts."""
    return database.get_sales_analytics()

@app.post("/api/settings/credentials", dependencies=[Depends(require_api_auth)])
async def update_credentials_api(payload: CredentialsUpdateRequest, response: Response):
    """Allows admin to update username and password from the dashboard."""
    admin_user, admin_pwd = database.get_admin_credentials()
    if payload.current_password != admin_pwd:
        raise HTTPException(status_code=400, detail="Current password is incorrect.")

    new_user = payload.new_username.strip()
    new_pass = payload.new_password.strip()

    if not new_user:
        raise HTTPException(status_code=400, detail="Username cannot be empty.")
    if len(new_pass) < 4:
        raise HTTPException(status_code=400, detail="New password must be at least 4 characters long.")

    database.update_admin_credentials(new_user, new_pass)

    # Set new secure auth session cookie
    response.set_cookie(
        key=AUTH_COOKIE_NAME,
        value=get_auth_token(),
        max_age=86400 * 30,
        httponly=True,
        samesite="lax"
    )
    return {
        "success": True,
        "message": "Username and password updated successfully!",
        "username": new_user
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
    """Add a new custom design/subproduct to database and save image."""
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

@app.get("/api/portfolio")
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
