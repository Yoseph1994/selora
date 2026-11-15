import logging
from typing import Optional
import config

logger = logging.getLogger(__name__)

def get_system_prompt() -> str:
    from bot.data import database

    products_data = database.get_products_data()
    designs_data = database.get_designs_data()

    products_text = ""
    for p in products_data.get("products", []):
        min_ord = f" (Minimum order: {p['min_order']})" if p.get("min_order") else ""
        price_val = f"{p['price']} birr" if p.get('price') is not None else "Custom / upon inquiry"
        products_text += f"- {p['name']}: {price_val} {p.get('unit', '')}{min_ord}. {p.get('description', '')}\n"

    designs_lines = []
    for d in designs_data.get("designs", [])[:15]:
        designs_lines.append(f"- {d.get('title')} ({d.get('product_name')}, Style: {d.get('subproduct')})")
    designs_summary = "\n".join(designs_lines)

    prompt = f"""You are the official AI assistant for "Selora Prints", a boutique printing and custom gifts business based in Addis Ababa, Ethiopia.
Your brand personality is warm, creative, helpful, and polite with a yellow aesthetic (💛).

STORE INFORMATION:
- Store Name: Selora Prints
- Location: Ledeta, Addis Ababa
- Store Pickup: Free pickup directly from our store in Ledeta.
- Delivery: Delivered across Addis Ababa via Yango. The customer pays the delivery fee directly to the Yango driver upon arrival.
- 50% Advance Pre-Payment: All orders require a 50% deposit before production begins.
- Turnaround & Rush Order Policy:
  • Standard production turnaround is 3+ days (normal pricing).
  • Urgent Rush Orders: Needed within 2 days require an additional +200 ETB rush fee.
  • NEXT-DAY (TOMORROW) ORDERS CANNOT BE ACCEPTED under any circumstances due to printing, binding, and drying time.
- Payment Accounts:
  • Commercial Bank of Ethiopia (CBE): {config.PAYMENT_CBE_ACCOUNT} (Name: {config.PAYMENT_CBE_NAME})
  • Telebirr: {config.PAYMENT_TELEBIRR} (Name: {config.PAYMENT_TELEBIRR_NAME})
- To Place an Order: Customers should specify:
  1. What they want to order and quantity
  2. When they need it by (deadline)
  3. Their delivery location (or store pickup in Ledeta)
  4. Send any photos/artwork files if ordering custom items (Polaroids, Mugs, Puzzles, Stickers).

PRODUCT CATALOG & CURRENT PRICES (Live Database):
{products_text}

READY DESIGN COLLECTIONS & STYLES (Customers can pick ready designs or upload custom photos):
{designs_summary}

IMPORTANT RULES:
1. Always be polite, warm, and concise. Use emojis like 💛, ✨, 🏷, 🚚.
2. Support both English and Amharic (አማርኛ). If the customer writes in Amharic (or Latin Amharic), reply fluently in Amharic.
3. If asked about prices, give the exact prices from the catalog above.
4. If a customer wants to place an order, encourage them to use the "📝 Place an Order" button in the menu, or prompt them to provide their order details, deadline, and delivery address.
5. If you do not know an answer or if they need custom negotiations or large bulk orders, warmly direct them to chat directly with the owner{f' (@{config.ADMIN_USERNAME})' if config.ADMIN_USERNAME else ''}.
"""
    return prompt

class GeminiService:
    def __init__(self):
        self.client = None
        if config.GEMINI_API_KEY:
            try:
                from google import genai
                self.client = genai.Client(api_key=config.GEMINI_API_KEY)
                logger.info("Gemini client initialized successfully.")
            except Exception as e:
                logger.error(f"Error initializing Gemini client: {e}")
                self.client = None
        else:
            logger.warning("GEMINI_API_KEY not found. AI responses will use local rule-based fallback.")

    async def get_response(self, user_message: str, user_name: Optional[str] = None) -> str:
        """Generate response via Gemini or intelligent fallback."""
        if self.client:
            try:
                # Use gemini-2.5-flash or gemini-2.0-flash with system instruction
                from google.genai import types
                
                system_instruction = get_system_prompt()
                user_content = f"User ({user_name or 'Customer'}): {user_message}"
                
                response = await self.client.aio.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=user_content,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.7,
                        max_output_tokens=500
                    )
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                logger.warning(f"Gemini API call failed: {e}. Falling back to rule-based responder.")

        # Built-in intelligent rule-based fallback
        return self._fallback_reply(user_message)

    def _fallback_reply(self, message: str) -> str:
        text = message.lower()

        # Pricing & Catalog
        if any(w in text for w in ["price", "cost", "catalog", "list", "how much", "ዋጋ", "ዝርዝር", "ስንት", "ምን አለ"]):
            return (
                "💛 *Selora Prints - Products & Prices*\n\n"
                "🏷 *Stickers:* 20 birr\n"
                "🔖 *Bookmarks:* 50 birr\n"
                "💼 *Business cards:* 10 birr\n"
                "📓 *Mini notebook:* 200 birr\n"
                "📔 *Notebook:* 500 birr\n"
                "📖 *Minibook:* 600 birr\n"
                "📸 *Polaroid prints:* Available upon request\n"
                "☕ *Mug:* 1500 birr\n"
                "🧩 *Puzzle:* 1500 birr\n\n"
                "🟢 *STICKER POSTER* (Peel & stick: wall, glass, smooth surface):\n"
                "• A5 = 40 birr (Min order: 10)\n"
                "• A4 = 70 birr (Min order: 10)\n\n"
                "Click the *📝 Place an Order* button below to make an order!"
            )

        # Delivery & Location
        if any(w in text for w in ["delivery", "yango", "where", "location", "address", "pickup", "ልደታ", "ማድረስ", "የት", "አድራሻ", "ቦታ"]):
            return (
                "📍 *Delivery & Pickup Information*\n\n"
                "🏪 *Ledeta Store Pickup:* Free pickup directly from our store in Ledeta!\n"
                "🚚 *Yango Delivery:* We send orders via Yango across Addis Ababa (delivery fee is paid by you upon receipt).\n\n"
                "Need help? Tap *📝 Place an Order* or *📞 Contact Owner*."
            )

        # Designs & Templates
        if any(w in text for w in ["design", "sample", "template", "style", "ዲዛይን", "ምሳሌ", "ስዕል"]):
            return (
                "🎨 *Selora Ready Designs & Templates*\n\n"
                "We offer curated artwork collections across our products:\n"
                "• 🏷 *Stickers:* Anime & Manga, Aesthetic Pastel, Motivational Quotes\n"
                "• 🔖 *Bookmarks:* Dark Academia, Pressed Wildflowers\n"
                "• 💼 *Business Cards:* Modern Corporate, Luxury Matte Black & Gold Foil\n"
                "• 📸 *Polaroids:* Classic 90s Vintage Frame, Retro Film Grain\n"
                "• 📖 *Photo Books:* Wedding & Couples, Keepsake Noir\n"
                "• ☕ *Mugs:* Addis Ababa Coffee Culture Ceramic\n\n"
                "👉 Tap **'🎨 Ready Designs'** in the menu or type `/designs` to flip through our visual design carousel!\n"
                "📸 *Prefer your own design?* You can always upload your own custom photos during ordering!"
            )

        # How to order
        if any(w in text for w in ["order", "buy", "how to", "ማዘዝ", "ትዕዛዝ", "መግዛት"]):
            return (
                "📝 *How to Order at Selora Prints:*\n\n"
                "Simply tap the *📝 Place an Order* button below, or message us:\n"
                "1️⃣ What you want to order and how many\n"
                "2️⃣ When you need it by (deadline)\n"
                "3️⃣ Your location (for Yango delivery or store pickup in Ledeta)\n\n"
                "We'll review your details and confirm right away! 💛"
            )

        # Contact owner
        if any(w in text for w in ["contact", "owner", "call", "phone", "ሰው", "ስልክ", "ማናገር"]):
            owner_contact = f"@{config.ADMIN_USERNAME}" if config.ADMIN_USERNAME else "our team"
            return (
                f"💛 You can reach the owner directly at {owner_contact} for special requests, bulk orders, or custom designs!"
            )

        # Amharic greetings
        if any(w in text for w in ["ሰላም", "እንደምን", "ሀይ", "selam"]):
            return (
                "ሰላም! 💛 እንኳን ወደ Selora Prints በደህና መጡ!\n\n"
                "ምን ልርዳዎት? የዋጋ ዝርዝር ለማየት '🏷 Products & Prices' ወይም ለማዘዝ '📝 Place an Order' የሚለውን ይጫኑ!"
            )

        # Default welcoming response
        return (
            "Welcome to *Selora Prints*! 💛\n\n"
            "We make custom stickers, bookmarks, notebooks, posters, mugs, puzzles, and polaroid prints!\n\n"
            "• Tap *🏷 Products & Prices* to view all items.\n"
            "• Tap *📝 Place an Order* to submit your request.\n"
            "• Or simply ask me any question about our products and delivery!"
        )

# Global singleton
gemini_service = GeminiService()

