import logging
from aiogram import Router, types
from services.gemini_service import gemini_service
import config

logger = logging.getLogger(__name__)
router = Router(name="business_router")

@router.business_connection()
async def on_business_connection_update(connection: types.BusinessConnection):
    """Triggered when the Telegram Premium user connects or disconnects the bot in Telegram Business settings."""
    status = "Connected ✅" if connection.is_enabled else "Disconnected ❌"
    logger.info(
        f"Business connection update: user_id={connection.user.id}, "
        f"status={status}, can_reply={connection.can_reply}"
    )

    if connection.is_enabled and config.ADMIN_CHAT_ID:
        try:
            await connection.bot.send_message(
                chat_id=config.ADMIN_CHAT_ID,
                text=(
                    f"💛 *Telegram Business Bot Connected!*\n\n"
                    f"Selora Bot is now linked to your Telegram account (`{connection.user.full_name}`).\n"
                    f"Can reply to incoming DMs: *{'Yes' if connection.can_reply else 'No'}*\n\n"
                    "When customers message your account, Selora will assist them with products, pricing, and ordering!"
                ),
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Failed to send business connection alert: {e}")

@router.business_message()
async def on_business_message(message: types.Message):
    """Triggered when a customer sends a DM to the business owner's personal account."""
    if not message.text:
        return

    # Don't auto-reply to messages sent by the owner herself
    if config.ADMIN_CHAT_ID and str(message.from_user.id) == str(config.ADMIN_CHAT_ID):
        logger.info("Ignoring business message sent by the business owner.")
        return

    sender_name = message.from_user.full_name or "Customer"
    logger.info(f"Received Business DM from {sender_name} ({message.from_user.id}): '{message.text}'")

    try:
        # Get AI or fallback response for the customer
        reply_text = await gemini_service.get_response(
            user_message=message.text,
            user_name=sender_name
        )

        # Send response on the owner's behalf using business_connection_id
        await message.answer(
            text=reply_text,
            business_connection_id=message.business_connection_id,
            parse_mode="Markdown"
        )
        logger.info(f"Auto-replied on business connection {message.business_connection_id} to {sender_name}")
    except Exception as e:
        logger.error(f"Failed to auto-reply to business message: {e}")

