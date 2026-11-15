import os
import json
import logging
import calendar
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any

from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    FSInputFile,
    InputMediaPhoto
)

from keyboards.reply_markup import (
    get_main_menu_keyboard,
    get_delivery_choice_keyboard,
    get_cancel_keyboard
)
from data import database
import config

logger = logging.getLogger(__name__)
router = Router(name="order_router")

RECEIPTS_DIR = Path(__file__).resolve().parent.parent / "data" / "receipts"
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)
DESIGNS_IMAGES_DIR = Path(__file__).resolve().parent.parent / "data" / "designs_images"
DESIGNS_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
CUSTOMER_UPLOADS_DIR = Path(__file__).resolve().parent.parent / "data" / "customer_uploads"
CUSTOMER_UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

class OrderFSM(StatesGroup):
    waiting_for_product = State()
    waiting_for_quantity = State()
    waiting_for_card_design = State()
    waiting_for_design_mode = State()
    waiting_for_photos = State()
    waiting_for_deadline = State()
    waiting_for_recipient_name = State()
    waiting_for_phone = State()
    waiting_for_payment_receipt = State()

class PostDeliveryFSM(StatesGroup):
    waiting_for_address = State()

# ─── Helpers ──────────────────────────────────────────────────
STEP_TOTAL = 5

def _step_header(step: int, title: str, icon: str = "📝") -> str:
    dots = "● " * step + "○ " * (STEP_TOTAL - step)
    return (
        f"╭─── {icon} New Order ───╮\n"
        f"│  Step {step} of {STEP_TOTAL} · {title}\n"
        f"╰─────────────────────╯\n"
        f"`{dots.strip()}`"
    )

# ─── KEYBOARDS ────────────────────────────────────────────────

def get_product_picker_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏷 Stickers  (min 15)", callback_data="sel_prod:stickers"),
            InlineKeyboardButton(text="🔖 Bookmarks  (min 2)", callback_data="sel_prod:bookmarks")
        ],
        [
            InlineKeyboardButton(text="💼 Business Cards  (min 50)", callback_data="sel_prod:business_cards"),
            InlineKeyboardButton(text="📸 Polaroids  (min 10)", callback_data="sel_prod:polaroid")
        ],
        [
            InlineKeyboardButton(text="📖 Photo Books & Minibooks ▾", callback_data="sel_cat:books")
        ],
        [
            InlineKeyboardButton(text="📓 Mini Notebook — 200 ETB", callback_data="sel_prod:mini_notebook"),
            InlineKeyboardButton(text="📔 Notebook — 500 ETB", callback_data="sel_prod:notebook")
        ],
        [
            InlineKeyboardButton(text="☕ Custom Mug — 1,500 ETB", callback_data="sel_prod:mug"),
            InlineKeyboardButton(text="🧩 Photo Puzzle — 1,500 ETB", callback_data="sel_prod:puzzle")
        ],
        [
            InlineKeyboardButton(text="▪ Poster A5  (min 10)", callback_data="sel_prod:sticker_poster_a5"),
            InlineKeyboardButton(text="▪ Poster A4  (min 10)", callback_data="sel_prod:sticker_poster_a4")
        ],
        [
            InlineKeyboardButton(
                text="🤝 Bulk Order (>100 pcs)",
                url=f"https://t.me/{config.ADMIN_USERNAME}?text=Hi%2C%20I%20am%20interested%20in%20a%20bulk%20order%20from%20Selora%20Prints"
            )
        ],
        [
            InlineKeyboardButton(text="✕ Cancel", callback_data="cancel_order")
        ]
    ])

def get_books_picker_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Mini White Cover — 600 ETB", callback_data="sel_prod:minibook_white")],
        [InlineKeyboardButton(text="📖 Mini Black Cover — 700 ETB", callback_data="sel_prod:minibook_black")],
        [InlineKeyboardButton(text="📖 Medium Photo Book — 800 ETB", callback_data="sel_prod:book_medium")],
        [InlineKeyboardButton(text="📖 A5 Photo Book — 1,000 ETB", callback_data="sel_prod:book_a5")],
        [InlineKeyboardButton(text="📖 A4 Luxury Photo Book — 1,500 ETB", callback_data="sel_prod:book_a4")],
        [InlineKeyboardButton(text="◀ Back to All Products", callback_data="sel_cat:all")]
    ])

def get_stepper_keyboard(prod_id: str, qty: int, min_order: int) -> InlineKeyboardMarkup:
    step_large = 10 if min_order >= 50 else (5 if min_order >= 10 else 2)
    step_small = 5 if min_order >= 50 else 1

    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=f"−{step_large}", callback_data=f"qstep:{prod_id}:-{step_large}"),
            InlineKeyboardButton(text=f"−{step_small}", callback_data=f"qstep:{prod_id}:-{step_small}"),
            InlineKeyboardButton(text=f"[ {qty} ]", callback_data="noop"),
            InlineKeyboardButton(text=f"+{step_small}", callback_data=f"qstep:{prod_id}:+{step_small}"),
            InlineKeyboardButton(text=f"+{step_large}", callback_data=f"qstep:{prod_id}:+{step_large}")
        ],
        [
            InlineKeyboardButton(text=f"✓ Confirm {qty} pcs", callback_data=f"qconfirm:{prod_id}:{qty}")
        ],
        [
            InlineKeyboardButton(
                text="🤝 Bulk (>100 pcs)?",
                url=f"https://t.me/{config.ADMIN_USERNAME}?text=Hi%2C%20I%20am%20interested%20in%20a%20bulk%20order%20for%20{prod_id}%20with%20custom%20pricing"
            )
        ],
        [
            InlineKeyboardButton(text="◀ Change Item", callback_data="sel_cat:all"),
            InlineKeyboardButton(text="✕ Cancel", callback_data="cancel_order")
        ]
    ])

def get_card_design_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📁 I have a ready design  (Free)", callback_data="card_design:ready")],
        [InlineKeyboardButton(text="🎨 Selora Custom Design  (+100 ETB)", callback_data="card_design:selora")],
        [InlineKeyboardButton(text="✕ Cancel Order", callback_data="cancel_order")]
    ])

def get_design_mode_keyboard(qty: int, prod_name: str) -> InlineKeyboardMarkup:
    buttons = []
    if qty > 1:
        buttons.append([InlineKeyboardButton(text=f"🖼 1 design for all {qty} copies", callback_data="dmode:single")])
        buttons.append([InlineKeyboardButton(text=f"📸 Different photo per item ({qty} photos)", callback_data="dmode:multi")])
    else:
        buttons.append([InlineKeyboardButton(text="📸 Upload My Photo / Artwork", callback_data="dmode:single")])

    buttons.append([InlineKeyboardButton(text="🎨 Browse Selora Ready Designs", callback_data="dmode:templates")])
    buttons.append([InlineKeyboardButton(text="✕ Cancel Order", callback_data="cancel_order")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_template_gallery_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✨ Minimalist", callback_data="tmpl:Minimalist Aesthetic"),
            InlineKeyboardButton(text="🎞 Retro Film", callback_data="tmpl:Retro Vintage Film")
        ],
        [
            InlineKeyboardButton(text="🌿 Floral", callback_data="tmpl:Floral & Nature"),
            InlineKeyboardButton(text="💬 Quotes", callback_data="tmpl:Typographic Quotes")
        ],
        [
            InlineKeyboardButton(text="🔤 Monogram", callback_data="tmpl:Custom Monogram")
        ],
        [
            InlineKeyboardButton(text="◀ Back to Photo Upload", callback_data="dmode:back")
        ]
    ])

# ─── INLINE CALENDAR DATE PICKER ─────────────────────────────

def build_calendar_keyboard(year: int, month: int) -> InlineKeyboardMarkup:
    """Build a month-view inline calendar grid."""
    today = date.today()
    tomorrow = today + timedelta(days=1)
    rush_day = today + timedelta(days=2)
    max_date = today + timedelta(days=60)  # ~2 months

    month_name = calendar.month_name[month]
    rows: list[list[InlineKeyboardButton]] = []

    # ── Header row: ◀ Month Year ▶
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    # Only allow navigation within valid range
    can_prev = date(prev_year, prev_month, 1) >= date(today.year, today.month, 1)
    can_next = date(next_year, next_month, 1) <= date(max_date.year, max_date.month, 1)

    nav_prev = InlineKeyboardButton(
        text="◀" if can_prev else " ",
        callback_data=f"cal_nav:{prev_year}-{prev_month:02d}" if can_prev else "noop"
    )
    nav_next = InlineKeyboardButton(
        text="▶" if can_next else " ",
        callback_data=f"cal_nav:{next_year}-{next_month:02d}" if can_next else "noop"
    )
    rows.append([nav_prev, InlineKeyboardButton(text=f"{month_name} {year}", callback_data="noop"), nav_next])

    # ── Day-of-week headers
    rows.append([InlineKeyboardButton(text=d, callback_data="noop") for d in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]])

    # ── Day grid
    cal = calendar.monthcalendar(year, month)
    for week in cal:
        row = []
        for day_num in week:
            if day_num == 0:
                row.append(InlineKeyboardButton(text=" ", callback_data="noop"))
                continue

            d = date(year, month, day_num)

            if d <= today:
                # Past or today — show dot
                row.append(InlineKeyboardButton(text="·", callback_data="noop"))
            elif d == tomorrow:
                # Tomorrow blocked
                row.append(InlineKeyboardButton(text="✖", callback_data="noop"))
            elif d > max_date:
                # Beyond 2 months
                row.append(InlineKeyboardButton(text="·", callback_data="noop"))
            elif d == rush_day:
                # Rush day (+200 ETB)
                iso = d.isoformat()
                row.append(InlineKeyboardButton(text=f"⚡{day_num}", callback_data=f"cal_day:{iso}:200"))
            else:
                # Normal selectable day
                iso = d.isoformat()
                row.append(InlineKeyboardButton(text=str(day_num), callback_data=f"cal_day:{iso}:0"))
        rows.append(row)

    # ── Cancel row
    rows.append([InlineKeyboardButton(text="✕ Cancel Order", callback_data="cancel_order")])

    return InlineKeyboardMarkup(inline_keyboard=rows)


def get_recipient_name_keyboard(tg_name: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✓ Use My Name: {tg_name}", callback_data="recip_name:tg")],
        [InlineKeyboardButton(text="✏ Different Recipient", callback_data="recip_name:custom")],
        [InlineKeyboardButton(text="✕ Cancel Order", callback_data="cancel_order")]
    ])

def get_phone_request_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Share Phone Number (1-Tap)", request_contact=True)],
            [KeyboardButton(text="❌ Cancel")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_location_dispatch_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Send Exact GPS Pin (Best for Ride/Yango)", request_location=True)],
            [KeyboardButton(text="🏙️ Choose Addis Ababa Sub-City / Area")],
            [KeyboardButton(text="✏️ Type Landmark / Street Name")],
            [KeyboardButton(text="❌ Cancel")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_subcities_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Bole / Medhanialem", callback_data="subcity:Bole / Medhanialem"),
            InlineKeyboardButton(text="Kazanchis / Bambis", callback_data="subcity:Kazanchis / Bambis")
        ],
        [
            InlineKeyboardButton(text="CMC / Ayat / Summit", callback_data="subcity:CMC / Ayat / Summit"),
            InlineKeyboardButton(text="Piassa / Arat Kilo", callback_data="subcity:Piassa / Arat Kilo")
        ],
        [
            InlineKeyboardButton(text="Sarbet / Bisrate Gabriel", callback_data="subcity:Sarbet / Bisrate Gabriel"),
            InlineKeyboardButton(text="Megenagna / 22", callback_data="subcity:Megenagna / 22")
        ],
        [
            InlineKeyboardButton(text="Gerji / Imperial", callback_data="subcity:Gerji / Imperial"),
            InlineKeyboardButton(text="Lebu / Jemo", callback_data="subcity:Lebu / Jemo")
        ],
        [
            InlineKeyboardButton(text="Mexico / Ledeta", callback_data="subcity:Mexico / Ledeta"),
            InlineKeyboardButton(text="4 Kilo / 6 Kilo", callback_data="subcity:4 Kilo / 6 Kilo")
        ],
        [
            InlineKeyboardButton(text="Gotera / Saris", callback_data="subcity:Gotera / Saris"),
            InlineKeyboardButton(text="Kera / Bulgaria", callback_data="subcity:Kera / Bulgaria")
        ],
        [
            InlineKeyboardButton(text="◀ Back to Location Options", callback_data="subcity:back")
        ]
    ])

# ─── START ORDER & PRODUCT PICKER ────────────────────────────

@router.message(Command("cancel"))
@router.message(F.text.in_(["❌ Cancel", "❌ Cancel Order"]))
async def cancel_order(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "✕ Order cancelled. You can start anytime from the menu.",
        reply_markup=get_main_menu_keyboard()
    )

@router.callback_query(F.data == "cancel_order")
async def callback_cancel_order(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("✕ Order cancelled.")
    await callback.message.answer(
        "_Feel free to browse or ask questions anytime._",
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()

@router.message(Command("order"))
@router.message(F.text == "📝 Place an Order")
async def start_order(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(OrderFSM.waiting_for_product)
    await message.answer(
        _step_header(1, "Product", "📝") + "\n"
        "─────────────────────\n"
        "Select the item you'd like to order:",
        parse_mode="Markdown",
        reply_markup=get_product_picker_keyboard()
    )

@router.callback_query(F.data == "start_order")
async def callback_start_order(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(OrderFSM.waiting_for_product)
    await callback.message.answer(
        _step_header(1, "Product", "📝") + "\n"
        "─────────────────────\n"
        "Select the item you'd like to order:",
        parse_mode="Markdown",
        reply_markup=get_product_picker_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "sel_cat:books")
async def callback_show_books_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "╭─── 📖 Photo Books ───╮\n"
        "│  Choose your preferred\n"
        "│  cover and size:\n"
        "╰─────────────────────╯",
        parse_mode="Markdown",
        reply_markup=get_books_picker_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "sel_cat:all")
async def callback_show_all_prods(callback: types.CallbackQuery):
    await callback.message.edit_text(
        _step_header(1, "Product", "📝") + "\n"
        "─────────────────────\n"
        "Select the item you'd like to order:",
        parse_mode="Markdown",
        reply_markup=get_product_picker_keyboard()
    )
    await callback.answer()

# ─── QUANTITY STEPPER ─────────────────────────────────────────

async def show_quantity_stepper(message: types.Message, prod_id: str, state: FSMContext, initial_qty: Optional[int] = None):
    products = database.get_products_data().get("products", [])
    prod = next((p for p in products if p["id"] == prod_id), None)
    if not prod:
        await message.answer("Product not found. Please choose from catalog.", reply_markup=get_product_picker_keyboard())
        return

    min_ord = prod.get("min_order", 1)
    qty = initial_qty if initial_qty is not None else min_ord
    price = prod.get("price") or 0
    subtotal = price * qty if price else 0

    await state.update_data(
        product_id=prod["id"],
        product_name=prod["name"],
        unit_price=price,
        min_order=min_ord,
        quantity=qty
    )
    await state.set_state(OrderFSM.waiting_for_quantity)

    price_info = f"{price} ETB each" if price else "Custom Quote"
    min_note = f"\n▸ *Min Order:* {min_ord} pcs" if min_ord > 1 else ""
    sub_line = f"\n▸ *Subtotal:* {subtotal} ETB" if price else ""

    text = (
        _step_header(2, "Quantity", "🔢") + "\n"
        "─────────────────────\n"
        f"*{prod['name']}*\n\n"
        f"▸ *Unit Price:* {price_info}{min_note}\n"
        f"▸ *Quantity:* {qty} pcs{sub_line}\n"
        "─────────────────────\n"
        "Use the buttons to adjust:"
    )

    keyboard = get_stepper_keyboard(prod_id, qty, min_ord)
    await message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)

@router.callback_query(F.data.startswith("sel_prod:"))
async def callback_select_product(callback: types.CallbackQuery, state: FSMContext):
    prod_id = callback.data.split(":")[1]
    await show_quantity_stepper(callback.message, prod_id, state)
    await callback.answer()

@router.callback_query(OrderFSM.waiting_for_quantity, F.data.startswith("qstep:"))
async def callback_quantity_step(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    prod_id = parts[1]
    delta = int(parts[2])

    data = await state.get_data()
    current_qty = data.get("quantity", 1)
    min_ord = data.get("min_order", 1)
    price = data.get("unit_price", 0)

    new_qty = current_qty + delta
    if new_qty < min_ord:
        await callback.answer(f"⚠ Minimum order is {min_ord} pieces!", show_alert=True)
        return

    await state.update_data(quantity=new_qty)
    subtotal = price * new_qty if price else 0

    price_info = f"{price} ETB each" if price else "Custom Quote"
    min_note = f"\n▸ *Min Order:* {min_ord} pcs" if min_ord > 1 else ""
    sub_line = f"\n▸ *Subtotal:* {subtotal} ETB" if price else ""

    text = (
        _step_header(2, "Quantity", "🔢") + "\n"
        "─────────────────────\n"
        f"*{data.get('product_name', prod_id)}*\n\n"
        f"▸ *Unit Price:* {price_info}{min_note}\n"
        f"▸ *Quantity:* {new_qty} pcs{sub_line}\n"
        "─────────────────────\n"
        "Use the buttons to adjust:"
    )

    keyboard = get_stepper_keyboard(prod_id, new_qty, min_ord)
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    except Exception:
        pass
    await callback.answer()

# ─── CONFIRM QUANTITY -> CARD DESIGN / DESIGN MODE ────────────

@router.callback_query(OrderFSM.waiting_for_quantity, F.data.startswith("qconfirm:"))
async def callback_quantity_confirm(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    prod_id = parts[1]
    qty = int(parts[2])

    data = await state.get_data()
    prod_name = data.get("product_name", prod_id)
    unit_price = data.get("unit_price", 0)
    subtotal = unit_price * qty

    await state.update_data(
        quantity=qty,
        items=f"{qty}x {prod_name}",
        subtotal=subtotal
    )

    # Special flow for Business Cards (+100 ETB design fee)
    if prod_id == "business_cards":
        await state.set_state(OrderFSM.waiting_for_card_design)
        await callback.message.edit_text(
            "╭─── 💼 Business Card Design ───╮\n"
            "│\n"
            f"│  Ordering: *{qty} Business Cards*\n"
            "│\n"
            "│  ▸ My own ready design — Free\n"
            "│  ▸ Selora custom design — +100 ETB\n"
            "│\n"
            "╰──────────────────────────────╯",
            parse_mode="Markdown",
            reply_markup=get_card_design_keyboard()
        )
        await callback.answer()
        return

    # Normal products -> Design mode selection
    await advance_to_design_mode(callback.message, state)
    await callback.answer()

# ─── BUSINESS CARD DESIGN HANDLER ────────────────────────────

@router.callback_query(OrderFSM.waiting_for_card_design, F.data.startswith("card_design:"))
async def callback_card_design(callback: types.CallbackQuery, state: FSMContext):
    choice = callback.data.split(":")[1]
    if choice == "selora":
        design_fee = 100
        design_note = "Selora Custom Design Service (+100 ETB)"
        await callback.message.answer("✓ *Selora Custom Design Service (+100 ETB)*", parse_mode="Markdown")
    else:
        design_fee = 0
        design_note = "Customer Ready Design File"
        await callback.message.answer("✓ *Customer Ready Design File (Free)*", parse_mode="Markdown")

    await state.update_data(design_fee=design_fee, design_note=design_note)
    await advance_to_design_mode(callback.message, state)
    await callback.answer()

# ─── DESIGN & ARTWORK SELECTION MODE ─────────────────────────

def get_order_design_card(index: int, product_id: str, qty: int):
    designs = database.get_designs(product_id=product_id)
    if not designs:
        designs = database.get_designs()
    if not designs:
        return None, None, None

    idx = index % len(designs)
    d = designs[idx]

    caption = (
        f"*{d['title']}*\n"
        "─────────────────────\n"
        f"▸ *Product:* {d['product_name']}\n"
        f"▸ *Style:* {d['subproduct']}\n"
        f"▸ {d.get('description', '')}\n"
        "─────────────────────\n"
        f"_Design {idx + 1} of {len(designs)}_\n\n"
        f"Tap *'✓ Use This Design'* to apply to your {qty} copies."
    )

    prev_idx = (idx - 1) % len(designs)
    next_idx = (idx + 1) % len(designs)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="◀ Prev", callback_data=f"odes_nav:{idx}:{prev_idx}"),
            InlineKeyboardButton(text=f"· {idx + 1}/{len(designs)} ·", callback_data="noop"),
            InlineKeyboardButton(text="Next ▶", callback_data=f"odes_nav:{idx}:{next_idx}")
        ],
        [
            InlineKeyboardButton(text="✓ Use This Design", callback_data=f"odes_pick:{d['id']}")
        ],
        [
            InlineKeyboardButton(text="📸 Upload My Own Instead", callback_data="odes_custom")
        ],
        [
            InlineKeyboardButton(text="◀ Back", callback_data="dmode:back"),
            InlineKeyboardButton(text="✕ Cancel", callback_data="cancel_order")
        ]
    ])

    image_path = None
    cand = DESIGNS_IMAGES_DIR / f"{d['id']}.png"
    if cand.exists():
        image_path = cand
    else:
        custom_url = d.get("image_url", "").split("?")[0]
        if custom_url.startswith("/designs-images/"):
            fname = custom_url.replace("/designs-images/", "")
            cand = DESIGNS_IMAGES_DIR / fname
            if cand.exists():
                image_path = cand

    if not image_path or not image_path.exists():
        image_path = Path(__file__).resolve().parent.parent / "data" / "products_images" / "stickers.png"

    return caption, FSInputFile(image_path), keyboard

async def advance_to_design_mode(message: types.Message, state: FSMContext):
    data = await state.get_data()
    qty = data.get("quantity", 1)
    prod_name = data.get("product_name", "Items")

    # If user already selected a ready design prior to stepper
    if data.get("selected_design_id") and data.get("design_note"):
        if isinstance(message, types.CallbackQuery):
            await message.message.answer(f"✓ Using Design: *{data.get('design_note')}*", parse_mode="Markdown")
        else:
            await message.answer(f"✓ Using Design: *{data.get('design_note')}*", parse_mode="Markdown")
        await advance_to_deadline_picker(message, state)
        return

    await state.set_state(OrderFSM.waiting_for_design_mode)
    text = (
        _step_header(3, "Design", "🎨") + "\n"
        "─────────────────────\n"
        f"Item: *{qty}x {prod_name}*\n\n"
        "How would you like to provide the design?\n\n"
        "▸ *Upload Photo:* Send your own custom artwork\n"
        "▸ *Ready Designs:* Browse curated templates"
    )
    if isinstance(message, types.CallbackQuery):
        await message.message.edit_text(text, parse_mode="Markdown", reply_markup=get_design_mode_keyboard(qty, prod_name))
    else:
        await message.edit_text(text, parse_mode="Markdown", reply_markup=get_design_mode_keyboard(qty, prod_name))

@router.callback_query(OrderFSM.waiting_for_design_mode, F.data.startswith("dmode:"))
async def callback_design_mode(callback: types.CallbackQuery, state: FSMContext):
    mode = callback.data.split(":")[1]
    data = await state.get_data()
    qty = data.get("quantity", 1)
    prod_name = data.get("product_name", "items")
    prod_id = data.get("product_id", "stickers")

    if mode == "templates":
        caption, img, markup = get_order_design_card(0, prod_id, qty)
        if caption and img:
            try:
                await callback.message.delete()
            except Exception:
                pass
            await callback.message.answer_photo(
                photo=img,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=markup
            )
        else:
            await callback.message.edit_text(
                "⚠ *No pre-made designs found for this item.*\n\n"
                "Please upload your own photo or artwork below:",
                parse_mode="Markdown"
            )
            await state.update_data(design_mode="single", photos=[])
            await state.set_state(OrderFSM.waiting_for_photos)
        await callback.answer()
        return

    if mode == "back":
        await advance_to_design_mode(callback.message, state)
        await callback.answer()
        return

    if mode == "single":
        await state.update_data(design_mode="single", photos=[], customer_files=[])
        await state.set_state(OrderFSM.waiting_for_photos)

        inline_cancel = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✕ Cancel Order", callback_data="cancel_order")]
        ])

        await callback.message.edit_text(
            _step_header(3, "Upload Artwork", "📸") + "\n"
            "─────────────────────\n"
            f"This design will print on all *{qty}* copies of {prod_name}.\n\n"
            "▸ For best quality: tap 📎 and send as *File/Document*\n"
            "▸ Regular high-res photos are also accepted\n"
            "─────────────────────\n"
            "Send your photo or artwork now:",
            parse_mode="Markdown",
            reply_markup=inline_cancel
        )
        await callback.answer()
        return

    if mode == "multi":
        await state.update_data(design_mode="multi", photos=[], customer_files=[])
        await state.set_state(OrderFSM.waiting_for_photos)

        done_btn = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✓ Done Uploading", callback_data="done_photos")],
            [InlineKeyboardButton(text="✕ Cancel Order", callback_data="cancel_order")]
        ])

        await callback.message.edit_text(
            _step_header(3, "Upload Photos", "📸") + "\n"
            "─────────────────────\n"
            f"Send {qty} photos, one by one or as an album.\n\n"
            "▸ For best quality: send as *Files/Documents* (📎)\n"
            "▸ Regular photos also accepted\n\n"
            f"Progress: `0 / {qty}` photos received\n"
            "─────────────────────\n"
            "Send your photos now:",
            parse_mode="Markdown",
            reply_markup=done_btn
        )
        await callback.answer()

@router.callback_query(OrderFSM.waiting_for_design_mode, F.data.startswith("odes_nav:"))
async def callback_order_design_nav(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    prod_id = data.get("product_id", "stickers")
    qty = data.get("quantity", 1)
    parts = callback.data.split(":")
    next_idx = int(parts[2])
    caption, img, markup = get_order_design_card(next_idx, prod_id, qty)
    if caption and img:
        try:
            await callback.message.edit_media(
                media=InputMediaPhoto(media=img, caption=caption, parse_mode="Markdown"),
                reply_markup=markup
            )
        except Exception as e:
            logger.warning(f"Could not edit order design media: {e}")
    await callback.answer()

@router.callback_query(OrderFSM.waiting_for_design_mode, F.data.startswith("odes_pick:"))
async def callback_order_design_pick(callback: types.CallbackQuery, state: FSMContext):
    design_id = callback.data.split(":", 1)[1]
    d = database.get_design_by_id(design_id)
    title = d['title'] if d else "Selected Design"
    subproduct = d.get('subproduct', '') if d else ""
    design_note = f"Ready Design: {title} ({subproduct})"

    await state.update_data(
        design_mode="template",
        design_note=design_note,
        selected_design_id=design_id,
        file_id=None
    )
    await callback.message.answer(f"✓ Selected Design: *{title}* ({subproduct})", parse_mode="Markdown")
    await advance_to_deadline_picker(callback.message, state)
    await callback.answer()

@router.callback_query(OrderFSM.waiting_for_design_mode, F.data == "odes_custom")
async def callback_order_design_custom(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    qty = data.get("quantity", 1)
    prod_name = data.get("product_name", "items")
    await state.update_data(design_mode="single", photos=[])
    await state.set_state(OrderFSM.waiting_for_photos)
    try:
        await callback.message.delete()
    except Exception:
        pass

    inline_cancel = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✕ Cancel Order", callback_data="cancel_order")]
    ])

    await callback.message.answer(
        _step_header(3, "Custom Artwork", "📸") + "\n"
        "─────────────────────\n"
        f"Send your custom artwork or photo for *{qty}* copies of {prod_name}:",
        parse_mode="Markdown",
        reply_markup=inline_cancel
    )
    await callback.answer()

# ─── PHOTO UPLOADER ───────────────────────────────────────────

@router.message(OrderFSM.waiting_for_photos, F.text)
async def handle_text_during_photo_upload(message: types.Message, state: FSMContext):
    if message.text in ["❌ Cancel", "❌ Cancel Order"]:
        await cancel_order(message, state)
        return
    await message.answer(
        "📸 _Please send a photo or document file — not text._\n"
        "_Tap 📎 to attach your artwork, or type /cancel to quit._",
        parse_mode="Markdown"
    )

@router.message(OrderFSM.waiting_for_photos, F.photo | F.document)
async def process_photo_upload(message: types.Message, state: FSMContext):
    data = await state.get_data()
    mode = data.get("design_mode", "single")
    qty = data.get("quantity", 1)
    user = message.from_user

    customer_files = data.get("customer_files", [])
    file_idx = len(customer_files) + 1

    if message.document:
        file_id = message.document.file_id
        orig_name = message.document.file_name or f"document_{file_idx}.jpg"
        ext = Path(orig_name).suffix.lower() or ".jpg"
        filename = f"art_{user.id}_{int(datetime.now().timestamp())}_{file_idx}{ext}"
        file_type = "Document (Uncompressed)"
    else:
        best_photo = message.photo[-1]
        file_id = best_photo.file_id
        orig_name = f"photo_{best_photo.width}x{best_photo.height}.jpg"
        filename = f"art_{user.id}_{int(datetime.now().timestamp())}_{file_idx}.jpg"
        file_type = f"Photo ({best_photo.width}x{best_photo.height})"

    dest_path = CUSTOMER_UPLOADS_DIR / filename
    try:
        await message.bot.download(file_id, destination=dest_path)
    except Exception as err:
        logger.warning(f"Could not download artwork locally: {err}")

    file_entry = {
        "file_id": file_id,
        "filename": filename,
        "original_name": orig_name,
        "file_type": file_type,
        "url": f"/customer-uploads/{filename}"
    }
    customer_files.append(file_entry)

    if mode == "single":
        await state.update_data(
            file_id=file_id,
            file_type="document" if message.document else "photo",
            customer_files=customer_files
        )
        await message.answer(f"✓ *Artwork received!* ({file_type})", parse_mode="Markdown")
        await advance_to_deadline_picker(message, state)
        return

    # Multi photo mode
    photos = data.get("photos", [])
    photos.append(file_id)
    await state.update_data(photos=photos, file_id=photos[0], customer_files=customer_files)

    count = len(photos)
    if count >= qty:
        await message.answer(f"✓ *All {count}/{qty} photos received!*", parse_mode="Markdown")
        await advance_to_deadline_picker(message, state)
    else:
        done_btn = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"✓ Done Uploading ({count}/{qty})", callback_data="done_photos")],
            [InlineKeyboardButton(text="✕ Cancel Order", callback_data="cancel_order")]
        ])
        await message.answer(
            f"📸 *Photo {count} of {qty} received*\n\n"
            f"Send more photos or tap *Done Uploading*:",
            parse_mode="Markdown",
            reply_markup=done_btn
        )

@router.callback_query(OrderFSM.waiting_for_photos, F.data == "done_photos")
async def callback_done_photos(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    photos = data.get("photos", [])
    if not photos:
        await callback.answer("Please send at least 1 photo first!", show_alert=True)
        return

    await callback.message.answer(f"✓ *{len(photos)} photos uploaded*", parse_mode="Markdown")
    await advance_to_deadline_picker(callback.message, state)
    await callback.answer()

# ─── INTERACTIVE CALENDAR DATE PICKER ─────────────────────────

async def advance_to_deadline_picker(message: types.Message, state: FSMContext):
    await state.set_state(OrderFSM.waiting_for_deadline)
    today = date.today()
    cal_kb = build_calendar_keyboard(today.year, today.month)

    text = (
        _step_header(4, "Completion Date", "🗓") + "\n"
        "─────────────────────\n"
        "▸ Standard: 3+ days (normal pricing)\n"
        "▸ ⚡ Urgent Rush (2 days): +200 ETB\n"
        "▸ ✖ Tomorrow: unavailable (drying time)\n"
        "─────────────────────\n"
        "Tap a date on the calendar below:"
    )
    if isinstance(message, types.CallbackQuery):
        await message.message.edit_text(text, parse_mode="Markdown", reply_markup=cal_kb)
    else:
        await message.answer(text, parse_mode="Markdown", reply_markup=cal_kb)

@router.callback_query(OrderFSM.waiting_for_deadline, F.data.startswith("cal_nav:"))
async def callback_cal_nav(callback: types.CallbackQuery, state: FSMContext):
    """Navigate to a different month in the calendar."""
    ym = callback.data.split(":")[1]  # YYYY-MM
    year, month = int(ym.split("-")[0]), int(ym.split("-")[1])
    cal_kb = build_calendar_keyboard(year, month)

    text = (
        _step_header(4, "Completion Date", "🗓") + "\n"
        "─────────────────────\n"
        "▸ Standard: 3+ days (normal pricing)\n"
        "▸ ⚡ Urgent Rush (2 days): +200 ETB\n"
        "▸ ✖ Tomorrow: unavailable (drying time)\n"
        "─────────────────────\n"
        "Tap a date on the calendar below:"
    )
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=cal_kb)
    except Exception:
        pass
    await callback.answer()

@router.callback_query(OrderFSM.waiting_for_deadline, F.data.startswith("cal_day:"))
async def callback_cal_day(callback: types.CallbackQuery, state: FSMContext):
    """User selected a day from the calendar."""
    parts = callback.data.split(":")
    iso_date = parts[1]   # YYYY-MM-DD
    rush_fee = int(parts[2])

    selected = datetime.strptime(iso_date, "%Y-%m-%d")
    date_label = selected.strftime("%a, %b %d")

    await state.update_data(deadline=date_label, rush_fee=rush_fee)
    await state.set_state(OrderFSM.waiting_for_recipient_name)

    if rush_fee > 0:
        confirm_text = f"✓ Completion Date: *{date_label}* _(⚡ Urgent Rush +200 ETB)_"
    else:
        confirm_text = f"✓ Completion Date: *{date_label}* _(Standard)_"

    await callback.message.edit_text(confirm_text, parse_mode="Markdown")

    user = callback.from_user
    await callback.message.answer(
        _step_header(5, "Contact Information", "👤") + "\n"
        "─────────────────────\n"
        "Who is this order for?\n\n"
        "👉 *Tap below to confirm recipient name:*",
        parse_mode="Markdown",
        reply_markup=get_recipient_name_keyboard(user.full_name)
    )
    await callback.answer()

# ─── CONTACT INFORMATION INTAKE (PRE-PAYMENT) ─────────────────

@router.callback_query(OrderFSM.waiting_for_recipient_name, F.data.startswith("recip_name:"))
async def callback_recipient_name(callback: types.CallbackQuery, state: FSMContext):
    mode = callback.data.split(":")[1]
    user = callback.from_user
    if mode == "tg":
        await state.update_data(recipient_name=user.full_name)
        await callback.message.edit_text(f"✓ Recipient: *{user.full_name}*", parse_mode="Markdown")
        await state.set_state(OrderFSM.waiting_for_phone)
        await callback.message.answer(
            "╭─── 📱 Contact Phone ───╮\n"
            "│  Order & Driver Contact\n"
            "╰─────────────────────────╯\n\n"
            "Please provide a phone number for order updates and driver coordination:\n\n"
            "Tap *'📱 Share Phone Number'* or type your 10-digit number (e.g. `0911223344`):",
            parse_mode="Markdown",
            reply_markup=get_phone_request_keyboard()
        )
    else:
        await callback.message.edit_text(
            "✏ *Type the full name of the recipient:*\n\n_e.g., Kebron Girma_",
            parse_mode="Markdown"
        )
    await callback.answer()

@router.message(OrderFSM.waiting_for_recipient_name, F.text)
async def process_custom_recipient_name(message: types.Message, state: FSMContext):
    if message.text in ["❌ Cancel", "❌ Cancel Order"]:
        await cancel_order(message, state)
        return
    name = message.text.strip()
    await state.update_data(recipient_name=name)
    await message.answer(f"✓ Recipient: *{name}*", parse_mode="Markdown")
    await state.set_state(OrderFSM.waiting_for_phone)
    await message.answer(
        "╭─── 📱 Contact Phone ───╮\n"
        "│  Order & Driver Contact\n"
        "╰─────────────────────────╯\n\n"
        "Please provide a phone number for order updates and driver coordination:\n\n"
        "Tap *'📱 Share Phone Number'* or type your 10-digit number (e.g. `0911223344`):",
        parse_mode="Markdown",
        reply_markup=get_phone_request_keyboard()
    )

@router.message(OrderFSM.waiting_for_phone, F.contact)
async def process_phone_contact(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number
    if not phone.startswith("+") and len(phone) == 10 and phone.startswith("0"):
        phone = f"+251{phone[1:]}"
    await state.update_data(
        phone=phone,
        delivery_type="Pending Dispatch (Coordinated when Ready)",
        delivery_location="To be selected upon order completion"
    )
    await message.answer(
        f"✓ Contact Phone: *{phone}*\n\n"
        "📦 *Delivery Coordination Notice:*\n"
        "_To ensure fast & accurate dispatch, your delivery method (Free Store Pickup vs. Yango/Feres Taxi Delivery) will be chosen once your items are printed and ready for pickup/delivery!_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    await show_payment_summary(message, state)

@router.message(OrderFSM.waiting_for_phone, F.text)
async def process_phone_text(message: types.Message, state: FSMContext):
    if message.text in ["❌ Cancel", "❌ Cancel Order"]:
        await cancel_order(message, state)
        return
    phone = message.text.strip()
    await state.update_data(
        phone=phone,
        delivery_type="Pending Dispatch (Coordinated when Ready)",
        delivery_location="To be selected upon order completion"
    )
    await message.answer(
        f"✓ Contact Phone: *{phone}*\n\n"
        "📦 *Delivery Coordination Notice:*\n"
        "_To ensure fast & accurate dispatch, your delivery method (Free Store Pickup vs. Yango/Feres Taxi Delivery) will be chosen once your items are printed and ready for pickup/delivery!_",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    await show_payment_summary(message, state)

# ─── PAYMENT SUMMARY & VERIFICATION ──────────────────────────

async def show_payment_summary(message: types.Message, state: FSMContext):
    data = await state.get_data()
    subtotal = data.get("subtotal", 0)
    design_fee = data.get("design_fee", 0)
    rush_fee = data.get("rush_fee", 0)

    total = subtotal + design_fee + rush_fee
    deposit = round(total * 0.5) if total > 0 else 0
    remaining = total - deposit

    await state.update_data(total_price=total, deposit_amount=deposit)
    await state.set_state(OrderFSM.waiting_for_payment_receipt)

    fee_lines = ""
    if design_fee > 0:
        fee_lines += f"│  ▸ Custom Design: +{design_fee} ETB\n"
    if rush_fee > 0:
        fee_lines += f"│  ▸ ⚡ Rush Fee: +{rush_fee} ETB\n"

    recip_str = data.get('recipient_name', 'Customer')
    phone_str = data.get('phone', 'N/A')

    payment_prompt = (
        "╭─── 💳 Order Summary ───╮\n"
        "│\n"
        f"│  *{data.get('items')}*\n"
        f"│  Design: {data.get('design_note', 'Custom artwork')}\n"
        f"│  Needed by: {data.get('deadline')}\n"
        "│\n"
        f"│  Recipient: {recip_str}\n"
        f"│  Contact Phone: {phone_str}\n"
        "│  Delivery: Coordinated when ready\n"
        "│\n"
        "╰─────────────────────────╯\n\n"
        "─── Cost Breakdown ───\n\n"
        f"▸ Items Subtotal: {subtotal} ETB\n"
        f"{fee_lines}"
        f"▸ *Total Order Price:* {total} ETB\n\n"
        f"✦ *50% Advance Deposit Due:* *{deposit} ETB*\n"
        f"_Remaining {remaining} ETB paid upon pickup or delivery_\n\n"
        "ℹ️ *Delivery Fee Policy:*\n"
        "• 🏪 *Store Pickup (Ledeta):* 100% Free\n"
        "• 🚚 *Doorstep Taxi Delivery:* Driver fare depends on transportation distance and taxi rate (~300 – 1,000 ETB all-inclusive via Yango/Feres/RIDE), paid directly to the driver upon delivery. If you prefer to avoid the delivery fee, you are warmly welcome to visit our Ledeta office for free pickup!\n\n"
        "─── Payment Accounts ───\n\n"
        f"🏦 *CBE (Commercial Bank of Ethiopia):*\n"
        f"`{config.PAYMENT_CBE_ACCOUNT}`\n"
        f"Account Name: *{config.PAYMENT_CBE_NAME}*\n\n"
        f"📱 *Telebirr:*\n"
        f"`{config.PAYMENT_TELEBIRR}`\n"
        f"Account Name: *{config.PAYMENT_TELEBIRR_NAME}*\n\n"
        "─────────────────────\n"
        "Transfer the 50% deposit, then upload your screenshot below:"
    )

    await message.answer(payment_prompt, parse_mode="Markdown", reply_markup=get_cancel_keyboard())

# ─── PAYMENT RECEIPT HANDLER & OWNER NOTIFICATION ─────────────

@router.message(OrderFSM.waiting_for_payment_receipt)
async def process_payment_receipt(message: types.Message, state: FSMContext):
    if message.text in ["❌ Cancel", "❌ Cancel Order"]:
        await cancel_order(message, state)
        return

    screenshot_file_id = None
    if message.photo:
        screenshot_file_id = message.photo[-1].file_id
    elif message.document and message.document.mime_type and message.document.mime_type.startswith("image/"):
        screenshot_file_id = message.document.file_id
    elif message.text:
        await message.answer(
            "📸 _Please upload a photo or screenshot of your payment receipt._\n"
            "_Tap /cancel if you need to stop._",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        return

    data = await state.get_data()
    user = message.from_user
    username_str = f"@{user.username}" if user.username else "No username"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    temp_filename = f"receipt_{user.id}_{int(datetime.now().timestamp())}.jpg"
    receipt_local_path = RECEIPTS_DIR / temp_filename

    try:
        await message.bot.download(screenshot_file_id, destination=receipt_local_path)
    except Exception as e:
        logger.warning(f"Could not download receipt locally: {e}")

    # Save to database
    notes_combined = f"{data.get('design_note', '')} | Deposit: {data.get('deposit_amount', 0)} ETB (Total: {data.get('total_price', 0)} ETB)"
    if data.get('delivery_maps_url'):
        notes_combined += f" | GPS: {data.get('delivery_maps_url')}"

    order_code = database.save_order(
        user_id=user.id,
        full_name=user.full_name,
        username=user.username,
        items=data.get('items', ''),
        deadline=data.get('deadline', ''),
        delivery_type=data.get('delivery_type', ''),
        delivery_location=data.get('delivery_location', ''),
        notes=notes_combined,
        has_attachment=bool(data.get('file_id') or data.get('customer_files')),
        payment_screenshot_file_id=screenshot_file_id,
        payment_screenshot_filename=temp_filename,
        payment_status="pending_review",
        status="pending",
        phone=data.get('phone', ''),
        recipient_name=data.get('recipient_name', user.full_name),
        customer_files=json.dumps(data.get('customer_files', []))
    )

    # 1. Customer confirmation — celebration message
    loc_disp = data.get('delivery_location', '')
    if data.get('delivery_maps_url'):
        loc_disp += f" — [GPS Pin]({data.get('delivery_maps_url')})"

    phone_disp = data.get('phone', 'N/A')
    recip_disp = data.get('recipient_name', user.full_name)

    customer_msg = (
        "─────────────────────\n"
        "       ✦  Order Confirmed  ✦\n"
        "─────────────────────\n\n"
        f"🔖 *Order Code:* `{order_code}`\n\n"
        f"▸ *Items:* {data.get('items')}\n"
        f"▸ *Total:* {data.get('total_price', 0)} ETB\n"
        f"▸ *Deposit:* {data.get('deposit_amount', 0)} ETB\n"
        f"▸ *Deadline:* {data.get('deadline')}\n"
        f"▸ *Recipient:* {recip_disp}\n"
        f"▸ *Phone:* {phone_disp}\n"
        f"▸ *Delivery:* {data.get('delivery_type')} ({loc_disp})\n\n"
        "─────────────────────\n"
        "Status: *Pending Review*\n"
        "_We're verifying your deposit — you'll be notified once approved and production begins._"
    )
    if config.ADMIN_USERNAME:
        customer_msg += f"\n\nQuestions? @{config.ADMIN_USERNAME}"

    await message.answer(customer_msg, parse_mode="Markdown", reply_markup=get_main_menu_keyboard())

    # 2. Notify Owner / Admin with inline approval buttons
    if config.ADMIN_CHAT_ID:
        try:
            rush_badge = "\n⚡ *PRIORITY:* URGENT 2-DAY RUSH (+200 ETB)" if data.get("rush_fee", 0) > 0 else ""
            design_badge = "\n🎨 *INCLUDES SELORA DESIGN SERVICE (+100 ETB)*" if data.get("design_fee", 0) > 0 else ""

            phone_val = data.get('phone', 'N/A')
            recip_val = data.get('recipient_name', user.full_name)
            maps_val = data.get('delivery_maps_url')
            nav_line = f"\n🗺️ *Driver Navigation Link (RIDE / Yango / Feres):*\n[📍 Open GPS Coordinates in Google Maps]({maps_val})" if maps_val else ""

            admin_text = (
                f"🚨 *NEW ORDER & PAYMENT SUBMITTED! — {order_code}*{rush_badge}{design_badge}\n"
                f"⏰ *Time:* {timestamp}\n"
                f"👤 *Customer:* [{user.full_name}](tg://user?id={user.id}) ({username_str})\n"
                f"🆔 *Telegram ID:* `{user.id}`\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"📦 *Recipient:* *{recip_val}*\n"
                f"📞 *Driver Call Phone:* [{phone_val}](tel:{phone_val})\n"
                f"🚚 *Method:* {data.get('delivery_type')}\n"
                f"📍 *Location:* {data.get('delivery_location')}{nav_line}\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"🏷 *Items:* {data.get('items')}\n"
                f"💰 *Total:* `{data.get('total_price', 0)} ETB` | *50% Deposit:* `{data.get('deposit_amount', 0)} ETB`\n"
                f"🗓 *Needed By:* {data.get('deadline')}\n"
                f"📝 *Details:* {notes_combined}\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "💰 *Payment Receipt Attached Below.* Please verify and tap an action:"
            )

            approval_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Approve 50% Deposit", callback_data=f"pay_approve:{order_code}"),
                    InlineKeyboardButton(text="❌ Reject", callback_data=f"pay_reject:{order_code}")
                ],
                [
                    InlineKeyboardButton(text="💬 DM Customer", url=f"tg://user?id={user.id}")
                ]
            ])

            await message.bot.send_photo(
                chat_id=config.ADMIN_CHAT_ID,
                photo=screenshot_file_id,
                caption=admin_text,
                parse_mode="Markdown",
                reply_markup=approval_keyboard
            )
        except Exception as e:
            logger.error(f"Failed to alert admin of new order: {e}")

    await state.clear()


# ─── POST-PRODUCTION DELIVERY COORDINATION & DM INTAKE ────────

def get_post_delivery_choice_keyboard(order_code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏪 Free Store Pickup (Ledeta)", callback_data=f"post_del:pickup:{order_code}")
        ],
        [
            InlineKeyboardButton(text="🚚 Doorstep Taxi Delivery (Yango/Feres)", callback_data=f"post_del:taxi:{order_code}")
        ]
    ])

def get_post_taxi_location_keyboard(order_code: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏙️ Select Sub-City / Area", callback_data=f"post_subcity_pick:{order_code}")
        ],
        [
            InlineKeyboardButton(text="✏️ Type Building / Street Name", callback_data=f"post_type_addr:{order_code}")
        ],
        [
            InlineKeyboardButton(text="🏪 Switch to Free Store Pickup", callback_data=f"post_del:pickup:{order_code}")
        ]
    ])

def get_post_subcities_keyboard(order_code: str) -> InlineKeyboardMarkup:
    subcities = [
        "Bole / Medhanialem", "Kazanchis / Bambis",
        "CMC / Ayat / Summit", "Piassa / Arat Kilo",
        "Sarbet / Bisrate Gabriel", "Megenagna / 22",
        "Gerji / Imperial", "Lebu / Jemo",
        "Mexico / Ledeta", "4 Kilo / 6 Kilo",
        "Gotera / Saris", "Kera / Bulgaria"
    ]
    rows = []
    for i in range(0, len(subcities), 2):
        row = [InlineKeyboardButton(text=subcities[i], callback_data=f"post_set_sub:{order_code}:{subcities[i]}")]
        if i + 1 < len(subcities):
            row.append(InlineKeyboardButton(text=subcities[i+1], callback_data=f"post_set_sub:{order_code}:{subcities[i+1]}"))
        rows.append(row)
    rows.append([InlineKeyboardButton(text="◀ Back", callback_data=f"post_del:taxi:{order_code}")])
    return InlineKeyboardMarkup(inline_keyboard=rows)

async def send_ready_for_delivery_dm(bot, order: dict) -> bool:
    """Send interactive DM to customer when order is printed and ready for pickup/delivery."""
    order_code = order["order_code"]
    user_id = order.get("user_id")
    if not user_id:
        return False

    recip = order.get('recipient_name') or order.get('full_name') or 'Customer'
    phone = order.get('phone') or 'N/A'

    text = (
        "🎉 *Great News! Your Order is Printed & Ready to Ship!* 💛\n\n"
        f"🔖 *Order Code:* `{order_code}`\n"
        f"🏷 *Items:* {order.get('items', '')}\n"
        f"👤 *Recipient:* {recip} (`{phone}`)\n"
        "─────────────────────\n"
        "Your custom prints have finished drying & binding. Please choose how you would like to receive your package:\n\n"
        "• 🏪 *Free Store Pickup:* Pick up in person at our Ledeta store (Free of charge).\n"
        "• 🚚 *Doorstep Taxi Delivery:* Dispatched directly to your door via Yango / Feres / RIDE.\n\n"
        "⚠️ *Delivery Fee Notice:*\n"
        "The delivery fee depends on transportation distance and taxi rate (all inclusive, including Yango/Feres/RIDE) and is typically *300 – 1,000 ETB* depending on your distance in Addis Ababa, paid directly to the driver upon delivery. If you prefer to avoid the fee, you are warmly welcome to visit our Ledeta office for free pickup!\n\n"
        "👉 *Tap an option below to proceed:*"
    )
    try:
        await bot.send_message(
            chat_id=user_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=get_post_delivery_choice_keyboard(order_code)
        )
        return True
    except Exception as e:
        logger.error(f"Failed to send ready delivery DM for {order_code}: {e}")
        return False

@router.callback_query(F.data.startswith("post_del:pickup:"))
async def callback_post_del_pickup(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    order_code = callback.data.split(":")[2]
    order = database.get_order_by_code(order_code)

    database.update_order_delivery(order_code, "Store Pickup (Ledeta - Free)", "Ledeta Store (In-Person Pickup)")
    database.update_order_status(order_code, "ready_for_delivery")

    text = (
        f"✅ *Store Pickup Confirmed for Order {order_code}!* 💛\n\n"
        "📍 *Store Address:* Selora Prints, Ledeta (near Balcha Hospital), Addis Ababa\n"
        "⏰ *Pickup Hours:* Monday – Saturday, 9:00 AM – 6:00 PM\n"
        "📞 *Store Phone:* 0906287728\n"
        "─────────────────────\n"
        f"Your package is packed and waiting for you! Please present your order code `{order_code}` upon arrival.\n\n"
        "_Need to switch to doorstep taxi delivery instead? Tap below anytime._"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Switch to Taxi Delivery", callback_data=f"post_del:taxi:{order_code}")],
        [InlineKeyboardButton(text="🔍 Track Order", callback_data=f"track_orders_menu")]
    ])
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=kb)
    except Exception:
        await callback.message.answer(text, parse_mode="Markdown", reply_markup=kb)

    # Notify Admin
    if config.ADMIN_CHAT_ID:
        try:
            cust_name = order.get('recipient_name') or order.get('full_name') or 'Customer'
            cust_phone = order.get('phone') or 'N/A'
            await callback.bot.send_message(
                chat_id=config.ADMIN_CHAT_ID,
                text=(
                    f"🏪 *STORE PICKUP CONFIRMED — {order_code}*\n"
                    f"👤 *Customer:* {cust_name}\n"
                    f"📞 *Phone:* {cust_phone}\n"
                    f"Order is marked for free in-store pickup at Ledeta."
                ),
                parse_mode="Markdown"
            )
        except Exception:
            pass
    await callback.answer("Store pickup confirmed!")

@router.callback_query(F.data.startswith("post_del:taxi:"))
async def callback_post_del_taxi(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    order_code = callback.data.split(":")[2]

    text = (
        f"🚚 *DOORSTEP TAXI DELIVERY — {order_code}*\n"
        "─────────────────────\n"
        "Where should the driver deliver your package?\n\n"
        "1️⃣ 🎯 *Recommended:* Tap **'Send Exact GPS Pin'** below (best for Yango/Feres navigation)\n"
        "2️⃣ 🏙 Or select your sub-city / area from list\n"
        "3️⃣ ✏ Or type your exact building / street / landmark\n\n"
        "⚠️ *Reminder:* Taxi fare (~300 – 1,000 ETB) is paid directly to the driver upon drop-off."
    )
    await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=get_post_taxi_location_keyboard(order_code))

    # Send GPS helper keyboard
    gps_kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Send Exact GPS Pin (Best for Driver)", request_location=True)],
            [KeyboardButton(text="❌ Cancel")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await callback.message.answer(
        "💡 _You can also tap the button below to share your exact live GPS location with the driver:_ ",
        parse_mode="Markdown",
        reply_markup=gps_kb
    )
    await state.set_state(PostDeliveryFSM.waiting_for_address)
    await state.update_data(post_order_code=order_code)
    await callback.answer()

@router.callback_query(F.data.startswith("post_subcity_pick:"))
async def callback_post_subcity_pick(callback: types.CallbackQuery, state: FSMContext):
    order_code = callback.data.split(":")[1]
    await callback.message.edit_text(
        "🏙 *Select your Addis Ababa sub-city / area:*",
        parse_mode="Markdown",
        reply_markup=get_post_subcities_keyboard(order_code)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("post_set_sub:"))
async def callback_post_set_sub(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    parts = callback.data.split(":")
    order_code = parts[1]
    subcity = parts[2]
    loc_text = f"{subcity}, Addis Ababa"

    database.update_order_delivery(order_code, "Yango / Feres Taxi Delivery", loc_text)
    database.update_order_status(order_code, "ready_for_delivery")
    order = database.get_order_by_code(order_code)

    cust_name = order.get('recipient_name') or order.get('full_name') if order else 'Customer'
    cust_phone = order.get('phone') or 'N/A' if order else 'N/A'

    confirm_text = (
        f"✅ *Delivery Location Saved for Order {order_code}!* 💛\n\n"
        f"📍 *Drop-off Area:* {loc_text}\n"
        f"👤 *Recipient:* {cust_name}\n"
        f"📞 *Driver Call Phone:* `{cust_phone}`\n"
        "─────────────────────\n"
        "🚕 Our team is preparing your package for driver dispatch (Yango / Feres / RIDE). "
        f"The driver will call you at `{cust_phone}` upon arriving.\n\n"
        "⚠️ *Taxi Fare:* ~300 – 1,000 ETB paid directly to the driver upon drop-off.\n\n"
        "_Need to change address or switch to store pickup? Tap below anytime._"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Change Delivery Details", callback_data=f"post_del:change:{order_code}")],
        [InlineKeyboardButton(text="🔍 Track Order Status", callback_data="track_orders_menu")]
    ])
    try:
        await callback.message.edit_text(confirm_text, parse_mode="Markdown", reply_markup=kb)
    except Exception:
        await callback.message.answer(confirm_text, parse_mode="Markdown", reply_markup=kb)
    await callback.message.answer("Delivery location updated.", reply_markup=ReplyKeyboardRemove())

    # Alert Admin
    if config.ADMIN_CHAT_ID:
        try:
            await callback.bot.send_message(
                chat_id=config.ADMIN_CHAT_ID,
                text=(
                    f"🚨 *TAXI DELIVERY DISPATCH READY — {order_code}*\n"
                    f"👤 *Recipient:* {cust_name}\n"
                    f"📞 *Driver Call Phone:* [{cust_phone}](tel:{cust_phone})\n"
                    f"📍 *Area:* {loc_text}\n"
                    "Ready to call Yango / Feres / RIDE!"
                ),
                parse_mode="Markdown"
            )
        except Exception:
            pass
    await callback.answer("Delivery location saved!")

@router.callback_query(F.data.startswith("post_type_addr:"))
async def callback_post_type_addr(callback: types.CallbackQuery, state: FSMContext):
    order_code = callback.data.split(":")[1]
    await state.set_state(PostDeliveryFSM.waiting_for_address)
    await state.update_data(post_order_code=order_code)
    await callback.message.edit_text(
        "✏️ *Please type your exact street, building name, or landmark below:*\n\n"
        "_(e.g., Bole Medhanialem next to Edna Mall, Morning Star Bldg 3rd Fl)_",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.message(PostDeliveryFSM.waiting_for_address, F.location)
async def process_post_location_gps(message: types.Message, state: FSMContext):
    data = await state.get_data()
    order_code = data.get("post_order_code")
    await state.clear()

    lat = message.location.latitude
    lon = message.location.longitude
    maps_url = f"https://www.google.com/maps?q={lat},{lon}"
    loc_text = f"GPS Pin ({lat:.4f}, {lon:.4f})"

    if order_code:
        database.update_order_delivery(order_code, "Yango / Feres Taxi Delivery", loc_text)
        database.update_order_status(order_code, "ready_for_delivery")

    order = database.get_order_by_code(order_code) if order_code else {}
    cust_name = order.get('recipient_name') or order.get('full_name') or 'Customer'
    cust_phone = order.get('phone') or 'N/A'

    confirm_text = (
        f"✅ *Exact GPS Location Received for Order {order_code}!* 🎯\n\n"
        f"📍 [Open Coordinates in Google Maps]({maps_url})\n"
        f"👤 *Recipient:* {cust_name}\n"
        f"📞 *Driver Call Phone:* `{cust_phone}`\n"
        "─────────────────────\n"
        "🚕 Our driver will navigate directly to your GPS coordinates via Yango / Feres / RIDE. "
        f"They will call `{cust_phone}` when outside!\n\n"
        "_Need to change delivery details? Tap below anytime._"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Change Delivery Details", callback_data=f"post_del:change:{order_code}")],
        [InlineKeyboardButton(text="🔍 Track Order Status", callback_data="track_orders_menu")]
    ])
    await message.answer(confirm_text, parse_mode="Markdown", reply_markup=kb)
    await message.answer("GPS pinned.", reply_markup=ReplyKeyboardRemove())

    # Alert Admin
    if config.ADMIN_CHAT_ID:
        try:
            await message.bot.send_message(
                chat_id=config.ADMIN_CHAT_ID,
                text=(
                    f"🚨 *TAXI DELIVERY GPS PIN RECEIVED — {order_code}*\n"
                    f"👤 *Recipient:* {cust_name}\n"
                    f"📞 *Driver Call Phone:* [{cust_phone}](tel:{cust_phone})\n"
                    f"📍 *GPS Link:* [Google Maps Link]({maps_url})\n"
                    "Ready to dispatch driver directly to GPS pin!"
                ),
                parse_mode="Markdown"
            )
        except Exception:
            pass

@router.message(PostDeliveryFSM.waiting_for_address, F.text)
async def process_post_location_text(message: types.Message, state: FSMContext):
    if message.text in ["❌ Cancel", "❌ Cancel Order"]:
        await state.clear()
        await message.answer("Cancelled address update.", reply_markup=ReplyKeyboardRemove())
        return

    data = await state.get_data()
    order_code = data.get("post_order_code")
    await state.clear()

    loc_text = message.text.strip()
    if order_code:
        database.update_order_delivery(order_code, "Yango / Feres Taxi Delivery", loc_text)
        database.update_order_status(order_code, "ready_for_delivery")

    order = database.get_order_by_code(order_code) if order_code else {}
    cust_name = order.get('recipient_name') or order.get('full_name') or 'Customer'
    cust_phone = order.get('phone') or 'N/A'

    confirm_text = (
        f"✅ *Delivery Address Saved for Order {order_code}!* 💛\n\n"
        f"📍 *Address:* {loc_text}\n"
        f"👤 *Recipient:* {cust_name}\n"
        f"📞 *Driver Call Phone:* `{cust_phone}`\n"
        "─────────────────────\n"
        f"🚕 We are preparing your taxi dispatch. Driver will call you at `{cust_phone}` upon arrival. (~300 – 1,000 ETB paid to driver).\n\n"
        "_Need to update or switch to office pickup? Tap below anytime._"
    )
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Change Delivery Details", callback_data=f"post_del:change:{order_code}")],
        [InlineKeyboardButton(text="🔍 Track Order Status", callback_data="track_orders_menu")]
    ])
    await message.answer(confirm_text, parse_mode="Markdown", reply_markup=kb)
    await message.answer("Address saved.", reply_markup=ReplyKeyboardRemove())

    # Alert Admin
    if config.ADMIN_CHAT_ID:
        try:
            await message.bot.send_message(
                chat_id=config.ADMIN_CHAT_ID,
                text=(
                    f"🚨 *TAXI DELIVERY ADDRESS RECEIVED — {order_code}*\n"
                    f"👤 *Recipient:* {cust_name}\n"
                    f"📞 *Call Phone:* [{cust_phone}](tel:{cust_phone})\n"
                    f"📍 *Address:* {loc_text}\n"
                    "Ready to call Yango / Feres / RIDE!"
                ),
                parse_mode="Markdown"
            )
        except Exception:
            pass

@router.callback_query(F.data.startswith("post_del:change:"))
async def callback_post_del_change(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    order_code = callback.data.split(":")[2]
    order = database.get_order_by_code(order_code)

    text = (
        f"✏️ *CHANGE DELIVERY METHOD / DETAILS — {order_code}*\n"
        "─────────────────────\n"
        f"• *Current Method:* {order.get('delivery_type', 'None')}\n"
        f"• *Current Location:* {order.get('delivery_location', 'None')}\n"
        "─────────────────────\n"
        "Choose how you would like to receive your package:\n\n"
        "• 🏪 *Free Store Pickup:* In person at Ledeta store\n"
        "• 🚚 *Doorstep Taxi Delivery:* Yango / Feres dispatch (~300 – 1,000 ETB paid to driver)"
    )
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=get_post_delivery_choice_keyboard(order_code))
    except Exception:
        await callback.message.answer(text, parse_mode="Markdown", reply_markup=get_post_delivery_choice_keyboard(order_code))
    await callback.answer()
