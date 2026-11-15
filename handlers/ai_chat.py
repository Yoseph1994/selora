import logging
from aiogram import Router, F, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from services.gemini_service import gemini_service
import config

logger = logging.getLogger(__name__)
router = Router(name="ai_chat_router")

@router.message(Command("contact"))
@router.message(F.text == "📞 Contact Owner")
async def contact_owner_handler(message: types.Message):
    if config.ADMIN_USERNAME:
        text = (
            "💛 *Contact Selora Prints*\n\n"
            f"You can message the owner directly on Telegram here:\n"
            f"👉 [@{config.ADMIN_USERNAME}](https://t.me/{config.ADMIN_USERNAME})\n\n"
            "We are always happy to help with custom orders, design consultations, or bulk discounts!"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Message Owner Directly", url=f"https://t.me/{config.ADMIN_USERNAME}")]
        ])
    else:
        text = (
            "💛 *Contact Selora Prints*\n\n"
            "Feel free to ask your question right here in this chat, or use *📝 Place an Order* "
            "to leave your details and we will reach out to you immediately!"
        )
        keyboard = None

    await message.answer(text=text, parse_mode="Markdown", reply_markup=keyboard)

@router.message(F.text == "💬 Ask Question / AI")
@router.callback_query(F.data == "ask_question_prompt")
async def ask_question_prompt(event: types.Message | types.CallbackQuery):
    msg = (
        "💬 *How can I help you today?*\n\n"
        "Feel free to ask anything about:\n"
        "• Pricing and product options (stickers, bookmarks, posters, mugs, notebooks)\n"
        "• Store pickup in Ledeta or Yango delivery\n"
        "• Custom sizes, photos, and order timelines\n\n"
        "Just type your question below in *English* or *Amharic (አማርኛ)*! 💛"
    )
    if isinstance(event, types.CallbackQuery):
        await event.message.answer(msg, parse_mode="Markdown")
        await event.answer()
    else:
        await event.answer(msg, parse_mode="Markdown")

@router.message(F.text)
async def handle_freeform_text(message: types.Message):
    """Fallback handler for any general question/message not caught by specific handlers."""
    # Show typing action while processing
    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    user_name = message.from_user.full_name or "Friend"
    reply = await gemini_service.get_response(
        user_message=message.text,
        user_name=user_name
    )

    # Offer helpful action buttons underneath
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 Place an Order", callback_data="start_order"),
            InlineKeyboardButton(text="🏷 View Catalog", callback_data="show_catalog")
        ]
    ])

    await message.answer(
        text=reply,
        parse_mode="Markdown",
        reply_markup=keyboard
    )

