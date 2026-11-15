import os
import logging
from pathlib import Path
from datetime import datetime
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

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
    waiting_for_items = State()
    waiting_for_deadline = State()
    waiting_for_delivery_type = State()
    waiting_for_location = State()
    waiting_for_files_or_notes = State()
    waiting_for_payment_receipt = State()

@router.message(Command("cancel"))
@router.message(F.text == "❌ Cancel")
async def cancel_order(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state is None:
        await message.answer(
            "There is no active order in progress.",
            reply_markup=get_main_menu_keyboard()
        )
        return

    await state.clear()
    await message.answer(
        "❌ Order process cancelled. You can start anytime with the menu below!",
        reply_markup=get_main_menu_keyboard()
    )

def get_deadline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚡ Urgent: in 2 days (+200 ETB)", callback_data="dl_choice:urgent_2_days")
        ],
        [
            InlineKeyboardButton(text="🗓 Standard: in 3-4 days", callback_data="dl_choice:standard_3_days"),
            InlineKeyboardButton(text="📅 Next Week", callback_data="dl_choice:next_week")
        ]
    ])

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
    await state.set_state(OrderFSM.waiting_for_items)
    await message.answer(
        "📱 *SELORA ORDER ASSISTANT*\n"
        "`[ 🟡 ⚪ ⚪ ⚪ ] Step 1 of 4: Select Items`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "1️⃣ *What items would you like to order and how many?*\n\n"
        "⚠️ *Minimum Order Quantities:*\n"
        "• Stickers: Min 15 pcs\n"
        "• Bookmarks: Min 2 pcs\n"
        "• Business Cards: Min 50 pcs\n"
        "• Polaroid Prints: Min 10 pcs\n"
        "• Sticker Posters: Min 10 pcs\n"
        "• Minibooks & Other Items: 1 pc\n\n"
        "_(e.g., 20 Stickers, 1 Mini Book (White), and 2 Bookmarks)_\n\n"
        "Type your items below (or tap *❌ Cancel* anytime):",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )

@router.callback_query(F.data == "start_order")
async def callback_start_order(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(OrderFSM.waiting_for_items)
    await callback.message.answer(
        "📱 *SELORA ORDER ASSISTANT*\n"
        "`[ 🟡 ⚪ ⚪ ⚪ ] Step 1 of 4: Select Items`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "1️⃣ *What items would you like to order and how many?*\n\n"
        "⚠️ *Minimum Order Quantities:*\n"
        "• Stickers: Min 15 pcs\n"
        "• Bookmarks: Min 2 pcs\n"
        "• Business Cards: Min 50 pcs\n"
        "• Polaroid Prints: Min 10 pcs\n"
        "• Sticker Posters: Min 10 pcs\n"
        "• Minibooks & Other Items: 1 pc\n\n"
        "_(e.g., 20 Stickers, 1 Mini Book (White), and 2 Bookmarks)_\n\n"
        "Type your items below:",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

@router.message(OrderFSM.waiting_for_items)
async def process_items(message: types.Message, state: FSMContext):
    if not message.text or message.text == "❌ Cancel":
        return
    await state.update_data(items=message.text.strip())
    await state.set_state(OrderFSM.waiting_for_deadline)
    await message.answer(
        "📱 *SELORA ORDER ASSISTANT*\n"
        "`[ 🟢 🟡 ⚪ ⚪ ] Step 2 of 4: Timing & Deadline`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "2️⃣ *When do you need your order by?* 🗓\n\n"
        "⏱ *Turnaround Policy:*\n"
        "• 🟢 *Standard:* 3+ days (regular price)\n"
        "• ⚡ *Urgent Rush:* In 2 days (*+200 ETB rush fee*)\n"
        "• ⛔ *Next-day (tomorrow):* Cannot be accepted due to drying & binding time.\n\n"
        "Tap an option below or type your deadline:",
        parse_mode="Markdown",
        reply_markup=get_deadline_keyboard()
    )

@router.callback_query(OrderFSM.waiting_for_deadline, F.data.startswith("dl_choice:"))
async def process_deadline_callback(callback: types.CallbackQuery, state: FSMContext):
    choice = callback.data.split(":")[1]
    if choice == "urgent_2_days":
        deadline = "⚡ Urgent Rush (in 2 days) [+200 ETB]"
        rush_fee = 200
    elif choice == "standard_3_days":
        deadline = "Standard (in 3-4 days)"
        rush_fee = 0
    else:
        deadline = "Next Week"
        rush_fee = 0

    await state.update_data(deadline=deadline, rush_fee=rush_fee)
    await state.set_state(OrderFSM.waiting_for_delivery_type)

    rush_note = " _(+200 ETB rush fee)_" if rush_fee > 0 else ""
    await callback.message.edit_text(f"✅ Selected Timing: *{deadline}*{rush_note}", parse_mode="Markdown")
    await callback.message.answer(
        "📱 *SELORA ORDER ASSISTANT*\n"
        "`[ 🟢 🟢 🟡 ⚪ ] Step 3 of 4: Delivery Method`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "3️⃣ *How would you like to receive your order?*\n\n"
        "• 🏪 *Free Store Pickup:* Ledeta Store\n"
        "• 🚚 *Yango Delivery:* Delivered across Addis Ababa (fee paid by you upon receipt)",
        parse_mode="Markdown",
        reply_markup=get_delivery_choice_keyboard()
    )
    await callback.answer()

@router.message(OrderFSM.waiting_for_deadline)
async def process_deadline(message: types.Message, state: FSMContext):
    if not message.text or message.text == "❌ Cancel":
        return

    text_lower = message.text.lower().strip()
    tomorrow_words = ["tomorrow", "tomorow", "nege", "ነገ", "today", "tonight", "ዛሬ", "1 day", "1day", "one day"]
    if any(w in text_lower for w in tomorrow_words):
        await message.answer(
            "⚠️ *Orders cannot be accepted for tomorrow!*\n\n"
            "Custom printing, binding, and drying require at least 48 hours.\n\n"
            "• Earliest possible: **In 2 days** (Urgent Rush, *+200 ETB fee*)\n"
            "• Standard turnaround: **3+ days** (regular pricing)\n\n"
            "Please select an option below or type a date at least 2 days away:",
            parse_mode="Markdown",
            reply_markup=get_deadline_keyboard()
        )
        return

    urgent_words = ["urgent", "rush", "2 days", "2days", "in 2 days", "2 ቀን", "ሁለት ቀን"]
    is_urgent = any(w in text_lower for w in urgent_words)
    rush_fee = 200 if is_urgent else 0
    deadline = message.text.strip()
    if is_urgent and "(+200 ETB)" not in deadline:
        deadline += " (⚡ Urgent: +200 ETB rush fee)"

    await state.update_data(deadline=deadline, rush_fee=rush_fee)
    await state.set_state(OrderFSM.waiting_for_delivery_type)
    await message.answer(
        "📱 *SELORA ORDER ASSISTANT*\n"
        "`[ 🟢 🟢 🟡 ⚪ ] Step 3 of 4: Delivery Method`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "3️⃣ *How would you like to receive your order?*\n\n"
        "• 🏪 *Free Store Pickup:* Ledeta Store\n"
        "• 🚚 *Yango Delivery:* Delivered across Addis Ababa (fee paid by you upon receipt)",
        parse_mode="Markdown",
        reply_markup=get_delivery_choice_keyboard()
    )

@router.callback_query(OrderFSM.waiting_for_delivery_type, F.data.startswith("delivery_choice:"))
async def process_delivery_choice(callback: types.CallbackQuery, state: FSMContext):
    choice = callback.data.split(":")[1]
    if choice == "pickup":
        await state.update_data(
            delivery_type="Store Pickup (Ledeta - Free)",
            delivery_location="Ledeta Store"
        )
        await state.set_state(OrderFSM.waiting_for_files_or_notes)
        await callback.message.edit_text("✅ Selected: *Store Pickup (Ledeta - Free)*", parse_mode="Markdown")
        await callback.message.answer(
            "4️⃣ *Custom Files or Special Notes:*\n\n"
            "If your order requires custom photos/designs (e.g. Polaroid photos, custom Mug print, Sticker artwork), "
            "you can send the photo/document now, or type any special instructions.\n\n"
            "If you don't have custom files, just reply with *None* or *Skip*.",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
    else:
        await state.update_data(delivery_type="Yango Delivery")
        await state.set_state(OrderFSM.waiting_for_location)
        await callback.message.edit_text("✅ Selected: *Yango Delivery*", parse_mode="Markdown")
        await callback.message.answer(
            "📍 *Please provide your delivery location & contact phone number:*\n\n"
            "_(e.g., Bole Medhanialem next to Edna Mall, Phone: 0911XXXXXX)_",
            parse_mode="Markdown",
            reply_markup=get_cancel_keyboard()
        )
    await callback.answer()

@router.message(OrderFSM.waiting_for_location)
async def process_location(message: types.Message, state: FSMContext):
    if not message.text or message.text == "❌ Cancel":
        return
    await state.update_data(delivery_location=message.text.strip())
    await state.set_state(OrderFSM.waiting_for_files_or_notes)
    await message.answer(
        "4️⃣ *Custom Files or Special Notes:*\n\n"
        "If your order requires custom photos/designs (e.g. Polaroid photos, custom Mug print, Sticker artwork), "
        "you can send the photo/document now, or type any special instructions.\n\n"
        "If you don't have custom files, just reply with *None* or *Skip*.",
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )

@router.message(OrderFSM.waiting_for_files_or_notes)
async def process_files_or_notes(message: types.Message, state: FSMContext):
    if message.text == "❌ Cancel":
        return

    file_id = None
    file_type = None
    notes = "None"

    if message.photo:
        file_id = message.photo[-1].file_id
        file_type = "photo"
        notes = message.caption or "Photo attached"
    elif message.document:
        file_id = message.document.file_id
        file_type = "document"
        notes = message.caption or f"Document attached: {message.document.file_name}"
    elif message.text:
        notes = message.text.strip()

    await state.update_data(
        file_id=file_id,
        file_type=file_type,
        notes=notes
    )

    data = await state.get_data()
    rush_fee = data.get("rush_fee", 0)
    rush_line = "\n• ⚡ *Urgent Rush Fee:* `+200 ETB` (2-day turnaround)" if rush_fee > 0 else ""

    # Step 4: Pre-payment deposit instructions
    payment_prompt = (
        "📱 *SELORA ORDER ASSISTANT*\n"
        "`[ 🟢 🟢 🟢 🟡 ] Step 4 of 4: 50% Pre-Payment Deposit`\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        "📋 *Order Summary:*\n"
        f"• *Items:* {data.get('items')}\n"
        f"• *Need by:* {data.get('deadline')}{rush_line}\n"
        f"• *Delivery:* {data.get('delivery_type')} ({data.get('delivery_location')})\n"
        f"• *Notes/Files:* {data.get('notes')}\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "💳 *50% Advance Pre-Payment Required:*\n"
        f"• *CBE:* `{config.PAYMENT_CBE_ACCOUNT}` ({config.PAYMENT_CBE_NAME})\n"
        f"• *Telebirr:* `{config.PAYMENT_TELEBIRR}` ({config.PAYMENT_TELEBIRR_NAME})\n\n"
        "📸 *Please transfer the 50% deposit and upload your payment screenshot / transaction SMS receipt below:*"
    )

    await state.set_state(OrderFSM.waiting_for_payment_receipt)
    await message.answer(
        text=payment_prompt,
        parse_mode="Markdown",
        reply_markup=get_cancel_keyboard()
    )

@router.message(OrderFSM.waiting_for_payment_receipt)
async def process_payment_receipt(message: types.Message, state: FSMContext):
    if message.text == "❌ Cancel":
        await cancel_order(message, state)
        return

    # Check for photo or document screenshot
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

    # Generate placeholder order code to save receipt image
    temp_filename = f"receipt_{user.id}_{int(datetime.now().timestamp())}.jpg"
    receipt_local_path = RECEIPTS_DIR / temp_filename

    # Download receipt to local disk for web dashboard
    try:
        await message.bot.download(screenshot_file_id, destination=receipt_local_path)
    except Exception as e:
        logger.warning(f"Could not download receipt image locally: {e}")

    # Save to persistent database
    order_code = database.save_order(
        user_id=user.id,
        full_name=user.full_name,
        username=user.username,
        items=data.get('items', ''),
        deadline=data.get('deadline', ''),
        delivery_type=data.get('delivery_type', ''),
        delivery_location=data.get('delivery_location', ''),
        notes=data.get('notes', 'None'),
        has_attachment=bool(data.get('file_id')),
        payment_screenshot_file_id=screenshot_file_id,
        payment_screenshot_filename=temp_filename,
        payment_status="pending_review",
        status="pending"
    )

    # 1. Notify Customer
    customer_msg = (
        "🎉 *Thank you! Your order & deposit receipt have been received!* 💛\n\n"
        f"🔖 *Order Code:* `{order_code}`\n\n"
        "📋 *Summary:*\n"
        f"• *Items:* {data.get('items')}\n"
        f"• *Deadline:* {data.get('deadline')}\n"
        f"• *Delivery:* {data.get('delivery_type')} ({data.get('delivery_location')})\n\n"
        "🔍 *Status:* `Pending Approval` (We are verifying your 50% deposit receipt).\n"
        "Once verified, we will notify you immediately and begin production! ✨"
    )
    if config.ADMIN_USERNAME:
        customer_msg += f"\n\nNeed urgent assistance? Chat with owner: @{config.ADMIN_USERNAME}"

    await message.answer(customer_msg, parse_mode="Markdown", reply_markup=get_main_menu_keyboard())

    # 2. Notify Store Owner / Admin with Approval Buttons
    if config.ADMIN_CHAT_ID:
        try:
            rush_badge = "\n⚡ *PRIORITY:* URGENT 2-DAY RUSH (+200 ETB fee included)" if data.get("rush_fee", 0) > 0 else ""
            admin_text = (
                f"🚨 *NEW ORDER & PAYMENT SUBMITTED! — {order_code}*{rush_badge}\n"
                f"⏰ *Time:* {timestamp}\n"
                f"👤 *Customer:* [{user.full_name}](tg://user?id={user.id}) ({username_str})\n"
                f"🆔 *Telegram ID:* `{user.id}`\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                f"🏷 *Items:* {data.get('items')}\n"
                f"🗓 *Needed By:* {data.get('deadline')}\n"
                f"🚚 *Method:* {data.get('delivery_type')}\n"
                f"📍 *Location:* {data.get('delivery_location')}\n"
                f"📝 *Notes:* {data.get('notes')}\n"
                "━━━━━━━━━━━━━━━━━━━━\n"
                "💰 *Payment Receipt Attached Below.* Please verify and tap an action:"
            )

            approval_keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Approve Payment", callback_data=f"pay_approve:{order_code}"),
                    InlineKeyboardButton(text="❌ Reject", callback_data=f"pay_reject:{order_code}")
                ],
                [
                    InlineKeyboardButton(text="💬 DM Customer", url=f"tg://user?id={user.id}")
                ]
            ])

            # Send photo receipt to admin with buttons
            await message.bot.send_photo(
                chat_id=config.ADMIN_CHAT_ID,
                photo=screenshot_file_id,
                caption=admin_text,
                parse_mode="Markdown",
                reply_markup=approval_keyboard
            )

            # If customer also attached custom artwork/photos, forward that too
            if data.get("file_id"):
                if data.get("file_type") == "photo":
                    await message.bot.send_photo(
                        chat_id=config.ADMIN_CHAT_ID,
                        photo=data.get("file_id"),
                        caption=f"🎨 Custom artwork/photo for {order_code}"
                    )
                elif data.get("file_type") == "document":
                    await message.bot.send_document(
                        chat_id=config.ADMIN_CHAT_ID,
                        document=data.get("file_id"),
                        caption=f"🎨 Custom artwork document for {order_code}"
                    )
        except Exception as e:
            logger.error(f"Failed to forward payment alert to ADMIN_CHAT_ID: {e}")

    await state.clear()
