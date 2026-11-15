from pathlib import Path
from aiogram import Router, F, types
from aiogram.filters import CommandStart, Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.reply_markup import get_main_menu_keyboard
import config

router = Router(name="start_router")

BANNER_PATH = Path(__file__).resolve().parent.parent / "data" / "products_images" / "stickers.png"

WELCOME_CAPTION = (
    "💛 *SELORA PRINTS* ✨\n"
    "_Boutique Custom Prints & Thoughtful Gifts_\n"
    "📍 *Ledeta, Addis Ababa*\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "Welcome! We create custom stickers, aesthetic bookmarks, notebooks, wall posters, mugs, and photo puzzles.\n\n"
    "• 💳 *50% Advance Pre-payment*\n"
    "• 🏪 *Free Store Pickup:* Ledeta\n"
    "• 🚚 *Doorstep Delivery:* Fast via Yango\n"
    "━━━━━━━━━━━━━━━━━━━━\n"
    "Choose an option below or type any question:"
)

def get_welcome_inline_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="🏷️ Browse Visual Catalog", callback_data="show_catalog_cards"),
            InlineKeyboardButton(text="📝 Place an Order", callback_data="start_order")
        ],
        [
            InlineKeyboardButton(text="🔍 Track My Order", callback_data="track_orders_menu"),
            InlineKeyboardButton(text="📍 Delivery & Pickup", callback_data="show_delivery")
        ],
        [
            InlineKeyboardButton(text="💬 Ask AI Assistant", callback_data="ask_question_prompt")
        ]
    ]
    if config.ADMIN_USERNAME:
        buttons.append([
            InlineKeyboardButton(text="📞 Chat with Owner Directly", url=f"https://t.me/{config.ADMIN_USERNAME}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(CommandStart())
async def handle_start(message: types.Message):
    if BANNER_PATH.exists():
        await message.answer_photo(
            photo=FSInputFile(BANNER_PATH),
            caption=WELCOME_CAPTION,
            parse_mode="Markdown",
            reply_markup=get_welcome_inline_keyboard()
        )
    else:
        await message.answer(
            text=WELCOME_CAPTION,
            parse_mode="Markdown",
            reply_markup=get_welcome_inline_keyboard()
        )

    # Also display persistent bottom menu
    await message.answer(
        "💡 _Tip: You can use the buttons below anytime to navigate or ask questions in English or Amharic (አማርኛ)!_",
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard()
    )

@router.callback_query(F.data == "show_catalog_cards")
async def cb_show_catalog_cards(callback: types.CallbackQuery):
    from handlers.catalog import get_product_card
    caption, image_file, keyboard = get_product_card(0)
    if caption and image_file:
        await callback.message.answer_photo(
            photo=image_file,
            caption=caption,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    await callback.answer()

@router.callback_query(F.data == "track_orders_menu")
async def cb_track_orders(callback: types.CallbackQuery):
    from handlers.track import track_orders_handler
    await track_orders_handler(callback.message)
    await callback.answer()

@router.message(Command("help"))
async def handle_help(message: types.Message):
    help_text = (
        "💡 *Selora Prints Bot Guide*\n\n"
        "Here are the available features:\n"
        "• /start — Welcome screen and quick actions\n"
        "• /catalog — Visual interactive design catalog with photos\n"
        "• /order — Guided 4-step order form with 50% deposit\n"
        "• /track — Check the live progress of your order\n"
        "• /delivery — Free Ledeta pickup and Yango delivery details\n"
        "• /contact — Speak with the owner\n"
        "• /cancel — Cancel an ongoing form\n\n"
        "You can also chat in free-form! Our AI concierge understands English and Amharic (አማርኛ) 💛"
    )
    await message.answer(
        text=help_text,
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard()
    )
