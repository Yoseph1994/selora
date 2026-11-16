from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
import config

def get_main_menu_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    """Persistent bottom reply keyboard (bilingual English / Amharic)."""
    if lang == "am":
        keyboard = [
            [
                KeyboardButton(text="🏷 እቃዎች እና ዋጋ"),
                KeyboardButton(text="🌟 የሰራናቸው ስራዎች")
            ],
            [
                KeyboardButton(text="📝 ማዘዝ ይጀምሩ"),
                KeyboardButton(text="🔍 ትዕዛዝ ይከታተሉ")
            ],
            [
                KeyboardButton(text="🎨 ዝግጁ ዲዛይኖች"),
                KeyboardButton(text="📍 የማድረስ መረጃ")
            ],
            [
                KeyboardButton(text="🌐 ቋንቋ / Language"),
                KeyboardButton(text="📞 ባለቤቱን ያነጋግሩ")
            ]
        ]
        placeholder = "አማራጭ ይምረጡ ወይም ማንኛውንም ጥያቄ ይጻፉ..."
    else:
        keyboard = [
            [
                KeyboardButton(text="🏷 Products & Prices"),
                KeyboardButton(text="🌟 Our Works / Portfolio")
            ],
            [
                KeyboardButton(text="📝 Place an Order"),
                KeyboardButton(text="🔍 Track My Order")
            ],
            [
                KeyboardButton(text="🎨 Ready Designs"),
                KeyboardButton(text="📍 Delivery & Pickup")
            ],
            [
                KeyboardButton(text="🌐 Change Language"),
                KeyboardButton(text="📞 Contact Owner")
            ]
        ]
        placeholder = "Choose an option or type any question..."

    return ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True,
        input_field_placeholder=placeholder
    )

def get_catalog_inline_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    """Inline keyboard attached to catalog messages."""
    if lang == "am":
        buttons = [
            [
                InlineKeyboardButton(text="📝 ማዘዝ ይጀምሩ", callback_data="start_order"),
                InlineKeyboardButton(text="🌟 የሰራናቸው ስራዎች", callback_data="show_portfolio")
            ],
            [
                InlineKeyboardButton(text="🎨 ዝግጁ ዲዛይኖች", callback_data="view_samples"),
                InlineKeyboardButton(text="📍 የማድረስ መረጃ", callback_data="show_delivery")
            ]
        ]
        if config.ADMIN_USERNAME:
            buttons.append([
                InlineKeyboardButton(text="📞 ባለቤቱን ያነጋግሩ", url=f"https://t.me/{config.ADMIN_USERNAME}")
            ])
    else:
        buttons = [
            [
                InlineKeyboardButton(text="📝 Place an Order", callback_data="start_order"),
                InlineKeyboardButton(text="🌟 Our Works", callback_data="show_portfolio")
            ],
            [
                InlineKeyboardButton(text="🎨 Ready Designs", callback_data="view_samples"),
                InlineKeyboardButton(text="📍 Delivery Info", callback_data="show_delivery")
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
            InlineKeyboardButton(text="🏪 Store Pickup - Ledeta (Free)", callback_data="delivery_choice:pickup")
        ],
        [
            InlineKeyboardButton(text="🚚 Doorstep Taxi Delivery (300-1,000 ETB)", callback_data="delivery_choice:yango")
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

def get_cancel_keyboard(lang: str = "en") -> ReplyKeyboardMarkup:
    """Single-button cancel keyboard for form steps."""
    cancel_text = "❌ ሰርዝ" if lang == "am" else "❌ Cancel"
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=cancel_text)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )
