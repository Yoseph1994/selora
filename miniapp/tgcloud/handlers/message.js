import { api } from 'sdk';

export default async function (message, ctx) {
  const chatId = message.chat.id;
  const user = message.from || {};
  const text = (message.text || '').trim();

  // Handle /start command or default message
  if (text.startsWith('/start') || text === 'hi' || text === 'hello') {
    const firstName = user.first_name || 'Customer';
    
    const welcomeText = (
      `✨ *Welcome to Selora Prints!* 💛\n` +
      `እንኳን ወደ ሴሎራ ፕሪንትስ በደህና መጡ!\n\n` +
      `Hello ${firstName}! We are your premier printing partner in Addis Ababa. ` +
      `From business cards and branding to custom T-shirts, mugs, and banners, we deliver top-tier quality prints.\n\n` +
      `🌟 *Order easily right inside Telegram:*\n` +
      `• Browse 15+ printing product lines\n` +
      `• Pick ready-made designs or upload your artwork\n` +
      `• Calculate instant 50% deposit with CBE / Telebirr\n` +
      `• Choose Ledeta store pickup or taxi delivery\n` +
      `• Track your print pipeline live (Deposit ➔ Production ➔ Delivery)\n\n` +
      `👇 *Tap below to launch the Selora Mini App:*`
    );

    const keyboard = {
      inline_keyboard: [
        [
          {
            text: "🛍️ Launch Selora Prints App",
            web_app: { url: "https://app.tgcloud.ai" }
          }
        ],
        [
          { text: "🔍 Track Order", callback_data: "cmd_track" },
          { text: "💬 Contact Support", url: "https://t.me/Keb_g" }
        ]
      ]
    };

    await api.sendMessage({
      chat_id: chatId,
      text: welcomeText,
      parse_mode: 'Markdown',
      reply_markup: keyboard
    });

    // Configure the Telegram persistent Chat Menu Button to launch the Mini App
    try {
      await api.setChatMenuButton({
        chat_id: chatId,
        menu_button: {
          type: 'web_app',
          text: '🛍️ Open Store',
          web_app: { url: 'https://app.tgcloud.ai' }
        }
      });
    } catch (e) {
      // Menu button configuration fallback
    }
    return;
  }

  // Handle direct order tracking: /track SP-1003
  if (text.toLowerCase().startsWith('/track')) {
    const parts = text.split(/\s+/);
    if (parts.length > 1) {
      const code = parts[1].toUpperCase();
      await api.sendMessage({
        chat_id: chatId,
        text: `🔍 *Tracking Order ${code}:*\nPlease tap below to view live pipeline status, remaining balance, and delivery updates:`,
        parse_mode: 'Markdown',
        reply_markup: {
          inline_keyboard: [
            [
              {
                text: `📦 View Status of ${code}`,
                web_app: { url: `https://app.tgcloud.ai?track=${code}` }
              }
            ]
          ]
        }
      });
      return;
    }

    await api.sendMessage({
      chat_id: chatId,
      text: `🔍 *Order Tracking*\nTo track your order, send: \`/track SP-XXXX\` or launch the Mini App below:`,
      parse_mode: 'Markdown',
      reply_markup: {
        inline_keyboard: [
          [
            {
              text: "🔍 Open Order Tracker",
              web_app: { url: "https://app.tgcloud.ai?tab=track" }
            }
          ]
        ]
      }
    });
    return;
  }

  // Default fallback
  await api.sendMessage({
    chat_id: chatId,
    text: `💛 *Selora Prints*\n\nTap below to explore our products or place a new print order:`,
    parse_mode: 'Markdown',
    reply_markup: {
      inline_keyboard: [
        [
          {
            text: "🛍️ Open Selora Store",
            web_app: { url: "https://app.tgcloud.ai" }
          }
        ]
      ]
    }
  });
}
