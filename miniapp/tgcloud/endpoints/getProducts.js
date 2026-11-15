import { db } from 'sdk';
import { products } from '../schema.js';

const DEFAULT_PRODUCTS = [
  {
    id: "business_cards",
    name: "Business Cards",
    nameAm: "የቢዝነስ ካርድ",
    category: "stationery",
    price: 15.0,
    unit: "card",
    minOrder: 100,
    description: "Premium double-sided 350gsm matte/glossy laminated business cards.",
    descriptionAm: "ፕሪሚየም ባለ ሁለት ገጽ 350gsm ማት ወይም ግሎሲ የቢዝነስ ካርዶች።",
    imageUrl: "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=500&auto=format&fit=crop"
  },
  {
    id: "flyers",
    name: "Flyers & Leaflets",
    nameAm: "ፍላየሮች እና በራሪ ወረቀቶች",
    category: "marketing",
    price: 12.0,
    unit: "sheet",
    minOrder: 50,
    description: "High-impact full-color promotional flyers on 150gsm art paper.",
    descriptionAm: "በሚያምር 150gsm አርት ወረቀት ላይ የተዘጋጁ የማስተዋወቂያ ፍላየሮች።",
    imageUrl: "https://images.unsplash.com/photo-1561070791-2526d30994b5?w=500&auto=format&fit=crop"
  },
  {
    id: "stickers",
    name: "Custom Die-Cut Stickers",
    nameAm: "የተቆረጡ ተለጣፊዎች (ስቲከር)",
    category: "packaging",
    price: 8.0,
    unit: "sticker",
    minOrder: 50,
    description: "Waterproof vinyl die-cut stickers for branding, packaging, and laptops.",
    descriptionAm: "የውሃ መቋቋም የሚችሉ የቪኒል ስቲከሮች ለምርት ማሸጊያ እና ብራንዲንግ።",
    imageUrl: "https://images.unsplash.com/photo-1572375992501-4b0892d50c69?w=500&auto=format&fit=crop"
  },
  {
    id: "tshirts",
    name: "Custom T-Shirts",
    nameAm: "ብጁ ቲሸርቶች",
    category: "apparel",
    price: 650.0,
    unit: "shirt",
    minOrder: 1,
    description: "100% heavy combed cotton with vibrant DTF / screen printing.",
    descriptionAm: "100% የጥጥ ቲሸርት በዘመናዊ የዲቲኤፍ እና ስክሪን ፕሪንት የታተመ።",
    imageUrl: "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=500&auto=format&fit=crop"
  },
  {
    id: "hoodies",
    name: "Custom Hoodies",
    nameAm: "ሁዲዎች (ጃኬቶች)",
    category: "apparel",
    price: 1400.0,
    unit: "hoodie",
    minOrder: 1,
    description: "Cozy fleece-lined premium hoodies with chest/back custom graphics.",
    descriptionAm: "ሞቅ ያለ ፕሪሚየም የጥጥ ሁዲ በፈለጉት ዲዛይን እና ጽሑፍ።",
    imageUrl: "https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=500&auto=format&fit=crop"
  },
  {
    id: "mugs",
    name: "Ceramic Mugs",
    nameAm: "የሴራሚክ ኩባያዎች",
    category: "promotional",
    price: 350.0,
    unit: "mug",
    minOrder: 1,
    description: "11oz glossy white ceramic mugs with heat-fused dishwasher-safe print.",
    descriptionAm: "11oz ነጭ የሴራሚክ ኩባያ በሙቀት የታተመ የማያልቅ ፕሪንት።",
    imageUrl: "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=500&auto=format&fit=crop"
  },
  {
    id: "tote_bags",
    name: "Canvas Tote Bags",
    nameAm: "የሸራ ቦርሳዎች (ቶት ባግ)",
    category: "apparel",
    price: 280.0,
    unit: "bag",
    minOrder: 5,
    description: "Eco-friendly heavy canvas reusable tote bags with custom art.",
    descriptionAm: "ለአካባቢ ተስማሚ ጠንካራ የሸራ ቶት ባግ ለገበያ እና ለስጦታ።",
    imageUrl: "https://images.unsplash.com/photo-1544816155-12df9643f363?w=500&auto=format&fit=crop"
  },
  {
    id: "banners",
    name: "Rollup & Outdoor Banners",
    nameAm: "ሮል አፕ እና የውጪ ባነሮች",
    category: "marketing",
    price: 1800.0,
    unit: "banner",
    minOrder: 1,
    description: "High-resolution flex banner with aluminum rollup stand and carry bag.",
    descriptionAm: "ከፍተኛ ጥራት ያለው የፍሌክስ ባነር ከአሉሚኒየም ስታንድ እና ቦርሳ ጋር።",
    imageUrl: "https://images.unsplash.com/photo-1541701494587-cb58502866ab?w=500&auto=format&fit=crop"
  },
  {
    id: "badges",
    name: "Pin Badges",
    nameAm: "የሚሰኩ ባጆች",
    category: "promotional",
    price: 65.0,
    unit: "badge",
    minOrder: 20,
    description: "58mm round pinback badges for events, clubs, and campaigns.",
    descriptionAm: "58ሚሜ ክብ ባጆች ለስብሰባ፣ ለክበባት እና ለማስታወቂያ።",
    imageUrl: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=500&auto=format&fit=crop"
  },
  {
    id: "brochures",
    name: "Tri-Fold Brochures",
    nameAm: "ባለ 3 እጥፍ ብሮሸሮች",
    category: "marketing",
    price: 25.0,
    unit: "brochure",
    minOrder: 50,
    description: "A4 tri-fold corporate brochures on 170gsm glossy paper.",
    descriptionAm: "ለድርጅት ገለጻ የሚሆኑ ባለ 3 እጥፍ የሚያማምሩ ብሮሸሮች።",
    imageUrl: "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=500&auto=format&fit=crop"
  }
];

export default async function (input, ctx) {
  try {
    let rows = await db.select().from(products).all();
    if (!rows || rows.length === 0) {
      // Seed initial products if DB is empty
      try {
        await db.insert(products).values(DEFAULT_PRODUCTS).run();
        rows = DEFAULT_PRODUCTS;
      } catch (e) {
        rows = DEFAULT_PRODUCTS;
      }
    }
    return { ok: true, products: rows };
  } catch (err) {
    return { ok: true, products: DEFAULT_PRODUCTS };
  }
}
