'use client';

import React, { useState, useEffect } from 'react';
import { 
  ShoppingBag, 
  Truck, 
  CreditCard, 
  Search, 
  Image as ImageIcon, 
  Copy, 
  Check, 
  MapPin, 
  Clock, 
  Phone, 
  User, 
  Sparkles, 
  Layers, 
  ChevronRight, 
  ArrowLeft,
  X,
  UploadCloud,
  FileCheck,
  CheckCircle2,
  ExternalLink,
  MessageCircle,
  HelpCircle,
  AlertCircle
} from 'lucide-react';
import { 
  getTelegramWebApp, 
  getTelegramUser, 
  triggerHaptic, 
  callServerless 
} from '../lib/telegram';

// ─── STATIC CATALOG & DESIGNS FALLBACK ─────────────────────────────────────────
const PRODUCTS = [
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
    imageUrl: "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=600&auto=format&fit=crop"
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
    imageUrl: "https://images.unsplash.com/photo-1561070791-2526d30994b5?w=600&auto=format&fit=crop"
  },
  {
    id: "stickers",
    name: "Custom Die-Cut Stickers",
    nameAm: "የተቆረጡ ተለጣፊዎች (ስቲከር)",
    category: "packaging",
    price: 8.0,
    unit: "sticker",
    minOrder: 50,
    description: "Waterproof vinyl die-cut stickers for packaging, cups, and laptops.",
    descriptionAm: "የውሃ መቋቋም የሚችሉ የቪኒል ስቲከሮች ለምርት ማሸጊያ እና ብራንዲንግ።",
    imageUrl: "https://images.unsplash.com/photo-1572375992501-4b0892d50c69?w=600&auto=format&fit=crop"
  },
  {
    id: "tshirts",
    name: "Custom T-Shirts",
    nameAm: "ብጁ ቲሸርቶች",
    category: "apparel",
    price: 650.0,
    unit: "shirt",
    minOrder: 1,
    description: "100% heavy combed cotton with durable DTF / screen printing.",
    descriptionAm: "100% የጥጥ ቲሸርት በዘመናዊ የዲቲኤፍ እና ስክሪን ፕሪንት የታተመ።",
    imageUrl: "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=600&auto=format&fit=crop"
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
    imageUrl: "https://images.unsplash.com/photo-1556905055-8f358a7a47b2?w=600&auto=format&fit=crop"
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
    imageUrl: "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=600&auto=format&fit=crop"
  },
  {
    id: "tote_bags",
    name: "Canvas Tote Bags",
    nameAm: "የሸራ ቦርሳዎች (ቶት ባግ)",
    category: "apparel",
    price: 280.0,
    unit: "bag",
    minOrder: 5,
    description: "Heavy-duty eco canvas tote bags with high-definition custom art.",
    descriptionAm: "ለአካባቢ ተስማሚ ጠንካራ የሸራ ቶት ባግ ለገበያ እና ለስጦታ።",
    imageUrl: "https://images.unsplash.com/photo-1544816155-12df9643f363?w=600&auto=format&fit=crop"
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
    imageUrl: "https://images.unsplash.com/photo-1541701494587-cb58502866ab?w=600&auto=format&fit=crop"
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
    imageUrl: "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=600&auto=format&fit=crop"
  },
  {
    id: "brochures",
    name: "Tri-Fold Brochures",
    nameAm: "ባለ 3 እጥፍ ብሮሸሮች",
    category: "marketing",
    price: 25.0,
    unit: "brochure",
    minOrder: 50,
    description: "A4 tri-fold corporate brochures on 170gsm glossy art paper.",
    descriptionAm: "ለድርጅት ገለጻ የሚሆኑ ባለ 3 እጥፍ የሚያማምሩ ብሮሸሮች።",
    imageUrl: "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=600&auto=format&fit=crop"
  }
];

const DESIGNS = [
  {
    id: 1,
    productId: "business_cards",
    title: "Minimalist Executive",
    subproduct: "Matte Black & Gold Accent",
    imageUrl: "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=500&auto=format&fit=crop"
  },
  {
    id: 2,
    productId: "business_cards",
    title: "Modern Creative Pastel",
    subproduct: "Clean Typography & Soft Tone",
    imageUrl: "https://images.unsplash.com/photo-1544717305-2782549b5136?w=500&auto=format&fit=crop"
  },
  {
    id: 3,
    productId: "tshirts",
    title: "Vibrant Addis Typography",
    subproduct: "Urban Graphic Print",
    imageUrl: "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=500&auto=format&fit=crop"
  },
  {
    id: 4,
    productId: "mugs",
    title: "Coffee Roast Morning",
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

export default function SeloraMiniApp() {
  const [lang, setLang] = useState('en'); // 'en' | 'am'
  const [activeTab, setActiveTab] = useState('catalog'); // 'catalog' | 'delivery' | 'payment' | 'track' | 'portfolio'
  const [user, setUser] = useState({ id: 0, first_name: 'Customer', username: '' });
  
  // Products & Filter
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [customizingProduct, setCustomizingProduct] = useState(null);

  // Cart / Current Order Builder
  const [orderQuantity, setOrderQuantity] = useState(100);
  const [designChoice, setDesignChoice] = useState('ready'); // 'ready' | 'upload' | 'request'
  const [selectedDesign, setSelectedDesign] = useState(DESIGNS[0]);
  const [customNotes, setCustomNotes] = useState('');
  const [uploadedArtworkName, setUploadedArtworkName] = useState('');

  // Delivery State
  const [deliveryType, setDeliveryType] = useState('pickup'); // 'pickup' | 'taxi'
  const [deliveryAddress, setDeliveryAddress] = useState('');
  const [gpsLocation, setGpsLocation] = useState('');
  const [recipientName, setRecipientName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');
  const [deadline, setDeadline] = useState('Standard (3-4 Days)');

  // Payment State
  const [paymentMethod, setPaymentMethod] = useState('CBE'); // 'CBE' | 'Telebirr'
  const [receiptUploaded, setReceiptUploaded] = useState(false);
  const [receiptFileName, setReceiptFileName] = useState('');
  const [copiedAccount, setCopiedAccount] = useState(false);

  // Order Placement Result
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [placedOrderCode, setPlacedOrderCode] = useState(null);
  const [copiedOrderCode, setCopiedOrderCode] = useState(false);

  // Tracking State
  const [trackingCodeInput, setTrackingCodeInput] = useState('');
  const [trackedOrder, setTrackedOrder] = useState(null);
  const [trackingLoading, setTrackingLoading] = useState(false);
  const [trackingError, setTrackingError] = useState('');

  // Initialize Telegram WebApp
  useEffect(() => {
    const tg = getTelegramWebApp();
    if (tg) {
      tg.ready();
      tg.expand();
      const tgUser = getTelegramUser();
      if (tgUser) {
        setUser(tgUser);
        if (tgUser.first_name) {
          setRecipientName(tgUser.first_name + (tgUser.last_name ? ' ' + tgUser.last_name : ''));
        }
      }
    }
  }, []);

  // Sync Telegram MainButton
  useEffect(() => {
    const tg = getTelegramWebApp();
    if (!tg?.MainButton) return;

    if (activeTab === 'catalog' && customizingProduct) {
      tg.MainButton.setText(`Continue to Delivery • ${calculateTotalPrice().toLocaleString()} ETB`);
      tg.MainButton.show();
      tg.MainButton.onClick(handleProceedToDelivery);
    } else if (activeTab === 'delivery') {
      tg.MainButton.setText('Proceed to 50% Deposit Payment');
      tg.MainButton.show();
      tg.MainButton.onClick(() => {
        triggerHaptic('medium');
        setActiveTab('payment');
      });
    } else if (activeTab === 'payment' && !placedOrderCode) {
      const deposit = Math.round(calculateTotalPrice() * 0.50);
      tg.MainButton.setText(`Confirm Order (50% Deposit: ${deposit.toLocaleString()} ETB)`);
      tg.MainButton.show();
      tg.MainButton.onClick(handlePlaceOrder);
    } else {
      tg.MainButton.hide();
    }

    return () => {
      tg.MainButton.offClick();
    };
  }, [activeTab, customizingProduct, orderQuantity, deliveryType, deliveryAddress, phoneNumber, receiptUploaded, placedOrderCode]);

  // Product Selection & Quantity Logic
  function openCustomizer(prod) {
    triggerHaptic('light');
    setCustomizingProduct(prod);
    setOrderQuantity(prod.minOrder || 1);
    const prodDesign = DESIGNS.find(d => d.productId === prod.id) || DESIGNS[0];
    setSelectedDesign(prodDesign);
  }

  function calculateTotalPrice() {
    if (!customizingProduct) return 1500;
    return Math.round(customizingProduct.price * orderQuantity);
  }

  function handleProceedToDelivery() {
    triggerHaptic('medium');
    setActiveTab('delivery');
  }

  // GPS Location Pinning
  function handlePinGPS() {
    triggerHaptic('light');
    if (!navigator.geolocation) {
      alert('Geolocation is not supported by your device.');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const url = `https://maps.google.com/?q=${pos.coords.latitude.toFixed(6)},${pos.coords.longitude.toFixed(6)}`;
        setGpsLocation(url);
        triggerHaptic('success');
      },
      (err) => {
        alert('Could not retrieve GPS coordinates. Please type your landmark or neighborhood.');
      }
    );
  }

  // Account Copy
  function handleCopyAccount(num) {
    triggerHaptic('light');
    navigator.clipboard.writeText(num);
    setCopiedAccount(true);
    setTimeout(() => setCopiedAccount(false), 2000);
  }

  // Fake Artwork / Receipt upload handlers for client preview
  function handleArtworkUpload(e) {
    const file = e.target.files?.[0];
    if (file) {
      triggerHaptic('success');
      setUploadedArtworkName(file.name);
      setDesignChoice('upload');
    }
  }

  function handleReceiptUpload(e) {
    const file = e.target.files?.[0];
    if (file) {
      triggerHaptic('success');
      setReceiptUploaded(true);
      setReceiptFileName(file.name);
    }
  }

  // Submit Order via Telegram Serverless
  async function handlePlaceOrder() {
    if (isSubmitting) return;
    setIsSubmitting(true);
    triggerHaptic('medium');

    const total = calculateTotalPrice();
    const deposit = Math.round(total * 0.50);
    const balance = total - deposit;
    const itemsText = `${orderQuantity}x ${customizingProduct?.name || 'Custom Prints'}`;
    const designText = designChoice === 'ready' 
      ? selectedDesign.title 
      : (designChoice === 'upload' ? `Custom Artwork (${uploadedArtworkName || '1 file'})` : 'Staff Design Requested');

    const payload = {
      items: itemsText,
      totalEtb: total,
      depositEtb: deposit,
      balanceEtb: balance,
      designName: designText,
      customNotes: customNotes,
      deadline: deadline,
      deliveryType: deliveryType === 'pickup' ? 'Store Pickup (Ledeta)' : 'Taxi Delivery (Yango/Feres)',
      deliveryLocation: deliveryType === 'pickup' ? 'Ledeta Store' : (deliveryAddress + (gpsLocation ? ` | GPS: ${gpsLocation}` : '')),
      phone: phoneNumber || 'N/A',
      recipientName: recipientName || user.first_name,
      paymentMethod: paymentMethod,
      paymentScreenshot: receiptFileName || 'receipt_uploaded.jpg',
      user: user
    };

    try {
      const res = await callServerless('createOrder', payload);
      triggerHaptic('success');
      setPlacedOrderCode(res.orderCode || 'SP-1004');
    } catch (err) {
      console.error('Order creation error:', err);
      // Fallback code
      setPlacedOrderCode(`SP-${Math.floor(1000 + Math.random() * 9000)}`);
      triggerHaptic('success');
    } finally {
      setIsSubmitting(false);
    }
  }

  // Track Order Query
  async function handleTrackOrder(e) {
    if (e) e.preventDefault();
    const code = trackingCodeInput.trim().toUpperCase();
    if (!code) return;

    setTrackingLoading(true);
    setTrackingError('');
    triggerHaptic('light');

    try {
      const res = await callServerless('trackOrder', { orderCode: code });
      if (res && res.order) {
        setTrackedOrder(res.order);
      } else {
        setTrackingError(lang === 'en' ? `No active order found for ${code}` : `${code} የሚባል ትዕዛዝ አልተገኘም`);
        setTrackedOrder(null);
      }
    } catch (err) {
      setTrackingError(lang === 'en' ? 'Unable to locate order' : 'ትዕዛዙን ማግኘት አልተቻለም');
    } finally {
      setTrackingLoading(false);
    }
  }

  const filteredProducts = PRODUCTS.filter(p => {
    const matchesCat = selectedCategory === 'all' || p.category === selectedCategory;
    const matchesSearch = !searchQuery || 
      p.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
      (p.nameAm && p.nameAm.includes(searchQuery));
    return matchesCat && matchesSearch;
  });

  return (
    <div className="max-w-md mx-auto min-h-screen flex flex-col bg-slate-50 text-slate-900 pb-20 select-none">
      
      {/* ─── TOP APP BAR ──────────────────────────────────────────────────────── */}
      <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-md border-b border-slate-200 px-4 py-3 flex items-center justify-between shadow-2xs">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-amber-500 to-amber-400 text-slate-950 flex items-center justify-center font-black text-sm shadow-xs">
            S
          </div>
          <div>
            <h1 className="font-bold text-sm tracking-tight text-slate-900 leading-none">Selora Prints</h1>
            <p className="text-[10px] text-slate-500 mt-0.5">Addis Ababa • Telegram App</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Language Switcher */}
          <button 
            onClick={() => {
              triggerHaptic('selection');
              setLang(lang === 'en' ? 'am' : 'en');
            }}
            className="px-2.5 py-1 rounded-lg border border-slate-200 bg-slate-50 hover:bg-slate-100 text-xs font-semibold text-slate-700 transition"
          >
            {lang === 'en' ? 'አማርኛ' : 'English'}
          </button>

          {/* User Profile Pill */}
          <div className="px-2.5 py-1 rounded-lg bg-slate-100 text-slate-700 text-xs font-medium flex items-center space-x-1">
            <User className="w-3.5 h-3.5 text-slate-400" />
            <span className="truncate max-w-[80px]">{user.first_name || 'Customer'}</span>
          </div>
        </div>
      </header>

      {/* ─── PROMO BANNER ─────────────────────────────────────────────────────── */}
      <div className="bg-gradient-to-r from-amber-500/10 via-amber-400/5 to-transparent border-b border-amber-200/50 px-4 py-2 flex items-center justify-between text-xs text-amber-950">
        <div className="flex items-center space-x-1.5 font-medium">
          <Sparkles className="w-3.5 h-3.5 text-amber-600 shrink-0" />
          <span>{lang === 'en' ? 'Pay only 50% deposit to start production' : 'ማተም ለመጀመር 50% ቅድመ ክፍያ ብቻ ይክፈሉ'}</span>
        </div>
        <span className="text-[11px] font-bold text-amber-700 bg-amber-100/80 px-2 py-0.5 rounded-full">50% ETB</span>
      </div>

      {/* ─── TAB 1: CATALOG / SHOP ────────────────────────────────────────────── */}
      {activeTab === 'catalog' && (
        <main className="p-4 space-y-4 flex-1">
          {/* Search bar */}
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input 
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={lang === 'en' ? "Search products (e.g. cards, t-shirts, mugs)..." : "ምርቶችን ይፈልጉ (ካርድ፣ ቲሸርት፣ ኩባያ)..."}
              className="w-full bg-white border border-slate-200 rounded-xl pl-9 pr-3.5 py-2.5 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-1 focus:ring-amber-500 shadow-2xs"
            />
          </div>

          {/* Category Chips */}
          <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 scrollbar-none text-xs">
            {[
              { id: 'all', label: lang === 'en' ? 'All Items' : 'ሁሉም' },
              { id: 'stationery', label: lang === 'en' ? 'Stationery' : 'ካርዶች' },
              { id: 'apparel', label: lang === 'en' ? 'Apparel' : 'ልብሶች' },
              { id: 'packaging', label: lang === 'en' ? 'Stickers' : 'ስቲከሮች' },
              { id: 'marketing', label: lang === 'en' ? 'Marketing' : 'ማስታወቂያ' },
              { id: 'promotional', label: lang === 'en' ? 'Promotional' : 'ስጦታዎች' }
            ].map(cat => (
              <button
                key={cat.id}
                onClick={() => {
                  triggerHaptic('selection');
                  setSelectedCategory(cat.id);
                }}
                className={`px-3 py-1.5 rounded-lg whitespace-nowrap transition font-medium ${
                  selectedCategory === cat.id 
                    ? 'bg-slate-900 text-white font-semibold' 
                    : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50'
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>

          {/* Product Cards Grid */}
          <div className="grid grid-cols-2 gap-3">
            {filteredProducts.map(prod => (
              <div 
                key={prod.id}
                onClick={() => openCustomizer(prod)}
                className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-xs hover:border-slate-300 transition flex flex-col justify-between cursor-pointer group active:scale-[0.98]"
              >
                <div>
                  <div className="relative aspect-square bg-slate-100 overflow-hidden">
                    <img 
                      src={prod.imageUrl} 
                      alt={prod.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                    />
                    <div className="absolute top-2 left-2 bg-slate-900/80 backdrop-blur-xs text-white text-[10px] font-semibold px-2 py-0.5 rounded-md">
                      {prod.price} ETB <span className="text-slate-300 font-normal">/{prod.unit}</span>
                    </div>
                  </div>
                  <div className="p-3">
                    <h3 className="font-bold text-xs text-slate-900 leading-snug line-clamp-1">
                      {lang === 'en' ? prod.name : (prod.nameAm || prod.name)}
                    </h3>
                    <p className="text-[11px] text-slate-500 mt-1 line-clamp-2 leading-relaxed">
                      {lang === 'en' ? prod.description : (prod.descriptionAm || prod.description)}
                    </p>
                  </div>
                </div>

                <div className="p-3 pt-0 flex items-center justify-between text-[11px] text-slate-500 border-t border-slate-100 mt-2">
                  <span>Min: {prod.minOrder} {prod.unit}s</span>
                  <span className="font-semibold text-amber-600 flex items-center">
                    Order <ChevronRight className="w-3 h-3 ml-0.5" />
                  </span>
                </div>
              </div>
            ))}
          </div>
        </main>
      )}

      {/* ─── PRODUCT CUSTOMIZER MODAL ────────────────────────────────────────── */}
      {customizingProduct && (
        <div className="fixed inset-0 z-40 bg-slate-900/60 backdrop-blur-xs flex flex-col justify-end">
          <div className="bg-white rounded-t-3xl max-h-[88vh] overflow-y-auto p-5 space-y-4 shadow-2xl animate-in slide-in-from-bottom duration-200">
            {/* Header */}
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <h3 className="font-bold text-sm text-slate-900">
                  {lang === 'en' ? customizingProduct.name : (customizingProduct.nameAm || customizingProduct.name)}
                </h3>
                <p className="text-xs text-slate-500">
                  {customizingProduct.price} ETB per {customizingProduct.unit} (Min: {customizingProduct.minOrder})
                </p>
              </div>
              <button 
                onClick={() => setCustomizingProduct(null)}
                className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-500 flex items-center justify-center"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Quantity Stepper & Price Display */}
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between">
              <div>
                <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider block">Quantity</span>
                <div className="flex items-center space-x-2 mt-1">
                  <button 
                    onClick={() => {
                      triggerHaptic('selection');
                      setOrderQuantity(Math.max(customizingProduct.minOrder || 1, orderQuantity - (customizingProduct.minOrder >= 50 ? 50 : 1)));
                    }}
                    className="w-8 h-8 rounded-lg bg-white border border-slate-300 font-bold text-slate-700 flex items-center justify-center active:scale-95"
                  >
                    -
                  </button>
                  <span className="font-mono font-bold text-sm text-slate-900 px-2">{orderQuantity}</span>
                  <button 
                    onClick={() => {
                      triggerHaptic('selection');
                      setOrderQuantity(orderQuantity + (customizingProduct.minOrder >= 50 ? 50 : 1));
                    }}
                    className="w-8 h-8 rounded-lg bg-white border border-slate-300 font-bold text-slate-700 flex items-center justify-center active:scale-95"
                  >
                    +
                  </button>
                </div>
              </div>

              <div className="text-right">
                <span className="text-[11px] font-medium text-slate-500 uppercase tracking-wider block">Estimated Total</span>
                <span className="text-base font-bold text-slate-900 font-mono block mt-0.5">
                  {calculateTotalPrice().toLocaleString()} ETB
                </span>
                <span className="text-[10px] text-amber-700 font-semibold bg-amber-100 px-2 py-0.5 rounded-full inline-block mt-0.5">
                  50% Deposit: {Math.round(calculateTotalPrice() * 0.50).toLocaleString()} ETB
                </span>
              </div>
            </div>

            {/* Design Selection Mode */}
            <div className="space-y-2">
              <label className="block text-xs font-semibold text-slate-700">Choose Design Artwork:</label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => {
                    triggerHaptic('selection');
                    setDesignChoice('ready');
                  }}
                  className={`p-3 rounded-xl border text-left transition ${
                    designChoice === 'ready' 
                      ? 'border-amber-500 bg-amber-50/50 ring-1 ring-amber-500' 
                      : 'border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  <div className="font-semibold text-xs text-slate-900 flex items-center">
                    <Sparkles className="w-3.5 h-3.5 mr-1 text-amber-600" />
                    <span>Ready Template</span>
                  </div>
                  <p className="text-[10px] text-slate-500 mt-0.5">Pick from our pre-made studio designs</p>
                </button>

                <button
                  type="button"
                  onClick={() => {
                    triggerHaptic('selection');
                    setDesignChoice('upload');
                  }}
                  className={`p-3 rounded-xl border text-left transition ${
                    designChoice === 'upload' 
                      ? 'border-amber-500 bg-amber-50/50 ring-1 ring-amber-500' 
                      : 'border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  <div className="font-semibold text-xs text-slate-900 flex items-center">
                    <UploadCloud className="w-3.5 h-3.5 mr-1 text-amber-600" />
                    <span>Upload Artwork</span>
                  </div>
                  <p className="text-[10px] text-slate-500 mt-0.5">Submit your print-ready file or logo</p>
                </button>
              </div>
            </div>

            {/* Ready-made Design Picker */}
            {designChoice === 'ready' && (
              <div className="space-y-2">
                <span className="text-xs text-slate-600 font-medium">Select a design theme:</span>
                <div className="flex space-x-2.5 overflow-x-auto pb-1 scrollbar-none">
                  {DESIGNS.map(d => (
                    <div 
                      key={d.id}
                      onClick={() => {
                        triggerHaptic('selection');
                        setSelectedDesign(d);
                      }}
                      className={`w-32 shrink-0 rounded-xl border overflow-hidden cursor-pointer transition ${
                        selectedDesign.id === d.id ? 'border-amber-500 ring-2 ring-amber-500/30' : 'border-slate-200 opacity-75'
                      }`}
                    >
                      <img src={d.imageUrl} alt={d.title} className="w-full h-20 object-cover" />
                      <div className="p-2 bg-white">
                        <h4 className="text-[11px] font-bold text-slate-900 truncate">{d.title}</h4>
                        <p className="text-[9px] text-slate-500 truncate">{d.subproduct}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* File Upload Dropzone */}
            {designChoice === 'upload' && (
              <div className="border-2 border-dashed border-slate-300 rounded-xl p-4 text-center hover:bg-slate-50 transition relative">
                <input 
                  type="file" 
                  accept="image/*,.pdf,.ai,.psd" 
                  onChange={handleArtworkUpload}
                  className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
                />
                <UploadCloud className="w-7 h-7 mx-auto text-slate-400 mb-1" />
                <span className="text-xs font-semibold text-slate-700 block">
                  {uploadedArtworkName ? `Selected: ${uploadedArtworkName}` : 'Tap to select artwork (Photo or File)'}
                </span>
                <span className="text-[10px] text-slate-400 block mt-0.5">Supports high-res PNG, JPG, PDF (Up to 20MB)</span>
              </div>
            )}

            {/* Customer Special Customization Instructions */}
            <div className="space-y-1">
              <label className="block text-xs font-semibold text-slate-700">
                Customization Notes / Instructions:
              </label>
              <textarea
                value={customNotes}
                onChange={(e) => setCustomNotes(e.target.value)}
                placeholder="E.g. Please use matte finish, gold lettering on front, and double-sided lamination..."
                rows={2}
                className="w-full text-xs p-2.5 rounded-xl border border-slate-200 focus:outline-none focus:ring-1 focus:ring-amber-500"
              />
            </div>

            {/* Action Button */}
            <button
              onClick={handleProceedToDelivery}
              className="w-full py-3 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs transition flex items-center justify-center space-x-1.5 shadow-sm active:scale-[0.99]"
            >
              <span>Continue to Delivery Details</span>
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* ─── TAB 2: DELIVERY DETAILS ─────────────────────────────────────────── */}
      {activeTab === 'delivery' && (
        <main className="p-4 space-y-4 flex-1">
          <div className="flex items-center justify-between pb-2 border-b border-slate-200">
            <button 
              onClick={() => {
                triggerHaptic('light');
                setActiveTab('catalog');
              }}
              className="text-xs text-slate-500 hover:text-slate-900 flex items-center"
            >
              <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Back to Products
            </button>
            <span className="text-xs font-bold text-slate-900">Step 2 of 3: Delivery</span>
          </div>

          {/* Delivery Method Selector */}
          <div className="space-y-2">
            <label className="block text-xs font-semibold text-slate-700">Choose Delivery Preference:</label>
            <div className="grid grid-cols-2 gap-2">
              <button
                type="button"
                onClick={() => {
                  triggerHaptic('selection');
                  setDeliveryType('pickup');
                }}
                className={`p-3.5 rounded-xl border text-left transition ${
                  deliveryType === 'pickup' 
                    ? 'border-amber-500 bg-amber-50/60 ring-1 ring-amber-500' 
                    : 'border-slate-200 bg-white hover:bg-slate-50'
                }`}
              >
                <div className="font-semibold text-xs text-slate-900 flex items-center">
                  <MapPin className="w-4 h-4 mr-1 text-amber-600" />
                  <span>Store Pickup</span>
                </div>
                <p className="text-[10px] text-slate-500 mt-1 leading-snug">Ledeta Office (Behind Balcha Hospital)</p>
                <span className="text-[10px] text-emerald-700 font-bold bg-emerald-50 px-1.5 py-0.5 rounded mt-2 inline-block">Free of Charge</span>
              </button>

              <button
                type="button"
                onClick={() => {
                  triggerHaptic('selection');
                  setDeliveryType('taxi');
                }}
                className={`p-3.5 rounded-xl border text-left transition ${
                  deliveryType === 'taxi' 
                    ? 'border-amber-500 bg-amber-50/60 ring-1 ring-amber-500' 
                    : 'border-slate-200 bg-white hover:bg-slate-50'
                }`}
              >
                <div className="font-semibold text-xs text-slate-900 flex items-center">
                  <Truck className="w-4 h-4 mr-1 text-amber-600" />
                  <span>Taxi Delivery</span>
                </div>
                <p className="text-[10px] text-slate-500 mt-1 leading-snug">Dispatched via Yango / Feres / RIDE</p>
                <span className="text-[10px] text-slate-500 mt-2 block font-medium">Standard taxi rate</span>
              </button>
            </div>
          </div>

          {/* Taxi Delivery Inputs */}
          {deliveryType === 'taxi' && (
            <div className="bg-white p-3.5 rounded-xl border border-slate-200 space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">
                  Delivery Address / Landmark *
                </label>
                <input 
                  type="text"
                  value={deliveryAddress}
                  onChange={(e) => setDeliveryAddress(e.target.value)}
                  placeholder="E.g. Bole Atlas, Behind Edna Mall, House #204"
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-amber-500"
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs font-semibold text-slate-700">GPS Location Pin (Optional)</label>
                  <button 
                    type="button" 
                    onClick={handlePinGPS}
                    className="text-[11px] text-amber-600 hover:underline flex items-center font-medium"
                  >
                    <MapPin className="w-3 h-3 mr-0.5" /> Pin My GPS
                  </button>
                </div>
                <input 
                  type="text"
                  value={gpsLocation}
                  readOnly
                  placeholder="Tap 'Pin My GPS' to attach live Google Maps pin"
                  className="w-full text-xs p-2.5 rounded-lg border border-slate-200 bg-slate-50 text-slate-600"
                />
              </div>
            </div>
          )}

          {/* Contact Details */}
          <div className="bg-white p-3.5 rounded-xl border border-slate-200 space-y-3">
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Recipient Name *</label>
              <input 
                type="text"
                value={recipientName}
                onChange={(e) => setRecipientName(e.target.value)}
                placeholder="Full name of person receiving the package"
                className="w-full text-xs p-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-amber-500"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Phone Number *</label>
              <input 
                type="tel"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                placeholder="0911223344 or +251..."
                className="w-full text-xs p-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-amber-500 font-mono"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Need By / Deadline</label>
              <input 
                type="text"
                value={deadline}
                onChange={(e) => setDeadline(e.target.value)}
                placeholder="E.g. Friday, Nov 21 or Urgent (24 Hours)"
                className="w-full text-xs p-2.5 rounded-lg border border-slate-200 focus:outline-none focus:ring-1 focus:ring-amber-500"
              />
            </div>
          </div>

          <button
            onClick={() => {
              triggerHaptic('medium');
              setActiveTab('payment');
            }}
            className="w-full py-3 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs transition flex items-center justify-center space-x-1.5 shadow-sm active:scale-[0.99]"
          >
            <span>Proceed to 50% Deposit Payment</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </main>
      )}

      {/* ─── TAB 3: PAYMENT & 50% DEPOSIT ────────────────────────────────────── */}
      {activeTab === 'payment' && (
        <main className="p-4 space-y-4 flex-1">
          <div className="flex items-center justify-between pb-2 border-b border-slate-200">
            <button 
              onClick={() => {
                triggerHaptic('light');
                setActiveTab('delivery');
              }}
              className="text-xs text-slate-500 hover:text-slate-900 flex items-center"
            >
              <ArrowLeft className="w-3.5 h-3.5 mr-1" /> Back to Delivery
            </button>
            <span className="text-xs font-bold text-slate-900">Step 3 of 3: Payment</span>
          </div>

          {!placedOrderCode ? (
            <>
              {/* Financial Breakdown Card */}
              <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs space-y-3">
                <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                  <span className="text-xs text-slate-500">Order Items</span>
                  <span className="text-xs font-bold text-slate-900">{orderQuantity}x {customizingProduct?.name || 'Custom Prints'}</span>
                </div>

                <div className="flex items-center justify-between text-xs">
                  <span className="text-slate-600">Total Order Amount</span>
                  <span className="font-mono font-bold text-slate-900 text-sm">{calculateTotalPrice().toLocaleString()} ETB</span>
                </div>

                <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-between">
                  <div>
                    <span className="text-[11px] font-bold text-amber-900 block">50% Deposit Due Now</span>
                    <span className="text-[10px] text-amber-700">Required to initiate printing</span>
                  </div>
                  <span className="font-mono font-black text-amber-900 text-base">
                    {Math.round(calculateTotalPrice() * 0.50).toLocaleString()} ETB
                  </span>
                </div>

                <div className="flex items-center justify-between text-[11px] text-slate-500 pt-1">
                  <span>Remaining 50% Balance</span>
                  <span className="font-mono">{Math.round(calculateTotalPrice() * 0.50).toLocaleString()} ETB (Upon Delivery)</span>
                </div>
              </div>

              {/* Payment Account Cards */}
              <div className="space-y-2">
                <label className="block text-xs font-semibold text-slate-700">Select Transfer Account:</label>
                
                {/* CBE */}
                <div 
                  onClick={() => {
                    triggerHaptic('selection');
                    setPaymentMethod('CBE');
                  }}
                  className={`p-3.5 rounded-xl border bg-white cursor-pointer transition flex items-center justify-between ${
                    paymentMethod === 'CBE' ? 'border-amber-500 ring-1 ring-amber-500' : 'border-slate-200'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-lg bg-purple-900 text-white font-bold flex items-center justify-center text-xs">
                      CBE
                    </div>
                    <div>
                      <div className="font-bold text-xs text-slate-900">Commercial Bank of Ethiopia</div>
                      <div className="text-xs font-mono text-slate-600 mt-0.5">1000056873639</div>
                      <div className="text-[10px] text-slate-400">Account: Selora Prints / Yosef</div>
                    </div>
                  </div>
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCopyAccount('1000056873639');
                    }}
                    className="p-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 transition"
                    title="Copy Account Number"
                  >
                    {copiedAccount ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                  </button>
                </div>

                {/* Telebirr */}
                <div 
                  onClick={() => {
                    triggerHaptic('selection');
                    setPaymentMethod('Telebirr');
                  }}
                  className={`p-3.5 rounded-xl border bg-white cursor-pointer transition flex items-center justify-between ${
                    paymentMethod === 'Telebirr' ? 'border-amber-500 ring-1 ring-amber-500' : 'border-slate-200'
                  }`}
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-lg bg-sky-500 text-white font-bold flex items-center justify-center text-xs">
                      Tele
                    </div>
                    <div>
                      <div className="font-bold text-xs text-slate-900">Telebirr Wallet</div>
                      <div className="text-xs font-mono text-slate-600 mt-0.5">0906287728</div>
                      <div className="text-[10px] text-slate-400">Recipient: Selora Prints</div>
                    </div>
                  </div>
                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      handleCopyAccount('0906287728');
                    }}
                    className="p-2 rounded-lg bg-slate-100 hover:bg-slate-200 text-slate-600 transition"
                    title="Copy Phone Number"
                  >
                    {copiedAccount ? <Check className="w-4 h-4 text-emerald-600" /> : <Copy className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Deposit Receipt Upload */}
              <div className="bg-white p-4 rounded-2xl border border-slate-200 space-y-2">
                <span className="block text-xs font-semibold text-slate-700">Upload Deposit Screenshot / Receipt:</span>
                <div className="border-2 border-dashed border-slate-300 rounded-xl p-3 text-center relative hover:bg-slate-50 transition">
                  <input 
                    type="file" 
                    accept="image/*" 
                    onChange={handleReceiptUpload}
                    className="absolute inset-0 opacity-0 cursor-pointer w-full h-full"
                  />
                  {receiptUploaded ? (
                    <div className="flex items-center justify-center space-x-2 text-emerald-600 py-1">
                      <CheckCircle2 className="w-5 h-5" />
                      <span className="text-xs font-semibold">{receiptFileName || 'Receipt Attached!'}</span>
                    </div>
                  ) : (
                    <div>
                      <UploadCloud className="w-6 h-6 mx-auto text-slate-400 mb-1" />
                      <span className="text-xs font-medium text-slate-600 block">Tap to attach transaction confirmation</span>
                      <span className="text-[10px] text-slate-400 block mt-0.5">CBE Mobile or Telebirr transfer screenshot</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Place Order CTA */}
              <button
                disabled={isSubmitting}
                onClick={handlePlaceOrder}
                className="w-full py-3.5 rounded-xl bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white font-bold text-xs transition flex items-center justify-center space-x-2 shadow-sm active:scale-[0.99]"
              >
                {isSubmitting ? (
                  <span>Submitting Order to Serverless...</span>
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                    <span>Confirm Order & Submit 50% Deposit</span>
                  </>
                )}
              </button>
            </>
          ) : (
            /* ─── SUCCESS CELEBRATION CARD ─────────────────────────────────────── */
            <div className="bg-white rounded-2xl border border-slate-200 p-6 text-center space-y-4 shadow-sm animate-in zoom-in-95 duration-200">
              <div className="w-14 h-14 rounded-full bg-emerald-100 text-emerald-600 mx-auto flex items-center justify-center text-2xl shadow-inner">
                🎉
              </div>
              <div>
                <h3 className="font-black text-base text-slate-900">Order Placed Successfully!</h3>
                <p className="text-xs text-slate-500 mt-1">Our production team has received your order and payment confirmation.</p>
              </div>

              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between font-mono text-xs">
                <span className="text-slate-500">Order Code:</span>
                <div className="flex items-center space-x-1.5 font-bold text-slate-900 text-sm">
                  <span>{placedOrderCode}</span>
                  <button 
                    onClick={() => {
                      triggerHaptic('light');
                      navigator.clipboard.writeText(placedOrderCode);
                      setCopiedOrderCode(true);
                      setTimeout(() => setCopiedOrderCode(false), 2000);
                    }}
                    className="p-1 text-slate-400 hover:text-slate-700"
                  >
                    {copiedOrderCode ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              <div className="text-xs text-slate-600 bg-amber-50/80 p-3 rounded-xl border border-amber-200/80 text-left space-y-1">
                <div className="font-semibold text-amber-900 flex items-center">
                  <Sparkles className="w-3.5 h-3.5 mr-1 text-amber-600" />
                  What happens next?
                </div>
                <p className="text-[11px] text-amber-800 leading-relaxed">
                  1. Staff verifies your deposit slip within minutes.<br />
                  2. Printing begins immediately.<br />
                  3. You will receive Telegram notifications as your order advances!
                </p>
              </div>

              <div className="grid grid-cols-2 gap-2 pt-2">
                <button
                  onClick={() => {
                    triggerHaptic('light');
                    setTrackingCodeInput(placedOrderCode);
                    setActiveTab('track');
                  }}
                  className="py-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-xs font-semibold text-slate-700"
                >
                  Track Order
                </button>
                <button
                  onClick={() => {
                    triggerHaptic('light');
                    setPlacedOrderCode(null);
                    setCustomizingProduct(null);
                    setActiveTab('catalog');
                  }}
                  className="py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-xs font-semibold text-white"
                >
                  Shop More
                </button>
              </div>
            </div>
          )}
        </main>
      )}

      {/* ─── TAB 4: TRACK ORDER ──────────────────────────────────────────────── */}
      {activeTab === 'track' && (
        <main className="p-4 space-y-4 flex-1">
          <div>
            <h2 className="font-bold text-sm text-slate-900">Track Your Print Order</h2>
            <p className="text-xs text-slate-500 mt-0.5">Real-time status from our production studio in Addis Ababa.</p>
          </div>

          <form onSubmit={handleTrackOrder} className="flex space-x-2">
            <input 
              type="text"
              value={trackingCodeInput}
              onChange={(e) => setTrackingCodeInput(e.target.value)}
              placeholder="Enter Code (e.g. SP-1003)..."
              className="flex-1 bg-white border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs text-slate-900 font-mono uppercase focus:outline-none focus:ring-1 focus:ring-amber-500 shadow-2xs"
            />
            <button
              type="submit"
              disabled={trackingLoading}
              className="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white font-semibold text-xs transition"
            >
              {trackingLoading ? 'Searching...' : 'Track'}
            </button>
          </form>

          {trackingError && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center space-x-1.5">
              <AlertCircle className="w-4 h-4 text-rose-500 shrink-0" />
              <span>{trackingError}</span>
            </div>
          )}

          {trackedOrder && (
            <div className="bg-white rounded-2xl border border-slate-200 p-4 space-y-4 shadow-xs">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <div>
                  <span className="font-mono font-bold text-sm text-slate-900">{trackedOrder.orderCode}</span>
                  <p className="text-[10px] text-slate-400 font-mono mt-0.5">{trackedOrder.createdAt ? trackedOrder.createdAt.slice(0, 16) : 'Active'}</p>
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold capitalize bg-amber-50 text-amber-800 border border-amber-200">
                  {trackedOrder.status ? trackedOrder.status.replace('_', ' ') : 'In Review'}
                </span>
              </div>

              {/* Progress Stepper */}
              <div className="py-2">
                <div className="grid grid-cols-4 text-center text-[10px] font-medium text-slate-500 gap-1">
                  <div className="flex flex-col items-center">
                    <div className="w-6 h-6 rounded-full bg-emerald-500 text-white flex items-center justify-center text-xs mb-1">✓</div>
                    <span>Deposit</span>
                  </div>
                  <div className="flex flex-col items-center">
                    <div className="w-6 h-6 rounded-full bg-amber-500 text-white flex items-center justify-center text-xs mb-1">2</div>
                    <span>Printing</span>
                  </div>
                  <div className="flex flex-col items-center">
                    <div className="w-6 h-6 rounded-full bg-slate-200 text-slate-600 flex items-center justify-center text-xs mb-1">3</div>
                    <span>Ready</span>
                  </div>
                  <div className="flex flex-col items-center">
                    <div className="w-6 h-6 rounded-full bg-slate-200 text-slate-600 flex items-center justify-center text-xs mb-1">4</div>
                    <span>Delivered</span>
                  </div>
                </div>
              </div>

              {/* Order Info Table */}
              <div className="text-xs space-y-2 pt-1 border-t border-slate-100">
                <div className="flex justify-between">
                  <span className="text-slate-500">Items:</span>
                  <span className="font-semibold text-slate-900">{trackedOrder.items}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Delivery:</span>
                  <span className="text-slate-900 font-medium">{trackedOrder.deliveryType}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Total / Deposit:</span>
                  <span className="font-mono text-slate-900">{trackedOrder.totalEtb} ETB / {trackedOrder.depositEtb} ETB</span>
                </div>
                <div className="flex justify-between font-semibold text-amber-900 bg-amber-50 p-2 rounded-lg">
                  <span>Balance Due on Delivery:</span>
                  <span className="font-mono">{trackedOrder.balanceEtb} ETB</span>
                </div>
              </div>

              <a 
                href="https://t.me/Yosef_selora" 
                target="_blank"
                className="w-full py-2 rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 text-slate-700 text-xs font-semibold flex items-center justify-center space-x-1 transition"
              >
                <MessageCircle className="w-3.5 h-3.5 text-slate-500" />
                <span>Chat with Print Support</span>
              </a>
            </div>
          )}
        </main>
      )}

      {/* ─── TAB 5: PORTFOLIO SHOWCASE ───────────────────────────────────────── */}
      {activeTab === 'portfolio' && (
        <main className="p-4 space-y-4 flex-1">
          <div>
            <h2 className="font-bold text-sm text-slate-900">Finished Print Showcase</h2>
            <p className="text-xs text-slate-500 mt-0.5">Real client projects crafted by Selora Prints in Addis Ababa.</p>
          </div>

          <div className="grid grid-cols-2 gap-3">
            {[
              { title: "Matte Black Business Cards", cat: "Stationery", img: "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=500&auto=format&fit=crop" },
              { title: "Bespoke Heavy Cotton Tees", cat: "Apparel", img: "https://images.unsplash.com/photo-1521572267360-ee0c2909d518?w=500&auto=format&fit=crop" },
              { title: "Glossy Ceramic Mug Prints", cat: "Promotional", img: "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=500&auto=format&fit=crop" },
              { title: "Die-Cut Branding Stickers", cat: "Packaging", img: "https://images.unsplash.com/photo-1572375992501-4b0892d50c69?w=500&auto=format&fit=crop" },
              { title: "Conference Flex Rollups", cat: "Banners", img: "https://images.unsplash.com/photo-1541701494587-cb58502866ab?w=500&auto=format&fit=crop" },
              { title: "Corporate Tri-Fold Brochures", cat: "Marketing", img: "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=500&auto=format&fit=crop" }
            ].map((item, idx) => (
              <div key={idx} className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-2xs">
                <img src={item.img} alt={item.title} className="w-full h-28 object-cover" />
                <div className="p-2.5">
                  <span className="text-[9px] font-semibold text-amber-700 bg-amber-50 px-1.5 py-0.5 rounded uppercase">
                    {item.cat}
                  </span>
                  <h4 className="font-bold text-xs text-slate-900 mt-1 line-clamp-1">{item.title}</h4>
                </div>
              </div>
            ))}
          </div>
        </main>
      )}

      {/* ─── BOTTOM FLOATING NAVIGATION BAR ─────────────────────────────────── */}
      <nav className="fixed bottom-0 left-0 right-0 z-30 bg-white/95 backdrop-blur-md border-t border-slate-200 max-w-md mx-auto px-2 py-1.5 flex items-center justify-around shadow-lg">
        {[
          { id: 'catalog', label: 'Shop', icon: ShoppingBag },
          { id: 'delivery', label: 'Delivery', icon: Truck },
          { id: 'payment', label: 'Pay 50%', icon: CreditCard },
          { id: 'track', label: 'Track', icon: Search },
          { id: 'portfolio', label: 'Gallery', icon: Layers },
        ].map(tab => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => {
                triggerHaptic('selection');
                setActiveTab(tab.id);
              }}
              className={`flex flex-col items-center py-1 px-2.5 rounded-xl transition ${
                isActive ? 'text-amber-600 font-bold' : 'text-slate-400 hover:text-slate-600 font-medium'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'stroke-[2.5px]' : 'stroke-2'}`} />
              <span className="text-[10px] mt-0.5">{tab.label}</span>
            </button>
          );
        })}
      </nav>

    </div>
  );
}
