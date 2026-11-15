from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config

router = Router(name="delivery_router")

DELIVERY_TEXT = (
    "╭─── 📍 Delivery & Pickup ───╮\n"
    "│\n"
    "│  *Store Pickup — Free*\n"
    "│  Ledeta, Addis Ababa\n"
    "│  Pickup details shared once ready\n"
    "│\n"
    "│  *Yango Delivery — Addis Ababa*\n"
    "│  Door-to-door, fast & reliable\n"
    "│  Delivery fee paid to driver on arrival\n"
    "│\n"
    "╰─────────────────────────╯\n\n"
    "_Ready to order? Choose your delivery method during checkout._"
)

def get_delivery_action_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="📝 Place an Order", callback_data="start_order"),
            InlineKeyboardButton(text="🏷 View Catalog", callback_data="show_catalog")
        ]
    ]
    if config.ADMIN_USERNAME:
        buttons.append([
            InlineKeyboardButton(text="✉ Message Us", url=f"https://t.me/{config.ADMIN_USERNAME}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(Command("delivery"))
@router.message(F.text == "📍 Delivery & Pickup")
async def show_delivery(message: types.Message):
    await message.answer(
        text=DELIVERY_TEXT,
        parse_mode="Markdown",
        reply_markup=get_delivery_action_keyboard()
    )

@router.callback_query(F.data == "show_delivery")
async def callback_show_delivery(callback: types.CallbackQuery):
    await callback.message.edit_text(
        text=DELIVERY_TEXT,
        parse_mode="Markdown",
        reply_markup=get_delivery_action_keyboard()
    )
    await callback.answer()
