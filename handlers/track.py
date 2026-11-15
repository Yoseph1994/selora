import logging
from aiogram import Router, F, types
from aiogram.filters import Command
from data import database
import config

logger = logging.getLogger(__name__)
router = Router(name="track_router")

def render_status_card(order: dict) -> str:
    status = order.get("status", "pending")
    pay_status = order.get("payment_status", "pending_review")

    if pay_status == "pending_review":
        progress = "⏳ *Status:* `50% Deposit Under Review`\n[ 🟡 Deposit Review ] ➔ [ ⚪ Printing ] ➔ [ ⚪ Ready ]"
        desc = "Our team is verifying your payment screenshot. You will receive an alert once approved!"
    elif status == "in_production" or pay_status == "approved":
        progress = "🎨 *Status:* `In Production & Printing`\n[ 🟢 Deposit Verified ] ➔ [ 🟡 Printing ] ➔ [ ⚪ Ready ]"
        desc = "Your 50% advance has been verified and your custom items are currently being printed!"
    elif status == "completed":
        progress = "🎉 *Status:* `Ready for Pickup / Out for Delivery`\n[ 🟢 Deposit Verified ] ➔ [ 🟢 Printed ] ➔ [ 🟢 Ready ]"
        desc = "Your order is ready! Please pick it up at Ledeta, or keep your phone ready for your Yango delivery driver."
    elif status == "cancelled" or pay_status == "rejected":
        progress = "❌ *Status:* `Cancelled / Payment Issue`"
        desc = f"Please contact the owner directly for assistance: @{config.ADMIN_USERNAME}"
    else:
        progress = f"📦 *Status:* `{status.upper()}`"
        desc = "Order is being processed."

    return (
        f"🔖 *Order Code:* `{order['order_code']}`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"{progress}\n\n"
        f"🏷 *Items:* {order.get('items')}\n"
        f"🗓 *Need by:* {order.get('deadline')}\n"
        f"🚚 *Delivery:* {order.get('delivery_type')} ({order.get('delivery_location')})\n"
        f"⏰ *Date Placed:* {order.get('created_at')}\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 {desc}\n"
        "💳 *Payment:* 50% deposit required in advance; remaining 50% upon pickup/receipt."
    )

@router.message(Command("track"))
@router.message(F.text == "🔍 Track My Order")
async def track_orders_handler(message: types.Message):
    # Check if user specified a specific code: /track SP-1001
    parts = message.text.strip().split()
    if len(parts) > 1 and parts[1].upper().startswith("SP-"):
        code = parts[1].upper()
        order = database.get_order_by_code(code)
        if order:
            await message.answer(render_status_card(order), parse_mode="Markdown")
            return
        else:
            await message.answer(f"❌ Order `{code}` not found. Please check your order code.", parse_mode="Markdown")
            return

    # Look up user's recent orders from SQLite
    user_orders = database.get_orders_by_user(message.from_user.id)
    if not user_orders:
        await message.answer(
            "📦 *No Active Orders Found*\n\n"
            "You haven't placed an order yet, or your order was under another account.\n\n"
            "• Tap *📝 Place an Order* to start a new order.\n"
            "• Or if you have an Order Code, type `/track <CODE>` (e.g. `/track SP-1001`).",
            parse_mode="Markdown"
        )
        return

    # Show the latest order first
    latest = user_orders[0]
    reply_text = "📦 *Your Most Recent Order:*\n\n" + render_status_card(latest)

    if len(user_orders) > 1:
        reply_text += f"\n\n_(You have {len(user_orders)} orders in total. To view another, type `/track SP-XXXX`)_"

    await message.answer(reply_text, parse_mode="Markdown")

