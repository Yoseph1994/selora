import { db, api, EndpointError } from 'sdk';
import { orders } from '../schema.js';
import { desc } from 'sdk/db';

export default async function (input, ctx) {
  const user = ctx.initData?.user || input.user || {};
  const userId = user.id || 0;
  const fullName = [user.first_name, user.last_name].filter(Boolean).join(' ') || input.fullName || 'Customer';
  const username = user.username || input.username || '';

  const items = input.items || 'Custom Print Order';
  const totalEtb = parseFloat(input.totalEtb) || 0;
  if (totalEtb <= 0) {
    throw new EndpointError('Invalid total amount', { code: 'INVALID_AMOUNT' });
  }

  const depositEtb = Math.round(totalEtb * 0.50);
  const balanceEtb = Math.max(0, totalEtb - depositEtb);

  // Generate unique order code (SP-100X)
  let nextNum = 1001;
  try {
    const latest = await db.select({ orderCode: orders.orderCode })
      .from(orders)
      .orderBy(desc(orders.id))
      .limit(1)
      .get();

    if (latest && latest.orderCode) {
      const match = latest.orderCode.match(/SP-(\d+)/i);
      if (match) {
        nextNum = parseInt(match[1], 10) + 1;
      }
    }
  } catch (e) {
    nextNum = Math.floor(1000 + Math.random() * 9000);
  }
  const orderCode = `SP-${nextNum}`;

  const deadline = input.deadline || 'Standard (3-4 Days)';
  const deliveryType = input.deliveryType || 'Store Pickup (Ledeta)';
  const deliveryLocation = input.deliveryLocation || '';
  const phone = input.phone || '';
  const recipientName = input.recipientName || fullName;
  const designName = input.designName || '';
  const customNotes = input.customNotes || '';
  const paymentMethod = input.paymentMethod || 'CBE';
  const paymentScreenshot = input.paymentScreenshot || '';
  const customerFiles = JSON.stringify(input.customerFiles || []);

  // Insert into SQLite database
  await db.insert(orders).values({
    orderCode,
    userId,
    fullName,
    username,
    items,
    totalEtb,
    depositEtb,
    balanceEtb,
    designName,
    customNotes,
    deadline,
    deliveryType,
    deliveryLocation,
    phone,
    recipientName,
    customerFiles,
    paymentMethod,
    paymentScreenshot,
    paymentStatus: 'pending_review',
    status: 'pending_review'
  }).run();

  // Send Telegram DM notification to Customer if userId is available
  if (userId) {
    try {
      const customerMsg = (
        `🎉 *Order Placed Successfully!* 💛\n\n` +
        `🔖 *Order Code:* \`${orderCode}\`\n` +
        `━━━━━━━━━━━━━━━━━━━━\n` +
        `🏷 *Items:* ${items}\n` +
        `💰 *Total Price:* ${totalEtb.toLocaleString()} ETB\n` +
        `💳 *50% Deposit:* ${depositEtb.toLocaleString()} ETB (${paymentMethod})\n` +
        `⏳ *Remaining Balance:* ${balanceEtb.toLocaleString()} ETB (on delivery)\n` +
        `🗓 *Need By:* ${deadline}\n` +
        `🚚 *Delivery:* ${deliveryType}\n` +
        (customNotes ? `📝 *Custom Note:* ${customNotes}\n` : '') +
        `━━━━━━━━━━━━━━━━━━━━\n` +
        `✅ Our production team has received your deposit proof and is reviewing it now. ` +
        `You will receive real-time updates directly in Telegram as printing begins!\n\n` +
        `🔍 Type \`/track ${orderCode}\` anytime to view progress.`
      );

      await api.sendMessage({
        chat_id: userId,
        text: customerMsg,
        parse_mode: 'Markdown'
      });
    } catch (e) {
      console.warn('Could not send DM to customer:', e);
    }
  }

  return {
    ok: true,
    orderCode,
    totalEtb,
    depositEtb,
    balanceEtb,
    status: 'pending_review',
    message: `Order ${orderCode} created successfully.`
  };
}
