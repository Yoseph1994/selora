from pathlib import Path
from aiogram import Router, F, types
from aiogram.filters import CommandStart, Command
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from keyboards.reply_markup import get_main_menu_keyboard
from data import database
import config

router = Router(name="start_router")

BANNER_PATH = Path(__file__).resolve().parent.parent / "data" / "products_images" / "stickers.png"

WELCOME_EN = (
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

WELCOME_AM = (
    "✦ *ሴሎራ ፕሪንትስ (Selora Prints)* ✦\n"
    "_ጥራት ያላቸው ህትመቶች እና ልዩ ስጦታዎች_\n"
    "📍 ልደታ፣ አዲስ አበባ\n\n"
    "─────────────────────\n\n"
    "▸ ስቲከሮች፣ ቡክማርኮች እና ፖስተሮች\n"
    "▸ የፎቶ ደብተሮች፣ ማጎች እና ፐዝሎች\n"
    "▸ 50% ቅድመ ክፍያ · ፈጣን የማድረስ አገልግሎት\n\n"
    "─────────────────────\n"
    "_ዛሬ ምን ማዘዝ ይፈልጋሉ?_"
)

def get_language_picker_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang:en"),
            InlineKeyboardButton(text="🇪🇹 አማርኛ (Amharic)", callback_data="set_lang:am")
        ]
    ])

def get_welcome_inline_keyboard(lang: str = "en") -> InlineKeyboardMarkup:
    if lang == "am":
        buttons = [
            [
                InlineKeyboardButton(text="🛍️ እቃዎች እና ዋጋ", callback_data="show_catalog_cards"),
                InlineKeyboardButton(text="📝 ማዘዝ ይጀምሩ", callback_data="start_order")
            ],
            [
                InlineKeyboardButton(text="🌟 የሰራናቸው ስራዎች", callback_data="show_portfolio"),
                InlineKeyboardButton(text="🔍 ትዕዛዝ ይከታተሉ", callback_data="track_orders_menu")
            ],
            [
                InlineKeyboardButton(text="📍 የማድረስ መረጃ", callback_data="show_delivery"),
                InlineKeyboardButton(text="🌐 ቋንቋ ይቀይሩ", callback_data="prompt_lang_change")
            ]
        ]
        if config.ADMIN_USERNAME:
            buttons.append([
                InlineKeyboardButton(text="📞 ባለቤቱን ያነጋግሩ", url=f"https://t.me/{config.ADMIN_USERNAME}")
            ])
    else:
        buttons = [
            [
                InlineKeyboardButton(text="🛍 Browse Catalog", callback_data="show_catalog_cards"),
                InlineKeyboardButton(text="📝 Place an Order", callback_data="start_order")
            ],
            [
                InlineKeyboardButton(text="🌟 Our Works / Portfolio", callback_data="show_portfolio"),
                InlineKeyboardButton(text="🔍 Track My Order", callback_data="track_orders_menu")
            ],
            [
                InlineKeyboardButton(text="📍 Delivery Info", callback_data="show_delivery"),
                InlineKeyboardButton(text="🌐 Change Language", callback_data="prompt_lang_change")
            ]
        ]
        if config.ADMIN_USERNAME:
            buttons.append([
                InlineKeyboardButton(text="📞 Chat with Owner", url=f"https://t.me/{config.ADMIN_USERNAME}")
            ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

async def send_welcome_screen(message: types.Message, lang: str):
    caption = WELCOME_AM if lang == "am" else WELCOME_EN
    markup = get_welcome_inline_keyboard(lang)
    bottom_menu = get_main_menu_keyboard(lang)

    if BANNER_PATH.exists():
        await message.answer_photo(
            photo=FSInputFile(BANNER_PATH),
            caption=caption,
            parse_mode="Markdown",
            reply_markup=markup
        )
    else:
        await message.answer(
            text=caption,
            parse_mode="Markdown",
            reply_markup=markup
        )

    tip_text = "💡 _ከታች ያለውን ሜኑ በመጠቀም በማንኛውም ጊዜ ማዘዝ ወይም መረጃ ማግኘት ይችላሉ!_ 💛" if lang == "am" else "💡 _Use the menu below anytime to navigate or ask questions!_ 💛"
    await message.answer(
        tip_text,
        parse_mode="Markdown",
        reply_markup=bottom_menu
    )

@router.message(CommandStart())
async def handle_start(message: types.Message):
    user = message.from_user
    lang = database.get_user_language(user.id)

    # First time user: ask for language preference!
    if not lang:
        lang_prompt = (
            "💛 *Welcome to Selora Prints!*\n"
            "*እንኳን ወደ ሴሎራ ፕሪንትስ በደህና መጡ!*\n"
            "─────────────────────\n"
            "Please choose your preferred language:\n"
            "እባክዎ የሚፈልጉትን ቋንቋ ይምረጡ፡"
        )
        await message.answer(
            lang_prompt,
            parse_mode="Markdown",
            reply_markup=get_language_picker_keyboard()
        )
        return

    await send_welcome_screen(message, lang)

@router.callback_query(F.data.startswith("set_lang:"))
async def callback_set_language(callback: types.CallbackQuery):
    lang = callback.data.split(":")[1]
    user = callback.from_user
    database.set_user_language(user.id, lang, user.full_name, user.username)

    ack = "✅ Language set to English!" if lang == "en" else "✅ ቋንቋው ወደ አማርኛ ተቀይሯል!"
    await callback.answer(ack)
    try:
        await callback.message.delete()
    except Exception:
        pass
    await send_welcome_screen(callback.message, lang)

@router.message(Command("language"))
@router.message(F.text.in_(["🌐 Change Language", "🌐 ቋንቋ / Language", "🌐 Language", "🌐 ቋንቋ ይቀይሩ"]))
@router.callback_query(F.data == "prompt_lang_change")
async def prompt_language_change(event: types.Message | types.CallbackQuery):
    text = (
        "🌐 *Select Language / ቋንቋ ይምረጡ*\n"
        "─────────────────────\n"
        "Choose your preferred language for the bot:"
    )
    markup = get_language_picker_keyboard()
    if isinstance(event, types.CallbackQuery):
        await event.message.answer(text, parse_mode="Markdown", reply_markup=markup)
        await event.answer()
    else:
        await event.answer(text, parse_mode="Markdown", reply_markup=markup)

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
    lang = database.get_user_language(message.from_user.id) or "en"
    if lang == "am":
        help_text = (
            "─────────────────────\n"
            "       *ሴሎራ ፕሪንትስ - መመሪያ*\n"
            "─────────────────────\n\n"
            "▸ /start - መነሻ ገጽ\n"
            "▸ /catalog - የእቃዎች ዝርዝር እና ዋጋ\n"
            "▸ /order - አዲስ ትዕዛዝ ማዘዣ\n"
            "▸ /portfolio - የሰራናቸው ስራዎች ማሳያ\n"
            "▸ /track - የትዕዛዝ ሁኔታ መከታተያ\n"
            "▸ /language - ቋንቋ መቀየሪያ\n"
            "▸ /delivery - የማድረሻ እና የመረከቢያ መረጃ\n"
            "▸ /cancel - ትዕዛዝ መሰረዣ\n\n"
            "_ማንኛውንም ጥያቄ እዚህ በመጻፍ መጠየቅ ይችላሉ!_"
        )
    else:
        help_text = (
            "─────────────────────\n"
            "       *Selora Prints - Help*\n"
            "─────────────────────\n\n"
            "▸ /start - Welcome screen\n"
            "▸ /catalog - Visual product catalog & prices\n"
            "▸ /order - Guided order form\n"
            "▸ /portfolio - Showcase of past works\n"
            "▸ /track - Check your order status\n"
            "▸ /language - Switch English / Amharic\n"
            "▸ /delivery - Pickup & delivery information\n"
            "▸ /cancel - Cancel an ongoing form\n\n"
            "_You can chat freely in English or Amharic (አማርኛ)!_"
        )
    await message.answer(
        text=help_text,
        parse_mode="Markdown",
        reply_markup=get_main_menu_keyboard(lang)
    )
