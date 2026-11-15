from pathlib import Path
from aiogram import Router, F, types
from aiogram.filters import CommandStart, Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.reply_markup import get_main_menu_keyboard
import config

router = Router(name="start_router")

BANNER_PATH = Path(__file__).resolve().parent.parent / "data" / "products_images" / "stickers.png"

WELCOME_CAPTION = (
    "✦ *SELORA PRINTS* ✦\n"
    "_Boutique Custom Prints & Thoughtful Gifts_\n"
    "📍 Ledeta, Addis Ababa\n\n"
    "─────────────────────\n\n"
    "▸ Custom stickers, bookmarks & posters\n"
    "▸ Photo books, mugs & puzzles\n"
    "▸ 50% advance deposit · Fast delivery\n\n"
    "─────────────────────\n"
    "_What would you like to do today?_"
)

def get_welcome_inline_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="🛍 Browse Catalog", callback_data="show_catalog_cards"),
            InlineKeyboardButton(text="📝 Place an Order", callback_data="start_order")
        ],
        [
            InlineKeyboardButton(text="🔍 Track My Order", callback_data="track_orders_menu"),
            InlineKeyboardButton(text="📍 Delivery Info", callback_data="show_delivery")
        ],
        [
            InlineKeyboardButton(text="💬 Ask a Question", callback_data="ask_question_prompt")
        ]
    ]
    if config.ADMIN_USERNAME:
        buttons.append([
            InlineKeyboardButton(text="📞 Chat with Owner", url=f"https://t.me/{config.ADMIN_USERNAME}")
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

    # Persistent bottom menu
    await message.answer(
        "_Use the menu below to navigate anytime — English & Amharic supported_ 💛",
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
        "─────────────────────\n"
        "       *Selora Prints — Help*\n"
        "─────────────────────\n\n"
        "▸ /start — Welcome screen\n"
        "▸ /catalog — Browse visual product catalog\n"
        "▸ /order — Start a new order (5-step guide)\n"
        "▸ /track — Check your order status\n"
        "▸ /designs — Browse ready-made designs\n"
        "▸ /delivery — Pickup & delivery info\n"
        "▸ /cancel — Cancel an ongoing form\n\n"
        "_You can also chat freely — our AI concierge understands English and Amharic (አማርኛ)._"
    )
    await message.answer(
        text=help_text,
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard()
    )
