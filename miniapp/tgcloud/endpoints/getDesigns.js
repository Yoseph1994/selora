import { db } from 'sdk';
import { designs } from '../schema.js';

const DEFAULT_DESIGNS = [
  {
    id: 1,
    productId: "business_cards",
    title: "Minimalist Executive",
    subproduct: "Matte Black & Gold Foil",
    imageUrl: "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=500&auto=format&fit=crop"
  },
  {
    id: 2,
    productId: "business_cards",
    title: "Modern Creative Pastel",
    subproduct: "Clean Typography & Soft Pastel",
    imageUrl: "https://images.unsplash.com/photo-1544717305-2782549b5136?w=500&auto=format&fit=crop"
  },
  {
    id: 3,
    productId: "tshirts",
    title: "Vibrant Addis Typography",
    subproduct: "Chest Graphic / Urban Amharic",
    imageUrl: "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=500&auto=format&fit=crop"
  },
  {
    id: 4,
    productId: "mugs",
    title: "Coffee Lover Morning Roast",
    subproduct: "Full Wrap Ceramic Print",
    imageUrl: "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=500&auto=format&fit=crop"
  },
  {
    id: 5,
    productId: "stickers",
    title: "Holographic Tech Badge",
    subproduct: "Glossy Die-Cut Vinyl",
    imageUrl: "https://images.unsplash.com/photo-1572375992501-4b0892d50c69?w=500&auto=format&fit=crop"
  },
  {
    id: 6,
    productId: "tote_bags",
    title: "Botanical Earth Line Art",
    subproduct: "Minimalist Screen Print",
    imageUrl: "https://images.unsplash.com/photo-1544816155-12df9643f363?w=500&auto=format&fit=crop"
  }
];

export default async function (input, ctx) {
  try {
    let rows = await db.select().from(designs).all();
    if (!rows || rows.length === 0) {
      try {
        await db.insert(designs).values(DEFAULT_DESIGNS).run();
        rows = DEFAULT_DESIGNS;
      } catch (e) {
        rows = DEFAULT_DESIGNS;
      }
    }
    return { ok: true, designs: rows };
  } catch (err) {
    return { ok: true, designs: DEFAULT_DESIGNS };
  }
}
