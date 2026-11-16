from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import config

router = Router(name="delivery_router")

DELIVERY_TEXT = (
    "╭─── 📍 Delivery & Pickup ───╮\n"
    "│\n"
    "│  *🏪 Store Pickup - Free*\n"
    "│  Ledeta (near Balcha), Addis Ababa\n"
    "│  Mon – Sat: 9:00 AM – 6:00 PM\n"
    "│\n"
    "│  *🚚 Doorstep Taxi Delivery*\n"
    "│  Fast via Yango / Feres / RIDE\n"
    "│  Driver fare (~300 – 1,000 ETB)\n"
    "│  Paid directly to driver on arrival\n"
    "│\n"
    "╰─────────────────────────╯\n\n"
    "💡 *Delivery Coordination:*\n"
    "To ensure accurate dispatch, your delivery method (Office Pickup vs. Taxi Delivery) is arranged directly once your custom items are printed and ready for pickup/delivery!\n\n"
    "_If you prefer to avoid the delivery fee, in-person pickup at our Ledeta office is completely free!_"
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
@router.message(F.text.in_(["📍 Delivery & Pickup", "📍 የማድረስ መረጃ", "📍 Delivery & Pickup / የማድረስ መረጃ"]))
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
