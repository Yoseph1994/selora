import { db, EndpointError } from 'sdk';
import { orders } from '../schema.js';
import { eq, desc } from 'sdk/db';

export default async function (input, ctx) {
  const user = ctx.initData?.user || input.user || {};
  const orderCode = (input.orderCode || '').trim().toUpperCase();

  // 1. Direct search by order code
  if (orderCode) {
    const row = await db.select().from(orders).where(eq(orders.orderCode, orderCode)).get();
    if (!row) {
      throw new EndpointError(`No order found with code ${orderCode}`, { code: 'NOT_FOUND' });
    }
    return { ok: true, order: row };
  }

  // 2. Search by current user ID
  if (user && user.id) {
    const userOrders = await db.select()
      .from(orders)
      .where(eq(orders.userId, user.id))
      .orderBy(desc(orders.id))
      .limit(10)
      .all();

    return {
      ok: true,
      orders: userOrders || [],
      order: userOrders && userOrders.length > 0 ? userOrders[0] : null
    };
  }

  throw new EndpointError('Please specify an order code or sign in with Telegram', { code: 'MISSING_PARAMS' });
}
