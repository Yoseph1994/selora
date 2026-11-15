import os
import logging
from pathlib import Path
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

CATALOG_TEXT = (
    "💛 *Welcome to Selora Prints!*\n"
    "Thanks for messaging us! Here's our complete price list:\n\n"
    "🏷 *Stickers:* 20 birr\n"
    "🔖 *Bookmarks:* 50 birr\n"
    "💼 *Business cards:* 10 birr\n"
    "📓 *Mini notebook:* 200 birr\n"
    "📔 *Notebook:* 500 birr\n"
    "📖 *Minibook:* 600 birr\n"
    "📸 *Polaroid prints:* Available upon request\n"
    "☕ *Mug:* 1500 birr\n"
    "🧩 *Puzzle:* 1500 birr\n\n"
    "🟢 *STICKER POSTER*\n"
    "_(Peel & stick: wall, glass, smooth surface)_\n"
    "• *A5* = 40 birr\n"
    "• *A4* = 70 birr\n"
    "_(Minimum order: 10 pieces)_\n\n"
    "✨ *Tap below to browse visual design cards or place an order!*"
)

def get_product_card(index: int):
    products = database.get_products_data().get("products", [])
    if not products:
        return None, None, None

    idx = index % len(products)
    p = products[idx]

    min_text = f"\n⚠️ *Minimum Order:* `{p['min_order']} pieces`" if "min_order" in p else ""
    price_val = f"`{p['price']} ETB` {p.get('unit', '')}" if p.get("price") is not None else "`Custom / Quote`"

    caption = (
        f"{p['name']}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 *Price:* {price_val}{min_text}\n"
        f"📝 *Details:* {p.get('description', '')}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"🗂 *Item {idx + 1} of {len(products)}*"
    )

    prev_idx = (idx - 1) % len(products)
    next_idx = (idx + 1) % len(products)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="◀ Prev", callback_data=f"cat_nav:{prev_idx}"),
            InlineKeyboardButton(text=f"• {idx + 1}/{len(products)} •", callback_data="noop"),
            InlineKeyboardButton(text="Next ▶", callback_data=f"cat_nav:{next_idx}")
        ],
        [
            InlineKeyboardButton(text=f"🛍️ Order {p['name'].split()[1] if len(p['name'].split()) > 1 else p['name']}", callback_data=f"order_this:{p['id']}")
        ],
        [
            InlineKeyboardButton(text="📋 Full Price List", callback_data="show_catalog"),
            InlineKeyboardButton(text="📍 Delivery Info", callback_data="show_delivery")
        ]
    ])

    image_path = PRODUCT_IMAGES_DIR / f"{p['id']}.png"
    if not image_path.exists():
        image_path = PRODUCT_IMAGES_DIR / "stickers.png"

    return caption, FSInputFile(image_path), keyboard

@router.message(Command("catalog"))
@router.message(F.text == "🏷 Products & Prices")
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
    prod_id = callback.data.split(":")[1]
    products = database.get_products_data().get("products", [])
    prod = next((p for p in products if p["id"] == prod_id), None)

    item_name = prod["name"] if prod else "Custom item"
    min_ord = prod.get("min_order", 1) if prod else 1

    await state.clear()
    await state.set_state(OrderFSM.waiting_for_items)

    prompt = (
        f"💛 *Ordering {item_name}*\n\n"
        f"1️⃣ *How many would you like to order?*\n"
        f"_(e.g., {min_ord} or more)_\n\n"
        "Type your quantity below:"
    )

    await callback.message.answer(prompt, parse_mode="Markdown", reply_markup=get_cancel_keyboard())
    await callback.answer()

@router.callback_query(F.data == "noop")
async def callback_noop(callback: types.CallbackQuery):
    await callback.answer()
