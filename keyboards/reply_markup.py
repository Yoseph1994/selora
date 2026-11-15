from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
import config

def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Persistent bottom reply keyboard."""
    keyboard = [
        [
            KeyboardButton(text="🏷 Products & Prices"),
            KeyboardButton(text="🎨 Ready Designs")
        ],
        [
            KeyboardButton(text="📝 Place an Order"),
            KeyboardButton(text="🔍 Track My Order")
        ],
        [
            KeyboardButton(text="📍 Delivery & Pickup"),
            KeyboardButton(text="💬 Ask a Question")
        ],
        [
            KeyboardButton(text="📞 Contact Owner")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder="Choose an option or type a question..."
    )

def get_catalog_inline_keyboard() -> InlineKeyboardMarkup:
    """Inline keyboard attached to catalog messages."""
    buttons = [
        [
            InlineKeyboardButton(text="📝 Place an Order", callback_data="start_order"),
            InlineKeyboardButton(text="🖼 View Designs", callback_data="view_samples")
        ],
        [
            InlineKeyboardButton(text="📍 Delivery Info", callback_data="show_delivery"),
            InlineKeyboardButton(text="💬 Ask a Question", callback_data="ask_question_prompt")
        ]
    ]
    if config.ADMIN_USERNAME:
        buttons.append([
            InlineKeyboardButton(text="💛 Chat with Owner", url=f"https://t.me/{config.ADMIN_USERNAME}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_delivery_choice_keyboard() -> InlineKeyboardMarkup:
    """Delivery method selection keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏪 Store Pickup — Ledeta (Free)", callback_data="delivery_choice:pickup")
        ],
        [
            InlineKeyboardButton(text="🚚 Yango / Feres / RIDE Delivery", callback_data="delivery_choice:yango")
        ],
        [
            InlineKeyboardButton(text="✕ Cancel Order", callback_data="cancel_order")
        ]
    ])

def get_order_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Order confirm/cancel keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✓ Submit Order", callback_data="confirm_order"),
            InlineKeyboardButton(text="✕ Cancel", callback_data="cancel_order")
        ]
    ])

def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    """Single-button cancel keyboard for form steps."""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Cancel")]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
