import logging
from typing import Optional
from aiogram import Router, F, types
from aiogram.filters import Command
from data import database
import config

logger = logging.getLogger(__name__)
router = Router(name="track_router")

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_track_order_keyboard(order: dict) -> Optional[InlineKeyboardMarkup]:
    status = order.get("status", "pending")
    pay_status = order.get("payment_status", "pending_review")
    order_code = order.get("order_code", "")

    buttons = []
    # If payment approved, allow managing/changing delivery
    if pay_status == "approved" or status in ("in_production", "ready_for_delivery", "completed"):
        buttons.append([
            InlineKeyboardButton(text="✏️ Change Delivery Details", callback_data=f"post_del:change:{order_code}")
        ])
    if config.ADMIN_USERNAME:
        buttons.append([
            InlineKeyboardButton(text="💬 Message Owner", url=f"https://t.me/{config.ADMIN_USERNAME}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None
    """Returns a visual status pipeline string."""
    if pay_status == "pending_review":
        return (
            "⏳ *Deposit Under Review*\n"
            "`● ○ ○`  Reviewing ▸ Printing ▸ Ready"
        )
    elif status in ("in_production",) or pay_status == "approved":
        return (
            "🎨 *In Production & Printing*\n"
            "`● ● ○`  Verified ▸ Printing ▸ Ready"
        )
    elif status == "completed":
        return (
            "🎉 *Ready for Pickup / Delivery*\n"
            "`● ● ●`  Verified ▸ Printed ▸ Ready"
        )
    elif status in ("cancelled",) or pay_status == "rejected":
        return "❌ *Cancelled / Payment Issue*"
    else:
        return f"📦 *Status:* {status.upper()}"

def render_status_card(order: dict) -> str:
    status = order.get("status", "pending")
    pay_status = order.get("payment_status", "pending_review")
    pipeline = _status_pipeline(status, pay_status)

    if pay_status == "pending_review":
        note = "Our team is verifying your payment. You'll be notified as soon as it's approved."
    elif status in ("in_production",) or pay_status == "approved":
        note = "Your deposit is verified and your items are currently being printed!"
    elif status == "completed":
        note = "Your order is ready! Head to Ledeta for pickup, or expect your Yango driver soon."
    elif status in ("cancelled",) or pay_status == "rejected":
        note = f"Please contact us for assistance: @{config.ADMIN_USERNAME}"
    else:
        note = "Order is being processed."

    return (
        "─────────────────────\n"
        f"🔖 *Order:* `{order['order_code']}`\n"
        "─────────────────────\n\n"
        f"{pipeline}\n\n"
        f"▸ *Items:* {order.get('items')}\n"
        f"▸ *Need by:* {order.get('deadline')}\n"
        f"▸ *Delivery:* {order.get('delivery_type')}\n"
        f"▸ *Placed:* {order.get('created_at')}\n\n"
        "─────────────────────\n"
        f"_{note}_"
    )

@router.message(Command("track"))
@router.message(F.text.in_(["🔍 Track My Order", "🔍 ትዕዛዝ ይከታተሉ", "🔍 Track My Order / ትዕዛዝ ይከታተሉ"]))
async def track_orders_handler(message: types.Message):
    text = message.text or ""
    parts = text.strip().split()

    # Direct code lookup: /track SP-1001
    if len(parts) > 1 and parts[1].upper().startswith("SP-"):
        code = parts[1].upper()
        order = database.get_order_by_code(code)
        if order:
            await message.answer(render_status_card(order), parse_mode="Markdown", reply_markup=get_track_order_keyboard(order))
        else:
            await message.answer(
                f"❌ Order `{code}` not found.\n\n"
                "_Double-check your order code, or tap_ *📝 Place an Order* _to start a new one._",
                parse_mode="Markdown"
            )
        return

    # Lookup by user ID
    user_orders = database.get_orders_by_user(message.from_user.id)
    if not user_orders:
        await message.answer(
            "─────────────────────\n"
            "       *No Active Orders*\n"
            "─────────────────────\n\n"
            "You haven't placed an order yet under this account.\n\n"
            "▸ Tap *📝 Place an Order* to start a new one\n"
            "▸ Or type `/track SP-XXXX` if you have an order code",
            parse_mode="Markdown"
        )
        return

    latest = user_orders[0]
    reply_text = "📦 *Your Latest Order*\n\n" + render_status_card(latest)

    if len(user_orders) > 1:
        reply_text += f"\n\n_({len(user_orders)} orders total - type `/track SP-XXXX` to view another)_"

    await message.answer(reply_text, parse_mode="Markdown", reply_markup=get_track_order_keyboard(latest))
