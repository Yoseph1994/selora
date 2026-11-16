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
import config

logger = logging.getLogger(__name__)
router = Router(name="portfolio_router")

PRODUCT_IMAGES_DIR = Path(__file__).resolve().parent.parent / "data" / "products_images"

def get_portfolio_card(index: int):
    items = database.get_portfolio_items()
    if not items:
        return None, None, None

    idx = index % len(items)
    item = items[idx]

    caption = (
        f"🌟 *{item['title']}*\n"
        f"🏷 *Category:* `{item.get('category', 'Custom Work')}`\n"
        "─────────────────────\n"
        f"{item.get('description', '')}\n"
        "─────────────────────\n"
        f"📸 *Showcase {idx + 1} of {len(items)}* · _Real Selora Prints Work_"
    )

    prev_idx = (idx - 1) % len(items)
    next_idx = (idx + 1) % len(items)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="◀ Prev", callback_data=f"port_nav:{prev_idx}"),
            InlineKeyboardButton(text=f"· {idx + 1}/{len(items)} ·", callback_data="noop"),
            InlineKeyboardButton(text="Next ▶", callback_data=f"port_nav:{next_idx}")
        ],
        [
            InlineKeyboardButton(text="🛍️ Order Custom Prints", callback_data="start_order")
        ],
        [
            InlineKeyboardButton(text="🏷 Browse Full Price List", callback_data="show_catalog"),
            InlineKeyboardButton(text="🎨 View Ready Designs", callback_data="view_samples")
        ]
    ])

    custom_url = (item.get("image_url") or "").strip()
    if custom_url.startswith(("http://", "https://")):
        return caption, custom_url, keyboard

    image_path = None
    clean_url = custom_url.split("?")[0]
    if clean_url.startswith("/product-images/"):
        fname = clean_url.replace("/product-images/", "")
        cand = PRODUCT_IMAGES_DIR / fname
        if cand.exists():
            image_path = cand

    if not image_path or not image_path.exists():
        image_path = PRODUCT_IMAGES_DIR / "stickers.png"

    return caption, FSInputFile(image_path), keyboard

@router.message(Command("portfolio"))
@router.message(Command("works"))
@router.message(F.text.in_(["🌟 Our Works / Portfolio", "🌟 የሰራናቸው ስራዎች", "🌟 Our Works", "🌟 Portfolio"]))
@router.callback_query(F.data == "show_portfolio")
async def show_portfolio_entry(event: types.Message | types.CallbackQuery):
    caption, img, keyboard = get_portfolio_card(0)
    if caption and img:
        if isinstance(event, types.CallbackQuery):
            try:
                await event.message.delete()
            except Exception:
                pass
            await event.message.answer_photo(
                photo=img,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
            await event.answer()
        else:
            await event.answer_photo(
                photo=img,
                caption=caption,
                parse_mode="Markdown",
                reply_markup=keyboard
            )
    else:
        text = "🌟 *Selora Prints Portfolio*\n\n_Showcase items will be uploaded soon! Tap '📝 Place an Order' to create your custom print._"
        if isinstance(event, types.CallbackQuery):
            await event.message.answer(text, parse_mode="Markdown")
            await event.answer()
        else:
            await event.answer(text, parse_mode="Markdown")

@router.callback_query(F.data.startswith("port_nav:"))
async def callback_portfolio_nav(callback: types.CallbackQuery):
    idx = int(callback.data.split(":")[1])
    caption, img, keyboard = get_portfolio_card(idx)
    if caption and img:
        try:
            await callback.message.edit_media(
                media=InputMediaPhoto(media=img, caption=caption, parse_mode="Markdown"),
                reply_markup=keyboard
            )
        except Exception as e:
            logger.warning(f"Could not edit portfolio media: {e}")
    await callback.answer()
