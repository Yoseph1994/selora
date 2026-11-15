import { table, integer, text, real, boolean, index, sql } from 'sdk/db';

// ─── ORDERS TABLE ─────────────────────────────────────────────────────────────
export const orders = table('orders', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  orderCode: text('order_code').unique().notNull(),
  userId: integer('user_id').notNull(),
  fullName: text('full_name').notNull(),
  username: text('username'),
  items: text('items').notNull(),
  totalEtb: real('total_etb').notNull(),
  depositEtb: real('deposit_etb').notNull(),
  balanceEtb: real('balance_etb').default(0),
  designName: text('design_name'),
  customNotes: text('custom_notes'),
  deadline: text('deadline'),
  deliveryType: text('delivery_type').notNull(),
  deliveryLocation: text('delivery_location'),
  phone: text('phone'),
  recipientName: text('recipient_name'),
  customerFiles: text('customer_files').default('[]'),
  paymentMethod: text('payment_method').default('CBE'),
  paymentScreenshot: text('payment_screenshot'),
  paymentStatus: text('payment_status').default('pending_review'),
  status: text('status').default('pending_review'),
  rejectionReason: text('rejection_reason'),
  createdAt: integer('created_at', { mode: 'timestamp' }).default(sql`(unixepoch())`),
  updatedAt: integer('updated_at', { mode: 'timestamp' }).default(sql`(unixepoch())`)
}, (t) => ({
  userOrderIdx: index('idx_orders_user').on(t.userId),
  codeIdx: index('idx_orders_code').on(t.orderCode),
  statusIdx: index('idx_orders_status').on(t.status)
}));

// ─── PRODUCTS TABLE ───────────────────────────────────────────────────────────
export const products = table('products', {
  id: text('id').primaryKey(),
  name: text('name').notNull(),
  nameAm: text('name_am'),
  category: text('category').notNull(),
  price: real('price').notNull(),
  unit: text('unit').default('each'),
  minOrder: integer('min_order').default(1),
  description: text('description'),
  descriptionAm: text('description_am'),
  imageUrl: text('image_url')
}, (t) => ({
  catIdx: index('idx_products_cat').on(t.category)
}));

// ─── DESIGNS TABLE ────────────────────────────────────────────────────────────
export const designs = table('designs', {
  id: integer('id').primaryKey({ autoIncrement: true }),
  productId: text('product_id').notNull(),
  title: text('title').notNull(),
  subproduct: text('subproduct'),
  imageUrl: text('image_url').notNull()
}, (t) => ({
  prodIdx: index('idx_designs_prod').on(t.productId)
}));
