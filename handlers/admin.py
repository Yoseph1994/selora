import os
import logging
from pathlib import Path
from datetime import datetime
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from data import database
import config

logger = logging.getLogger(__name__)
router = Router(name="admin_router")

def is_admin(user_id: int) -> bool:
    if not config.ADMIN_CHAT_ID:
        return False
    return str(user_id) == str(config.ADMIN_CHAT_ID)

@router.callback_query(F.data.startswith("pay_approve:"))
async def handle_payment_approval(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("🔒 Admin only action.", show_alert=True)
        return

    order_code = callback.data.split(":")[1]
    order = database.get_order_by_code(order_code)
    if not order:
        await callback.answer("Order not found.", show_alert=True)
        return

    # Update DB
    database.update_order_payment(order_code, payment_status="approved", order_status="in_production")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Update Admin Caption
    new_caption = (
        callback.message.caption + f"\n\n✅ *PAYMENT APPROVED* by {callback.from_user.full_name} at {timestamp}\n"
        "Status: `In Production`"
    )
    await callback.message.edit_caption(
        caption=new_caption,
        parse_mode="Markdown",
        reply_markup=None
    )

    # Notify Customer
    try:
        customer_msg = (
            "🎉 *Payment Verified & Order Confirmed!* 💛\n\n"
            f"🔖 *Order Code:* `{order_code}`\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            f"🏷 *Items:* {order.get('items')}\n"
            f"🗓 *Deadline:* {order.get('deadline')}\n"
            f"🚚 *Delivery:* {order.get('delivery_type')} ({order.get('delivery_location')})\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "✅ *Your 50% deposit has been approved!* We have officially started production on your order.\n\n"
            "We will send you an update as soon as your items are printed and ready for pickup/delivery! 🙏"
        )
        await callback.bot.send_message(
            chat_id=order["user_id"],
            text=customer_msg,
            parse_mode="Markdown"
        )
        await callback.answer("✅ Order approved and customer notified!")
    except Exception as e:
        logger.error(f"Failed to notify customer {order['user_id']}: {e}")
        await callback.answer("✅ Order approved (could not notify customer chat).")

@router.callback_query(F.data.startswith("pay_reject:"))
async def handle_payment_rejection(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("🔒 Admin only action.", show_alert=True)
        return

    order_code = callback.data.split(":")[1]
    order = database.get_order_by_code(order_code)
    if not order:
        await callback.answer("Order not found.", show_alert=True)
        return

    # Update DB
    database.update_order_payment(order_code, payment_status="rejected", order_status="payment_rejected")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")

    # Update Admin Caption
    new_caption = (
        callback.message.caption + f"\n\n❌ *PAYMENT REJECTED* by {callback.from_user.full_name} at {timestamp}"
    )
    await callback.message.edit_caption(
        caption=new_caption,
        parse_mode="Markdown",
        reply_markup=None
    )

    # Notify Customer
    try:
        owner_link = f"@{config.ADMIN_USERNAME}" if config.ADMIN_USERNAME else "our team"
        customer_msg = (
            "⚠️ *Payment Receipt Notice — Selora Prints*\n\n"
            f"🔖 *Order Code:* `{order_code}`\n\n"
            "We were unable to verify your 50% deposit payment screenshot.\n\n"
            "Possible reasons:\n"
            "• Transaction details or amount are unreadable\n"
            "• Payment has not appeared in our account yet\n\n"
            f"Please contact {owner_link} directly or resubmit with a clear confirmation receipt."
        )
        await callback.bot.send_message(
            chat_id=order["user_id"],
            text=customer_msg,
            parse_mode="Markdown"
        )
        await callback.answer("❌ Payment rejected and customer informed.")
    except Exception as e:
        logger.error(f"Failed to notify customer: {e}")
        await callback.answer("❌ Rejected.")

@router.message(Command("admin"))
async def admin_dashboard_menu(message: types.Message):
    """Interactive Admin Dashboard menu on Telegram."""
    if not is_admin(message.from_user.id):
        await message.answer("🔒 This menu is only available to the store owner.")
        return

    stats = database.get_stats()
    menu_text = (
        "👑 *Selora Prints — Owner Control Center*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 *Total Orders:* `{stats['total_orders']}`\n"
        f"⏳ *Pending 50% Review:* `{stats['pending_approvals']}`\n"
        f"🎨 *In Production:* `{stats['approved_orders']}`\n"
        f"✅ *Completed:* `{stats['completed_orders']}`\n"
        f"👥 *Total Customers:* `{stats['total_customers']}`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Choose an action below or open the Web Dashboard at `http://localhost:8000`:"
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📦 Recent Orders", callback_data="admin_view_orders"),
            InlineKeyboardButton(text="📊 Full Stats", callback_data="admin_view_stats")
        ],
        [
            InlineKeyboardButton(text="📢 Broadcast Promo", callback_data="admin_start_broadcast"),
            InlineKeyboardButton(text="📥 Export Excel (CSV)", callback_data="admin_export_data")
        ]
    ])

    await message.answer(menu_text, parse_mode="Markdown", reply_markup=keyboard)

@router.callback_query(F.data == "admin_view_orders")
async def cb_admin_orders(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Admin only.", show_alert=True)
        return
    orders = database.get_recent_orders(limit=8)
    if not orders:
        await callback.message.answer("📦 No orders recorded yet.")
        await callback.answer()
        return

    text = "📦 *Recent Orders:*\n━━━━━━━━━━━━━━━━━━━━\n\n"
    for o in orders:
        pay_badge = "⏳ Review Pending" if o.get('payment_status') == 'pending_review' else f"✅ {o.get('payment_status', '').upper()}"
        text += (
            f"🔖 *{o['order_code']}* — `{o['status'].upper()}`\n"
            f"💳 *Payment:* {pay_badge}\n"
            f"👤 *Customer:* {o['full_name']} (@{o['username'] or 'no_user'})\n"
            f"🏷 *Items:* {o['items']}\n"
            f"🗓 *Need by:* {o['deadline']}\n"
            f"👉 [Message Customer](tg://user?id={o['user_id']})\n"
            "────────────────────\n"
        )
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin_view_stats")
async def cb_admin_stats(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Admin only.", show_alert=True)
        return
    stats = database.get_stats()
    text = (
        "📊 *Selora Prints — Business Statistics*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 *Total Orders Received:* `{stats['total_orders']}`\n"
        f"⏳ *Pending Payment Approvals:* `{stats['pending_approvals']}`\n"
        f"🎨 *In Production:* `{stats['approved_orders']}`\n"
        f"✅ *Completed Orders:* `{stats['completed_orders']}`\n"
        f"👥 *Total Registered Customers:* `{stats['total_customers']}`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "Manage dynamically at `http://localhost:8000`!"
    )
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()

@router.callback_query(F.data == "admin_start_broadcast")
async def cb_admin_broadcast(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        await callback.answer("Admin only.", show_alert=True)
        return
    customer_ids = database.get_all_customers_user_ids()
    await state.set_state(BroadcastFSM.waiting_for_message)
    await callback.message.answer(
        f"📢 *Broadcast Announcement*\n\n"
        f"Recipients: `{len(customer_ids)}` customers.\n\n"
        "Send your message text or photo below (or `/cancel` to abort):",
        parse_mode="Markdown"
    )
    await callback.answer()

@router.callback_query(F.data == "admin_export_data")
async def cb_admin_export(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Admin only.", show_alert=True)
        return
    temp_csv = Path(__file__).resolve().parent.parent / "data" / "selora_orders_export.csv"
    try:
        database.export_orders_to_csv(temp_csv)
        document = FSInputFile(temp_csv, filename="selora_orders.csv")
        await callback.message.answer_document(
            document=document,
            caption="📊 Selora Prints orders export (CSV) ready for Excel / Google Sheets!"
        )
    except Exception as e:
        logger.error(f"Failed to export CSV: {e}")
        await callback.message.answer(f"❌ Failed to export: {e}")
    finally:
        if temp_csv.exists():
            try:
                os.remove(temp_csv)
            except Exception:
                pass
    await callback.answer()

@router.message(Command("orders"))
async def admin_orders(message: types.Message):
    """View recent orders with status badges (Admin only)."""
    if not is_admin(message.from_user.id):
        await message.answer("🔒 This command is only available to the store owner.")
        return

    orders = database.get_recent_orders(limit=10)
    if not orders:
        await message.answer("📦 No orders recorded yet.")
        return

    text = "📦 *Recent Orders (Last 10):*\n━━━━━━━━━━━━━━━━━━━━\n\n"
    for o in orders:
        pay_badge = "⏳ Review Pending" if o.get('payment_status') == 'pending_review' else f"✅ {o.get('payment_status', '').upper()}"
        text += (
            f"🔖 *{o['order_code']}* — `{o['status'].upper()}`\n"
            f"💳 *Payment:* {pay_badge}\n"
            f"👤 *Customer:* {o['full_name']} (@{o['username'] or 'no_user'})\n"
            f"🏷 *Items:* {o['items']}\n"
            f"🗓 *Need by:* {o['deadline']}\n"
            f"🚚 *Delivery:* {o['delivery_type']}\n"
            f"⏰ *Date:* {o['created_at']}\n"
            f"👉 [Message Customer](tg://user?id={o['user_id']})\n"
            "────────────────────\n"
        )

    await message.answer(text, parse_mode="Markdown")

@router.message(Command("stats"))
async def admin_stats(message: types.Message):
    """View store performance statistics (Admin only)."""
    if not is_admin(message.from_user.id):
        await message.answer("🔒 This command is only available to the store owner.")
        return

    stats = database.get_stats()
    text = (
        "📊 *Selora Prints — Business Statistics*\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 *Total Orders Received:* `{stats['total_orders']}`\n"
        f"⏳ *Pending Payment Approvals:* `{stats['pending_approvals']}`\n"
        f"🎨 *Approved / In Production:* `{stats['approved_orders']}`\n"
        f"✅ *Completed Orders:* `{stats['completed_orders']}`\n"
        f"👥 *Total Registered Customers:* `{stats['total_customers']}`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "💡 *Tip:* Open the Web Dashboard at `http://localhost:8000` to manage orders and prices dynamically!"
    )
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("export"))
async def admin_export_csv(message: types.Message):
    """Export all orders to a CSV file and send to admin."""
    if not is_admin(message.from_user.id):
        await message.answer("🔒 This command is only available to the store owner.")
        return

    temp_csv = Path(__file__).resolve().parent.parent / "data" / "selora_orders_export.csv"
    try:
        database.export_orders_to_csv(temp_csv)
        document = FSInputFile(temp_csv, filename="selora_orders.csv")
        await message.answer_document(
            document=document,
            caption="📊 Here is your full orders spreadsheet (CSV). You can open it in Microsoft Excel or Google Sheets!"
        )
    except Exception as e:
        logger.error(f"Failed to export CSV: {e}")
        await message.answer(f"❌ Failed to export orders: {e}")
    finally:
        if temp_csv.exists():
            try:
                os.remove(temp_csv)
            except Exception:
                pass

# Broadcast System
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

class BroadcastFSM(StatesGroup):
    waiting_for_message = State()
    waiting_for_confirmation = State()

@router.message(Command("broadcast"))
async def admin_broadcast_start(message: types.Message, state: FSMContext):
    """Start broadcast announcement flow (Admin only)."""
    if not is_admin(message.from_user.id):
        await message.answer("🔒 This command is only available to the store owner.")
        return

    customer_ids = database.get_all_customers_user_ids()
    await state.set_state(BroadcastFSM.waiting_for_message)
    await message.answer(
        f"📢 *Broadcast Announcement Tool*\n\n"
        f"You have `{len(customer_ids)}` registered customer(s) in your database.\n\n"
        "Send the announcement text (or photo with caption) you want to broadcast.\n\n"
        "_(Send `/cancel` to abort)_",
        parse_mode="Markdown"
    )

@router.message(BroadcastFSM.waiting_for_message)
async def admin_broadcast_preview(message: types.Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Broadcast cancelled.")
        return

    photo_id = message.photo[-1].file_id if message.photo else None
    text_content = message.caption or message.text or ""

    if not photo_id and not text_content:
        await message.answer("Please send some text or a photo.")
        return

    await state.update_data(photo_id=photo_id, text_content=text_content)
    await state.set_state(BroadcastFSM.waiting_for_confirmation)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚀 Send to All Customers", callback_data="broadcast_confirm"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="broadcast_cancel")
        ]
    ])

    await message.answer("📋 *Broadcast Preview Above.* Are you sure you want to send this to all customers?", parse_mode="Markdown", reply_markup=keyboard)

@router.callback_query(BroadcastFSM.waiting_for_confirmation, F.data == "broadcast_confirm")
async def admin_broadcast_send(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    customer_ids = database.get_all_customers_user_ids()

    await callback.message.edit_text("⏳ Sending broadcast to customers...")

    sent_count = 0
    failed_count = 0

    for uid in customer_ids:
        try:
            if data.get("photo_id"):
                await callback.bot.send_photo(
                    chat_id=uid,
                    photo=data["photo_id"],
                    caption=data.get("text_content", "")
                )
            else:
                await callback.bot.send_message(
                    chat_id=uid,
                    text=data.get("text_content", "")
                )
            sent_count += 1
        except Exception:
            failed_count += 1

    await callback.message.answer(
        f"✅ *Broadcast Finished!*\n\n"
        f"• Successfully sent: `{sent_count}`\n"
        f"• Failed/Blocked: `{failed_count}`",
        parse_mode="Markdown"
    )
    await state.clear()
    await callback.answer()

@router.callback_query(BroadcastFSM.waiting_for_confirmation, F.data == "broadcast_cancel")
async def admin_broadcast_cancel_cb(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("❌ Broadcast cancelled.")
    await callback.answer()
