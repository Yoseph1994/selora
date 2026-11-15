import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import (
    FSInputFile,
    InputMediaPhoto,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext

from data import database
from handlers.order import OrderFSM, get_cancel_keyboard
from keyboards.reply_markup import get_catalog_inline_keyboard, get_main_menu_keyboard
import config

logger = logging.getLogger(__name__)
router = Router(name="catalog_router")

PRODUCT_IMAGES_DIR = Path(__file__).resolve().parent.parent / "data" / "products_images"
DESIGNS_IMAGES_DIR = Path(__file__).resolve().parent.parent / "data" / "designs_images"

CATALOG_TEXT = (
    "╭─── 🏷 Selora Price List ───╮\n"
    "│\n"
    "│  *Stickers* — 20 ETB  _(min 15)_\n"
    "│  *Bookmarks* — 50 ETB  _(min 2)_\n"
    "│  *Business Cards* — 10 ETB  _(min 50)_\n"
    "│  *Polaroids* — Quote  _(min 10)_\n"
    "│  *Mini Notebook* — 200 ETB\n"
    "│  *Notebook* — 500 ETB\n"
    "│\n"
    "│  *Photo Books & Minibooks*\n"
    "│  ▸ Mini White — 600 ETB\n"
    "│  ▸ Mini Black — 700 ETB\n"
    "│  ▸ Medium — 800 ETB\n"
    "│  ▸ A5 — 1,000 ETB\n"
    "│  ▸ A4 Luxury — 1,500 ETB\n"
    "│\n"
    "│  *Custom Mug* — 1,500 ETB\n"
    "│  *Photo Puzzle* — 1,500 ETB\n"
    "│\n"
    "│  *Sticker Posters*\n"
    "│  ▸ A5 — 40 ETB  _(min 10)_\n"
    "│  ▸ A4 — 70 ETB  _(min 10)_\n"
    "│\n"
    "╰─────────────────────────╯\n\n"
    "⏱ *Turnaround*\n"
    "▸ Standard: 3+ days\n"
    "▸ Urgent Rush (2 days): +200 ETB\n"
    "▸ Next-day: unavailable (drying time)\n\n"
    "_Tap below to browse designs or start an order._"
)

def get_product_card(index: int):
    products = database.get_products_data().get("products", [])
    if not products:
        return None, None, None

    idx = index % len(products)
    p = products[idx]

    min_text = f"\n▸ *Min Order:* {p['min_order']} pcs" if "min_order" in p else ""
    price_val = f"{p['price']} ETB {p.get('unit', '')}" if p.get("price") is not None else "Custom Quote"

    caption = (
        f"*{p['name']}*\n"
        "─────────────────────\n"
        f"▸ *Price:* {price_val}{min_text}\n"
        f"▸ {p.get('description', '')}\n"
        "─────────────────────\n"
        f"_{idx + 1} of {len(products)}_"
    )

    prev_idx = (idx - 1) % len(products)
    next_idx = (idx + 1) % len(products)

    clean_short_name = p['name'].split()[1] if len(p['name'].split()) > 1 else p['name']

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="◀ Prev", callback_data=f"cat_nav:{prev_idx}"),
            InlineKeyboardButton(text=f"· {idx + 1}/{len(products)} ·", callback_data="noop"),
            InlineKeyboardButton(text="Next ▶", callback_data=f"cat_nav:{next_idx}")
        ],
        [
            InlineKeyboardButton(text=f"🛒 Order {clean_short_name}", callback_data=f"order_this:{p['id']}")
        ],
        [
            InlineKeyboardButton(text="📋 Full Price List", callback_data="show_catalog"),
            InlineKeyboardButton(text="📍 Delivery Info", callback_data="show_delivery")
        ]
    ])

    image_path = None
    # 1. Check if image_url points to a local file
    custom_url = p.get("image_url", "").split("?")[0]
    if custom_url.startswith("/product-images/"):
        fname = custom_url.replace("/product-images/", "")
        cand = PRODUCT_IMAGES_DIR / fname
        if cand.exists():
            image_path = cand

    # 2. Check standard extensions by product ID
    if not image_path:
        for ext in [".png", ".jpg", ".jpeg", ".webp"]:
            cand = PRODUCT_IMAGES_DIR / f"{p['id']}{ext}"
            if cand.exists():
                image_path = cand
                break

    # 3. Fallback to default banner
    if not image_path or not image_path.exists():
        image_path = PRODUCT_IMAGES_DIR / "stickers.png"

    return caption, FSInputFile(image_path), keyboard

@router.message(Command("catalog"))
@router.message(F.text.in_(["🏷 Products & Prices", "🏷 እቃዎች እና ዋጋ", "🏷 Products & Prices / እቃዎች እና ዋጋ"]))
async def show_catalog_overview(message: types.Message):
    """Show interactive visual product browser."""
    caption, image_file, keyboard = get_product_card(0)
    if caption and image_file:
        await message.answer_photo(
            photo=image_file,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    else:
        await message.answer(
            text=CATALOG_TEXT,
            parse_mode="Markdown",
            reply_markup=get_catalog_inline_keyboard()
        )

@router.callback_query(F.data.startswith("cat_nav:"))
async def callback_catalog_nav(callback: types.CallbackQuery):
    """Seamlessly flips to next/previous product card in place."""
    index = int(callback.data.split(":")[1])
    caption, image_file, keyboard = get_product_card(index)

    if caption and image_file:
        try:
            await callback.message.edit_media(
                media=InputMediaPhoto(
                    media=image_file,
                    caption=caption,
                    parse_mode="Markdown"
                ),
                reply_markup=keyboard
            )
        except Exception as e:
            logger.warning(f"Could not edit media: {e}")
    await callback.answer()

@router.callback_query(F.data == "show_catalog")
async def callback_show_catalog_list(callback: types.CallbackQuery):
    """Show textual catalog with quick action buttons."""
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        text=CATALOG_TEXT,
        parse_mode="Markdown",
        reply_markup=get_catalog_inline_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("order_this:"))
async def callback_order_specific_item(callback: types.CallbackQuery, state: FSMContext):
    """Customer clicked 'Order This Item' directly on the product card."""
    from handlers.order import show_quantity_stepper
    prod_id = callback.data.split(":")[1]
    await state.clear()
    sent = await callback.message.answer("_Preparing your order..._", parse_mode="Markdown")
    await show_quantity_stepper(sent, prod_id, state)
    await callback.answer()

@router.callback_query(F.data == "noop")
async def callback_noop(callback: types.CallbackQuery):
    await callback.answer()

# -------------------------------------------------------------
# DYNAMIC DESIGNS & SUB-PRODUCTS BROWSER
# -------------------------------------------------------------

def get_design_categories_keyboard() -> InlineKeyboardMarkup:
    cats = database.get_design_categories()
    buttons = []
    row = []
    for pid in cats.keys():
        name = pid.replace("_", " ").title()
        if "sticker" in pid:
            name = "🏷 Stickers"
        elif "bookmark" in pid:
            name = "🔖 Bookmarks"
        elif "card" in pid:
            name = "💼 Business Cards"
        elif "polaroid" in pid:
            name = "📸 Polaroids"
        elif "book" in pid:
            name = "📖 Photo Books"
        elif "mug" in pid:
            name = "☕ Custom Mugs"

        row.append(InlineKeyboardButton(text=name, callback_data=f"des_cat:{pid}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton(text="✦ Browse All Designs", callback_data="des_cat:all")])
    buttons.append([InlineKeyboardButton(text="◀ Back to Catalog", callback_data="show_catalog")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_design_card(index: int, product_id: Optional[str] = None):
    designs = database.get_designs(product_id=product_id if product_id != "all" else None)
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
        f"_{idx + 1} of {len(designs)}_"
    )

    prev_idx = (idx - 1) % len(designs)
    next_idx = (idx + 1) % len(designs)
    pid_param = product_id or "all"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="◀ Prev", callback_data=f"des_nav:{pid_param}:{prev_idx}"),
            InlineKeyboardButton(text=f"· {idx + 1}/{len(designs)} ·", callback_data="noop"),
            InlineKeyboardButton(text="Next ▶", callback_data=f"des_nav:{pid_param}:{next_idx}")
        ],
        [
            InlineKeyboardButton(text="🛒 Order This Design", callback_data=f"order_design:{d['id']}")
        ],
        [
            InlineKeyboardButton(text="📁 Other Collections", callback_data="view_design_cats"),
            InlineKeyboardButton(text="📸 Custom Art Info", callback_data="custom_upload_info")
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
        image_path = PRODUCT_IMAGES_DIR / "stickers.png"

    return caption, FSInputFile(image_path), keyboard

@router.message(Command("designs"))
@router.message(F.text.in_(["🖼 View Designs", "🎨 Ready Designs", "🎨 ዝግጁ ዲዛይኖች", "🎨 Ready Designs / ዝግጁ ዲዛይኖች"]))
@router.callback_query(F.data == "view_samples")
async def show_designs_entry(event: types.Message | types.CallbackQuery):
    text = (
        "╭─── 🎨 Ready Designs ───╮\n"
        "│\n"
        "│  Browse our curated artwork,\n"
        "│  styles, and templates — or\n"
        "│  upload your own photos.\n"
        "│\n"
        "╰─────────────────────────╯\n\n"
        "Choose a collection to browse:"
    )
    markup = get_design_categories_keyboard()
    if isinstance(event, types.CallbackQuery):
        try:
            await event.message.delete()
        except Exception:
            pass
        await event.message.answer(text, parse_mode="Markdown", reply_markup=markup)
        await event.answer()
    else:
        await event.answer(text, parse_mode="Markdown", reply_markup=markup)

@router.callback_query(F.data == "view_design_cats")
async def callback_view_design_cats(callback: types.CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(
        "╭─── 🎨 Ready Designs ───╮\n"
        "│\n"
        "│  Choose a collection below\n"
        "│  to preview styles & artwork.\n"
        "│\n"
        "╰─────────────────────────╯",
        parse_mode="Markdown",
        reply_markup=get_design_categories_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("des_cat:"))
async def callback_open_design_category(callback: types.CallbackQuery):
    cat = callback.data.split(":")[1]
    caption, img, keyboard = get_design_card(0, cat)
    if caption and img:
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer_photo(
            photo=img,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    else:
        await callback.answer("No designs found in this category yet!", show_alert=True)
    await callback.answer()

@router.callback_query(F.data.startswith("des_nav:"))
async def callback_design_nav(callback: types.CallbackQuery):
    parts = callback.data.split(":")
    cat = parts[1]
    idx = int(parts[2])
    caption, img, keyboard = get_design_card(idx, cat)
    if caption and img:
        try:
            await callback.message.edit_media(
                media=InputMediaPhoto(
                    media=img,
                    caption=caption,
                    parse_mode="Markdown"
                ),
                reply_markup=keyboard
            )
        except Exception as e:
            logger.warning(f"Could not edit design media: {e}")
    await callback.answer()

@router.callback_query(F.data.startswith("order_design:"))
async def callback_order_specific_design(callback: types.CallbackQuery, state: FSMContext):
    from handlers.order import show_quantity_stepper
    design_id = callback.data.split(":", 1)[1]
    d = database.get_design_by_id(design_id)
    if not d:
        await callback.answer("Design not found!", show_alert=True)
        return

    await state.clear()
    await state.update_data(
        design_mode="template",
        design_note=f"Ready Design: {d['title']} ({d['subproduct']})",
        selected_design_id=d["id"]
    )
    sent = await callback.message.answer(
        f"✓ *Selected:* {d['title']} ({d['subproduct']})\n"
        f"_Preparing your order for {d['product_name']}..._",
        parse_mode="Markdown"
    )
    await show_quantity_stepper(sent, d["product_id"], state)
    await callback.answer()

@router.callback_query(F.data == "custom_upload_info")
async def callback_custom_upload_info(callback: types.CallbackQuery):
    await callback.answer(
        "💡 You can upload your own custom photos/artwork! Start an order with '📝 Place an Order' and select 'Upload My Photo'.",
        show_alert=True
    )
