import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
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
    ReplyKeyboardRemove
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

class OrderFSM(StatesGroup):
    waiting_for_product = State()
    waiting_for_quantity = State()
    waiting_for_card_design = State()
    waiting_for_design_mode = State()
    waiting_for_photos = State()
    waiting_for_deadline = State()
    waiting_for_delivery_type = State()
    waiting_for_recipient_name = State()
    waiting_for_phone = State()
    waiting_for_location = State()
    waiting_for_payment_receipt = State()

# -------------------------------------------------------------
# KEYBOARDS FOR DETERMINISTIC APP-LIKE INTERACTION
# -------------------------------------------------------------

def get_product_picker_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏷 Stickers (Min 15)", callback_data="sel_prod:stickers"),
            InlineKeyboardButton(text="🔖 Bookmarks (Min 2)", callback_data="sel_prod:bookmarks")
        ],
        [
            InlineKeyboardButton(text="💼 Business Cards (Min 50)", callback_data="sel_prod:business_cards"),
            InlineKeyboardButton(text="📸 Polaroids (Min 10)", callback_data="sel_prod:polaroid")
        ],
        [
            InlineKeyboardButton(text="📖 Photo Books & Minibooks ▾", callback_data="sel_cat:books")
        ],
        [
            InlineKeyboardButton(text="📓 Mini Notebook (200 ETB)", callback_data="sel_prod:mini_notebook"),
            InlineKeyboardButton(text="📔 Notebook (500 ETB)", callback_data="sel_prod:notebook")
        ],
        [
            InlineKeyboardButton(text="☕ Custom Mug (1,500 ETB)", callback_data="sel_prod:mug"),
            InlineKeyboardButton(text="🧩 Photo Puzzle (1,500 ETB)", callback_data="sel_prod:puzzle")
        ],
        [
            InlineKeyboardButton(text="🟢 Poster A5 (Min 10)", callback_data="sel_prod:sticker_poster_a5"),
            InlineKeyboardButton(text="🟢 Poster A4 (Min 10)", callback_data="sel_prod:sticker_poster_a4")
        ],
        [
            InlineKeyboardButton(
                text="🤝 Bulk Order (>100 pcs) — Talk to Owner",
                url=f"https://t.me/{config.ADMIN_USERNAME}?text=Hi%2C%20I%20am%20interested%20in%20a%20bulk%20order%20from%20Selora%20Prints"
            )
        ],
        [
            InlineKeyboardButton(text="❌ Cancel Order", callback_data="cancel_order")
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
            InlineKeyboardButton(text=f"-{step_large}", callback_data=f"qstep:{prod_id}:-{step_large}"),
            InlineKeyboardButton(text=f"-{step_small}", callback_data=f"qstep:{prod_id}:-{step_small}"),
            InlineKeyboardButton(text=f"🔢 {qty}", callback_data="noop"),
            InlineKeyboardButton(text=f"+{step_small}", callback_data=f"qstep:{prod_id}:+{step_small}"),
            InlineKeyboardButton(text=f"+{step_large}", callback_data=f"qstep:{prod_id}:+{step_large}")
        ],
        [
            InlineKeyboardButton(text=f"✅ Confirm: {qty} pieces", callback_data=f"qconfirm:{prod_id}:{qty}")
        ],
        [
            InlineKeyboardButton(
                text="🤝 Need Bulk (>100 pcs)? Negotiate Price",
                url=f"https://t.me/{config.ADMIN_USERNAME}?text=Hi%2C%20I%20am%20interested%20in%20a%20bulk%20order%20for%20{prod_id}%20with%20custom%20pricing"
            )
        ],
        [
            InlineKeyboardButton(text="◀ Change Item", callback_data="sel_cat:all"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="cancel_order")
        ]
    ])

def get_card_design_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📁 I have ready design file (Free)", callback_data="card_design:ready")],
        [InlineKeyboardButton(text="🎨 Selora Custom Design Service (+100 ETB)", callback_data="card_design:selora")],
        [InlineKeyboardButton(text="❌ Cancel Order", callback_data="cancel_order")]
    ])

def get_design_mode_keyboard(qty: int, prod_name: str) -> InlineKeyboardMarkup:
    buttons = []
    if qty > 1:
        buttons.append([InlineKeyboardButton(text=f"🖼️ 1 Design for all {qty} copies", callback_data="dmode:single")])
        buttons.append([InlineKeyboardButton(text=f"📸 Different photo for each item ({qty} photos)", callback_data="dmode:multi")])
    else:
        buttons.append([InlineKeyboardButton(text="📸 Upload My Photo / Artwork", callback_data="dmode:single")])

    buttons.append([InlineKeyboardButton(text="🎨 Choose from Selora Ready Designs", callback_data="dmode:templates")])
    buttons.append([InlineKeyboardButton(text="❌ Cancel Order", callback_data="cancel_order")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_template_gallery_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✨ Minimalist Aesthetic", callback_data="tmpl:Minimalist Aesthetic"),
            InlineKeyboardButton(text="🎞 Retro Vintage Film", callback_data="tmpl:Retro Vintage Film")
        ],
        [
            InlineKeyboardButton(text="🌿 Floral & Nature", callback_data="tmpl:Floral & Nature"),
            InlineKeyboardButton(text="💬 Typographic Quotes", callback_data="tmpl:Typographic Quotes")
        ],
        [
            InlineKeyboardButton(text="🔤 Custom Monogram", callback_data="tmpl:Custom Monogram")
        ],
        [
            InlineKeyboardButton(text="◀ Back to Photo Upload", callback_data="dmode:back")
        ]
    ])

def get_date_picker_keyboard() -> InlineKeyboardMarkup:
    now = datetime.now()
    d2 = now + timedelta(days=2)
    d3 = now + timedelta(days=3)
    d4 = now + timedelta(days=4)
    d5 = now + timedelta(days=5)
    d7 = now + timedelta(days=7)

    d2_label = f"⚡ {d2.strftime('%a, %b %d')} (Urgent: +200 ETB)"
    d3_label = f"🗓 {d3.strftime('%a, %b %d')} (Standard)"
    d4_label = f"🗓 {d4.strftime('%a, %b %d')} (Standard)"
    d5_label = f"🗓 {d5.strftime('%a, %b %d')} (Standard)"
    d7_label = f"📅 Next Week ({d7.strftime('%b %d')}+)"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=d2_label, callback_data=f"pick_date:{d2.strftime('%a, %b %d')}:200")],
        [
            InlineKeyboardButton(text=d3_label, callback_data=f"pick_date:{d3.strftime('%a, %b %d')}:0"),
            InlineKeyboardButton(text=d4_label, callback_data=f"pick_date:{d4.strftime('%a, %b %d')}:0")
        ],
        [
            InlineKeyboardButton(text=d5_label, callback_data=f"pick_date:{d5.strftime('%a, %b %d')}:0"),
            InlineKeyboardButton(text=d7_label, callback_data=f"pick_date:{d7_label}:0")
        ],
        [InlineKeyboardButton(text="❌ Cancel Order", callback_data="cancel_order")]
    ])

def get_recipient_name_keyboard(tg_name: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"✅ Use My Name: {tg_name}", callback_data="recip_name:tg")],
        [InlineKeyboardButton(text="✏️ Different Recipient Name", callback_data="recip_name:custom")],
        [InlineKeyboardButton(text="❌ Cancel Order", callback_data="cancel_order")]
    ])

def get_phone_request_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Share Phone Number (1-Tap)", request_contact=True)],
            [KeyboardButton(text="❌ Cancel Order")]
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
            [KeyboardButton(text="❌ Cancel Order")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_subcities_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📍 Bole / Medhanialem", callback_data="subcity:Bole / Medhanialem"),
            InlineKeyboardButton(text="📍 Kazanchis / Bambis", callback_data="subcity:Kazanchis / Bambis")
        ],
        [
            InlineKeyboardButton(text="📍 CMC / Ayat / Summit", callback_data="subcity:CMC / Ayat / Summit"),
            InlineKeyboardButton(text="📍 Piassa / Arat Kilo", callback_data="subcity:Piassa / Arat Kilo")
        ],
        [
            InlineKeyboardButton(text="📍 Sarbet / Bisrate Gabriel", callback_data="subcity:Sarbet / Bisrate Gabriel"),
            InlineKeyboardButton(text="📍 Megenagna / 22", callback_data="subcity:Megenagna / 22")
        ],
        [
            InlineKeyboardButton(text="📍 Gerji / Imperial", callback_data="subcity:Gerji / Imperial"),
            InlineKeyboardButton(text="📍 Lebu / Jemo", callback_data="subcity:Lebu / Jemo")
        ],
        [
            InlineKeyboardButton(text="📍 Mexico / Ledeta", callback_data="subcity:Mexico / Ledeta"),
            InlineKeyboardButton(text="📍 4 Kilo / 6 Kilo", callback_data="subcity:4 Kilo / 6 Kilo")
        ],
        [
            InlineKeyboardButton(text="📍 Gotera / Saris", callback_data="subcity:Gotera / Saris"),
            InlineKeyboardButton(text="📍 Kera / Bulgaria", callback_data="subcity:Kera / Bulgaria")
        ],
        [
            InlineKeyboardButton(text="◀ Back to Location Options", callback_data="subcity:back")
        ]
    ])

# -------------------------------------------------------------
# START ORDER & PRODUCT PICKER
# -------------------------------------------------------------

@router.message(Command("cancel"))
@router.message(F.text.in_(["❌ Cancel", "❌ Cancel Order"]))
async def cancel_order(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "❌ Order process cancelled. You can start anytime with the menu below!",
        reply_markup=get_main_menu_keyboard()
    )

@router.callback_query(F.data == "cancel_order")
async def callback_cancel_order(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Order cancelled.")
    await callback.message.answer(
        "Feel free to browse or ask questions anytime! 💛",
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()

@router.message(Command("order"))
@router.message(F.text == "📝 Place an Order")
async def start_order(message: types.Message, state: FSMContext):
    await state.clear()
    await state.set_state(OrderFSM.waiting_for_product)
    await message.answer(
        "📱 *SELORA ORDER ASSISTANT*\n"
        "`[ 🟡 ⚪ ⚪ ⚪ ] Step 1 of 4: Select Your Product`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Tap the item you'd like to order below:",
        parse_mode="Markdown",
        reply_markup=get_product_picker_keyboard()
    )

@router.callback_query(F.data == "start_order")
async def callback_start_order(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(OrderFSM.waiting_for_product)
    await callback.message.answer(
        "📱 *SELORA ORDER ASSISTANT*\n"
        "`[ 🟡 ⚪ ⚪ ⚪ ] Step 1 of 4: Select Your Product`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Tap the item you'd like to order below:",
        parse_mode="Markdown",
        reply_markup=get_product_picker_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "sel_cat:books")
async def callback_show_books_menu(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📖 *SELECT PHOTO BOOK / MINIBOOK SIZE:*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Choose your preferred cover and size:",
        parse_mode="Markdown",
        reply_markup=get_books_picker_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "sel_cat:all")
async def callback_show_all_prods(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📱 *SELORA ORDER ASSISTANT*\n"
        "`[ 🟡 ⚪ ⚪ ⚪ ] Step 1 of 4: Select Your Product`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Tap the item you'd like to order below:",
        parse_mode="Markdown",
        reply_markup=get_product_picker_keyboard()
    )
    await callback.answer()

# -------------------------------------------------------------
# QUANTITY STEPPER (DETERMINISTIC INTERACTION)
# -------------------------------------------------------------

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

    min_note = f"\n⚠️ *Minimum Order:* `{min_ord} pieces`" if min_ord > 1 else ""
    price_info = f"`{price} ETB` each" if price else "Custom Quote"
    sub_line = f"\n💰 *Subtotal:* `{subtotal} ETB`" if price else ""

    text = (
        f"💛 *Select Quantity for {prod['name']}*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷 *Unit Price:* {price_info}{min_note}\n"
        f"🔢 *Current Quantity:* `{qty} pieces`{sub_line}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Use buttons below to adjust quantity:"
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
        await callback.answer(f"⚠️ Minimum order is {min_ord} pieces!", show_alert=True)
        return

    await state.update_data(quantity=new_qty)
    subtotal = price * new_qty if price else 0

    min_note = f"\n⚠️ *Minimum Order:* `{min_ord} pieces`" if min_ord > 1 else ""
    price_info = f"`{price} ETB` each" if price else "Custom Quote"
    sub_line = f"\n💰 *Subtotal:* `{subtotal} ETB`" if price else ""

    text = (
        f"💛 *Select Quantity for {data.get('product_name', prod_id)}*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷 *Unit Price:* {price_info}{min_note}\n"
        f"🔢 *Current Quantity:* `{new_qty} pieces`{sub_line}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Use buttons below to adjust quantity:"
    )

    keyboard = get_stepper_keyboard(prod_id, new_qty, min_ord)
    try:
        await callback.message.edit_text(text, parse_mode="Markdown", reply_markup=keyboard)
    except Exception:
        pass
    await callback.answer()

# -------------------------------------------------------------
# CONFIRM QUANTITY -> BUSINESS CARD DESIGN OPTION OR DESIGN MODE
# -------------------------------------------------------------

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
            f"💼 *BUSINESS CARD DESIGN OPTION*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Ordering: *{qty} Business Cards*\n\n"
            "Do you have a print-ready design file, or would you like Selora to create a custom design for you?\n\n"
            "• 📁 *My Own Ready Design:* Free (upload below)\n"
            "• 🎨 *Selora Custom Design Service:* +100 ETB",
            parse_mode="Markdown",
            reply_markup=get_card_design_keyboard()
        )
        await callback.answer()
        return

    # Normal products -> Design mode selection
    await advance_to_design_mode(callback.message, state)
    await callback.answer()

# -------------------------------------------------------------
# BUSINESS CARD DESIGN HANDLER
# -------------------------------------------------------------

@router.callback_query(OrderFSM.waiting_for_card_design, F.data.startswith("card_design:"))
async def callback_card_design(callback: types.CallbackQuery, state: FSMContext):
    choice = callback.data.split(":")[1]
    if choice == "selora":
        design_fee = 100
        design_note = "Selora Custom Design Service (+100 ETB)"
        await callback.message.answer("🎨 Selected: *Selora Custom Design Service (+100 ETB)*", parse_mode="Markdown")
    else:
        design_fee = 0
        design_note = "Customer Ready Design File"
        await callback.message.answer("📁 Selected: *Customer Ready Design File (Free)*", parse_mode="Markdown")

    await state.update_data(design_fee=design_fee, design_note=design_note)
    await advance_to_design_mode(callback.message, state)
    await callback.answer()

# -------------------------------------------------------------
# DESIGN & ARTWORK SELECTION MODE
# -------------------------------------------------------------

async def advance_to_design_mode(message: types.Message, state: FSMContext):
    data = await state.get_data()
    qty = data.get("quantity", 1)
    prod_name = data.get("product_name", "Items")

    await state.set_state(OrderFSM.waiting_for_design_mode)
    text = (
        f"🎨 *ARTWORK & DESIGN SELECTION*\n"
        f"`[ 🟢 🟡 ⚪ ⚪ ] Step 2 of 4: Design Source`\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"Item: *{qty}x {prod_name}*\n\n"
        "How would you like to provide the designs/photos for this order?"
    )
    await message.edit_text(text, parse_mode="Markdown", reply_markup=get_design_mode_keyboard(qty, prod_name))

@router.callback_query(OrderFSM.waiting_for_design_mode, F.data.startswith("dmode:"))
async def callback_design_mode(callback: types.CallbackQuery, state: FSMContext):
    mode = callback.data.split(":")[1]
    data = await state.get_data()
    qty = data.get("quantity", 1)
    prod_name = data.get("product_name", "items")

    if mode == "templates":
        await callback.message.edit_text(
            "🎨 *SELORA READY DESIGN TEMPLATES*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Choose a template style for your prints:",
            parse_mode="Markdown",
            reply_markup=get_template_gallery_keyboard()
        )
        await callback.answer()
        return

    if mode == "back":
        await advance_to_design_mode(callback.message, state)
        await callback.answer()
        return

    if mode == "single":
        await state.update_data(design_mode="single", photos=[])
        await state.set_state(OrderFSM.waiting_for_photos)
        await callback.message.edit_text(
            f"📸 *UPLOAD DESIGN / ARTWORK*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"This design will be printed on all *{qty} copies* of {prod_name}.\n\n"
            "👉 *Please send your photo or artwork file now:*",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
        await callback.answer()
        return

    if mode == "multi":
        await state.update_data(design_mode="multi", photos=[])
        await state.set_state(OrderFSM.waiting_for_photos)

        done_btn = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Done Uploading", callback_data="done_photos")],
            [InlineKeyboardButton(text="❌ Cancel Order", callback_data="cancel_order")]
        ])

        await callback.message.edit_text(
            f"📸 *UPLOAD {qty} PHOTOS*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"Send your photos one by one or as an album.\n\n"
            f"• *Progress:* `0 / {qty} photos received`\n\n"
            "Send your photos now (or tap *Done Uploading* when finished):",
            parse_mode="Markdown",
            reply_markup=done_btn
        )
        await callback.answer()

@router.callback_query(OrderFSM.waiting_for_design_mode, F.data.startswith("tmpl:"))
async def callback_template_chosen(callback: types.CallbackQuery, state: FSMContext):
    tmpl_name = callback.data.split(":", 1)[1]
    await state.update_data(
        design_mode="template",
        design_note=f"Selora Template: {tmpl_name}",
        file_id=None
    )
    await callback.message.answer(f"✅ Selected Template: *{tmpl_name}*", parse_mode="Markdown")
    await advance_to_deadline_picker(callback.message, state)
    await callback.answer()

# -------------------------------------------------------------
# PHOTO UPLOADER (SINGLE OR MULTI MATCHING MINIMUM ORDERS)
# -------------------------------------------------------------

@router.message(OrderFSM.waiting_for_photos, F.photo | F.document)
async def process_photo_upload(message: types.Message, state: FSMContext):
    data = await state.get_data()
    mode = data.get("design_mode", "single")
    qty = data.get("quantity", 1)

    file_id = message.photo[-1].file_id if message.photo else message.document.file_id

    if mode == "single":
        await state.update_data(file_id=file_id, file_type="photo" if message.photo else "document")
        await message.answer("✅ Artwork received successfully! 🎨")
        await advance_to_deadline_picker(message, state)
        return

    # Multi photo mode
    photos = data.get("photos", [])
    photos.append(file_id)
    await state.update_data(photos=photos, file_id=photos[0])

    count = len(photos)
    if count >= qty:
        await message.answer(f"🎉 *All {count}/{qty} photos received successfully!* 💛", parse_mode="Markdown")
        await advance_to_deadline_picker(message, state)
    else:
        done_btn = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"✅ Done Uploading ({count}/{qty})", callback_data="done_photos")],
            [InlineKeyboardButton(text="❌ Cancel Order", callback_data="cancel_order")]
        ])
        await message.answer(
            f"📸 *Received photo {count} of {qty}!*\n\n"
            f"Send more photos or tap *Done Uploading* when you're finished:",
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

    await callback.message.answer(f"✅ Finished photo upload with *{len(photos)} photos*! 💛", parse_mode="Markdown")
    await advance_to_deadline_picker(callback.message, state)
    await callback.answer()

# -------------------------------------------------------------
# INTERACTIVE DATE PICKER (DETERMINISTIC DEADLINES)
# -------------------------------------------------------------

async def advance_to_deadline_picker(message: types.Message, state: FSMContext):
    await state.set_state(OrderFSM.waiting_for_deadline)
    text = (
        "🗓 *TIMING & DELIVERY DEADLINE*\n"
        "`[ 🟢 🟢 🟡 ⚪ ] Step 3 of 4: Select Completion Date`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "⏱ *Turnaround Policy:*\n"
        "• 🟢 *Standard:* 3+ days (normal pricing)\n"
        "• ⚡ *Urgent Rush (in 2 days):* +200 ETB rush fee\n"
        "• ⛔ *Next-day (tomorrow):* Cannot be accepted due to drying & binding time.\n\n"
        "👉 *Tap your desired completion date below:*"
    )
    if isinstance(message, types.CallbackQuery):
        await message.message.edit_text(text, parse_mode="Markdown", reply_markup=get_date_picker_keyboard())
    else:
        await message.answer(text, parse_mode="Markdown", reply_markup=get_date_picker_keyboard())

@router.callback_query(OrderFSM.waiting_for_deadline, F.data.startswith("pick_date:"))
async def callback_date_picked(callback: types.CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    date_label = parts[1]
    rush_fee = int(parts[2])

    await state.update_data(deadline=date_label, rush_fee=rush_fee)
    await state.set_state(OrderFSM.waiting_for_delivery_type)

    rush_note = " _(+200 ETB urgent rush fee)_" if rush_fee > 0 else ""
    await callback.message.edit_text(f"✅ Completion Date: *{date_label}*{rush_note}", parse_mode="Markdown")

    await callback.message.answer(
        "📱 *SELORA ORDER ASSISTANT*\n"
        "`[ 🟢 🟢 🟢 ⚪ ] Step 4 of 4: Delivery Method`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "How would you like to receive your prints?\n\n"
        "• 🏪 *Store Pickup:* Free directly at our Ledeta store\n"
        "• 🚚 *Yango Delivery:* Delivered across Addis Ababa (fee paid upon receipt)",
        parse_mode="Markdown",
        reply_markup=get_delivery_choice_keyboard()
    )
    await callback.answer()

# -------------------------------------------------------------
# DELIVERY SELECTION & DETERMINISTIC DISPATCH INTAKE
# -------------------------------------------------------------

@router.callback_query(OrderFSM.waiting_for_delivery_type, F.data.startswith("delivery_choice:"))
async def process_delivery_choice(callback: types.CallbackQuery, state: FSMContext):
    choice = callback.data.split(":")[1]
    user = callback.from_user
    if choice == "pickup":
        await state.update_data(
            delivery_type="Store Pickup (Ledeta - Free)",
            delivery_location="Ledeta Store (In-Person Pickup)",
            recipient_name=user.full_name,
            phone="Store Pickup / In Person"
        )
        await callback.message.edit_text("✅ Selected: *Store Pickup (Ledeta - Free)*", parse_mode="Markdown")
        await show_payment_summary(callback.message, state)
    else:
        await state.update_data(delivery_type="Yango / Feres / RIDE Delivery")
        await state.set_state(OrderFSM.waiting_for_recipient_name)
        await callback.message.edit_text("✅ Selected: *Yango / Feres / RIDE Delivery*", parse_mode="Markdown")
        await callback.message.answer(
            "👤 *STEP 1 OF 3: RECIPIENT NAME FOR DRIVER DISPATCH*\n"
            "`[ 🟢 🟢 🟢 🟡 ] Driver Dispatch Information`\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "Who will be meeting the driver to receive the package?\n\n"
            "👉 *Tap below to confirm recipient:*",
            parse_mode="Markdown",
            reply_markup=get_recipient_name_keyboard(user.full_name)
        )
    await callback.answer()

@router.callback_query(OrderFSM.waiting_for_recipient_name, F.data.startswith("recip_name:"))
async def callback_recipient_name(callback: types.CallbackQuery, state: FSMContext):
    mode = callback.data.split(":")[1]
    user = callback.from_user
    if mode == "tg":
        await state.update_data(recipient_name=user.full_name)
        await callback.message.edit_text(f"✅ Recipient: *{user.full_name}*", parse_mode="Markdown")
        await state.set_state(OrderFSM.waiting_for_phone)
        await callback.message.answer(
            "📱 *STEP 2 OF 3: CONTACT PHONE NUMBER*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "The driver (Feres / Yango / RIDE) will call this number when arriving.\n\n"
            "👉 *Tap '📱 Share Phone Number (1-Tap)'* below, or type your 10-digit number (e.g. `0911223344`):",
            parse_mode="Markdown",
            reply_markup=get_phone_request_keyboard()
        )
    else:
        await callback.message.edit_text(
            "✏️ *Please type the full name of the recipient:*\n\n_(e.g., Kebron Girma)_",
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
    await message.answer(f"✅ Recipient: *{name}*", parse_mode="Markdown")
    await state.set_state(OrderFSM.waiting_for_phone)
    await message.answer(
        "📱 *STEP 2 OF 3: CONTACT PHONE NUMBER*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "The driver (Feres / Yango / RIDE) will call this number when arriving.\n\n"
        "👉 *Tap '📱 Share Phone Number (1-Tap)'* below, or type your 10-digit number (e.g. `0911223344`):",
        parse_mode="Markdown",
        reply_markup=get_phone_request_keyboard()
    )

@router.message(OrderFSM.waiting_for_phone, F.contact)
async def process_phone_contact(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number
    if not phone.startswith("+") and len(phone) == 10 and phone.startswith("0"):
        phone = f"+251{phone[1:]}"
    await state.update_data(phone=phone)
    await message.answer(f"✅ Contact Phone: *{phone}*", parse_mode="Markdown")
    await state.set_state(OrderFSM.waiting_for_location)
    await message.answer(
        "📍 *STEP 3 OF 3: EXACT LOCATION FOR DRIVER DISPATCH*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "To ensure the driver (Feres / Yango / RIDE) navigates directly to your door without getting lost:\n\n"
        "1️⃣ 🎯 *Recommended:* Tap **'📍 Send Exact GPS Pin'** below.\n"
        "2️⃣ 🏙️ Or tap **'Choose Addis Ababa Sub-City / Area'** for 1-tap area selection.\n"
        "3️⃣ ✏️ Or type your specific building / street name.",
        parse_mode="Markdown",
        reply_markup=get_location_dispatch_keyboard()
    )

@router.message(OrderFSM.waiting_for_phone, F.text)
async def process_phone_text(message: types.Message, state: FSMContext):
    if message.text in ["❌ Cancel", "❌ Cancel Order"]:
        await cancel_order(message, state)
        return
    phone = message.text.strip()
    await state.update_data(phone=phone)
    await message.answer(f"✅ Contact Phone: *{phone}*", parse_mode="Markdown")
    await state.set_state(OrderFSM.waiting_for_location)
    await message.answer(
        "📍 *STEP 3 OF 3: EXACT LOCATION FOR DRIVER DISPATCH*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "To ensure the driver (Feres / Yango / RIDE) navigates directly to your door without getting lost:\n\n"
        "1️⃣ 🎯 *Recommended:* Tap **'📍 Send Exact GPS Pin'** below.\n"
        "2️⃣ 🏙️ Or tap **'Choose Addis Ababa Sub-City / Area'** for 1-tap area selection.\n"
        "3️⃣ ✏️ Or type your specific building / street name.",
        parse_mode="Markdown",
        reply_markup=get_location_dispatch_keyboard()
    )

@router.message(OrderFSM.waiting_for_location, F.location)
async def process_location_gps(message: types.Message, state: FSMContext):
    lat = message.location.latitude
    lon = message.location.longitude
    maps_url = f"https://www.google.com/maps?q={lat},{lon}"
    loc_text = f"GPS Pin ({lat:.4f}, {lon:.4f})"
    await state.update_data(delivery_location=loc_text, delivery_maps_url=maps_url)
    await message.answer(
        f"🎯 *GPS Pin Received!*\n[🗺️ Open in Google Maps]({maps_url})",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )
    await show_payment_summary(message, state)

@router.message(OrderFSM.waiting_for_location, F.text == "🏙️ Choose Addis Ababa Sub-City / Area")
async def process_location_subcity_prompt(message: types.Message, state: FSMContext):
    await message.answer(
        "🏙️ *Select your Addis Ababa sub-city / area:*",
        parse_mode="Markdown",
        reply_markup=get_subcities_keyboard()
    )

@router.callback_query(OrderFSM.waiting_for_location, F.data.startswith("subcity:"))
async def process_subcity_choice(callback: types.CallbackQuery, state: FSMContext):
    subcity = callback.data.split(":", 1)[1]
    if subcity == "back":
        await callback.message.edit_text("📍 Please tap an option below to set your delivery location:")
        await callback.answer()
        return

    loc_text = f"{subcity}, Addis Ababa"
    await state.update_data(delivery_location=loc_text)
    await callback.message.edit_text(f"✅ Location: *{loc_text}*", parse_mode="Markdown")
    await callback.message.answer("Proceeding to payment summary...", reply_markup=ReplyKeyboardRemove())
    await show_payment_summary(callback.message, state)
    await callback.answer()

@router.message(OrderFSM.waiting_for_location, F.text == "✏️ Type Landmark / Street Name")
async def process_location_type_prompt(message: types.Message, state: FSMContext):
    await message.answer(
        "✏️ *Please type your street, building, or landmark:*\n\n_(e.g., Bole Medhanialem next to Edna Mall, Morning Star Bldg 3rd Fl)_",
        parse_mode="Markdown"
    )

@router.message(OrderFSM.waiting_for_location, F.text)
async def process_location_text(message: types.Message, state: FSMContext):
    if message.text in ["❌ Cancel", "❌ Cancel Order"]:
        await cancel_order(message, state)
        return
    if message.text in ["🏙️ Choose Addis Ababa Sub-City / Area", "✏️ Type Landmark / Street Name"]:
        return

    loc_text = message.text.strip()
    await state.update_data(delivery_location=loc_text)
    await message.answer(f"✅ Location: *{loc_text}*", parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())
    await show_payment_summary(message, state)

# -------------------------------------------------------------
# STEP 4: 50% PRE-PAYMENT SUMMARY & VERIFICATION
# -------------------------------------------------------------

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
        fee_lines += f"• Selora Custom Design: `+{design_fee} ETB`\n"
    if rush_fee > 0:
        fee_lines += f"• ⚡ Urgent Rush Fee (2-day): `+{rush_fee} ETB`\n"

    recip_str = data.get('recipient_name', 'Customer')
    phone_str = data.get('phone', 'N/A')
    loc_display = data.get('delivery_location', 'Ledeta Store')
    if data.get('delivery_maps_url'):
        loc_display += f" — [🗺️ GPS Link]({data.get('delivery_maps_url')})"

    payment_prompt = (
        "📱 *SELORA ORDER SUMMARY & 50% DEPOSIT*\n"
        "`[ 🟢 🟢 🟢 🟡 ] Final Step: Advance Pre-Payment`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🏷 *Order:* {data.get('items')}\n"
        f"🎨 *Design:* {data.get('design_note', 'Custom artwork attached')}\n"
        f"🗓 *Needed By:* {data.get('deadline')}\n"
        f"👤 *Recipient:* {recip_str}\n"
        f"📞 *Contact Phone:* `{phone_str}`\n"
        f"🚚 *Delivery:* {data.get('delivery_type')} ({loc_display})\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💰 *Cost Breakdown:*\n"
        f"• Items Subtotal: `{subtotal} ETB`\n"
        f"{fee_lines}"
        f"• *Total Order Price:* `{total} ETB`\n\n"
        f"✨ *Required 50% Advance Deposit:* 👉 *`{deposit} ETB`*\n"
        f"_(Remaining `{remaining} ETB` paid upon completion/pickup)_\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "💳 *Transfer 50% Deposit to either account:*\n\n"
        f"🏦 *CBE (Commercial Bank of Ethiopia):*\n"
        f"`{config.PAYMENT_CBE_ACCOUNT}`\n"
        f"Account Name: *{config.PAYMENT_CBE_NAME}*\n\n"
        f"📱 *Telebirr:*\n"
        f"`{config.PAYMENT_TELEBIRR}`\n"
        f"Account Name: *{config.PAYMENT_TELEBIRR_NAME}*\n\n"
        "📸 *Please transfer the deposit and upload your screenshot or transaction receipt photo below:*"
    )

    await message.answer(payment_prompt, parse_mode="Markdown", reply_markup=get_cancel_keyboard())

# -------------------------------------------------------------
# PAYMENT RECEIPT HANDLER & OWNER NOTIFICATION
# -------------------------------------------------------------

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
            "⚠️ Please upload a photo or screenshot of your payment receipt (from Telebirr or CBE Mobile Banking).\n\n"
            "If you need help or wish to cancel, tap *❌ Cancel*.",
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

    # Save to cloud PostgreSQL or SQLite database
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
        has_attachment=bool(data.get('file_id')),
        payment_screenshot_file_id=screenshot_file_id,
        payment_screenshot_filename=temp_filename,
        payment_status="pending_review",
        status="pending",
        phone=data.get('phone', ''),
        recipient_name=data.get('recipient_name', user.full_name)
    )

    # 1. Customer confirmation
    loc_disp = data.get('delivery_location', '')
    if data.get('delivery_maps_url'):
        loc_disp += f" — [🗺️ GPS Pin]({data.get('delivery_maps_url')})"

    phone_disp = data.get('phone', 'N/A')
    recip_disp = data.get('recipient_name', user.full_name)

    customer_msg = (
        "🎉 *Thank you! Your order & deposit receipt have been received!* 💛\n\n"
        f"🔖 *Order Code:* `{order_code}`\n\n"
        "📋 *Summary:*\n"
        f"• *Items:* {data.get('items')}\n"
        f"• *Total Price:* `{data.get('total_price', 0)} ETB`\n"
        f"• *50% Deposit Submitted:* `{data.get('deposit_amount', 0)} ETB`\n"
        f"• *Deadline:* {data.get('deadline')}\n"
        f"• *Recipient:* {recip_disp}\n"
        f"• *Contact Phone:* `{phone_disp}`\n"
        f"• *Delivery:* {data.get('delivery_type')} ({loc_disp})\n\n"
        "🔍 *Status:* `Pending Review` (Verifying deposit receipt).\n"
        "Once approved by the owner, we will notify you immediately and begin production! ✨"
    )
    if config.ADMIN_USERNAME:
        customer_msg += f"\n\nQuestions? Chat with owner: @{config.ADMIN_USERNAME}"

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
