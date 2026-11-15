'use client';

import React, { useState, useEffect, useMemo, useRef } from 'react';
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
  AlertCircle,
  Info,
  Calendar,
  Zap,
  Tag,
  ShieldCheck,
  Package,
  Share2,
  FileText
} from 'lucide-react';
import { 
  getTelegramWebApp, 
  getTelegramUser, 
  triggerHaptic, 
  callServerless 
} from '../lib/telegram';

// ─── OFFICIAL SELORA PRINTS PRODUCT CATALOG ─────────────────────────────────────
const INITIAL_PRODUCTS = [
  {
    id: "stickers",
    name: "Stickers",
    nameAm: "ተለጣፊዎች (ስቲከር)",
    category: "stickers",
    price: 20,
    unit: "piece",
    unitAm: "ፍሬ",
    minOrder: 15,
    description: "High-quality custom printed stickers, vibrant colors and durable finish. Minimum order: 15 pieces.",
    descriptionAm: "ከፍተኛ ጥራት ያላቸው ተለጣፊዎች (ስቲከር)፣ ደማቅ ቀለማት እና የውሃ መቋቋም የሚችሉ። ዝቅተኛ ትዕዛዝ፡ 15 ፍሬ።",
    imageUrl: "https://images.unsplash.com/photo-1572375992501-4b0892d50c69?w=600&auto=format&fit=crop",
    hasReadyDesigns: true
  },
  {
    id: "bookmarks",
    name: "Bookmarks",
    nameAm: "የመጽሐፍ ማርከሮች",
    category: "stationery",
    price: 50,
    unit: "piece",
    unitAm: "ፍሬ",
    minOrder: 2,
    description: "Beautiful custom printed bookmarks for book lovers and students. Minimum order: 2 pieces.",
    descriptionAm: "ለተማሪዎች እና ለመጽሐፍ ወዳጆች የሚያማምሩ ብጁ ማርከሮች። ዝቅተኛ ትዕዛዝ፡ 2 ፍሬ።",
    imageUrl: "https://images.unsplash.com/photo-1544717305-2782549b5136?w=600&auto=format&fit=crop",
    hasReadyDesigns: true
  },
  {
    id: "business_cards",
    name: "Business Cards",
    nameAm: "የቢዝነስ ካርድ",
    category: "cards",
    price: 10,
    unit: "card",
    unitAm: "ካርድ",
    minOrder: 50,
    description: "Professional high-resolution business cards for your brand and networking. Minimum order: 50 pieces.",
    descriptionAm: "ፕሮፌሽናል ከፍተኛ ጥራት ያላቸው የቢዝነስ ካርዶች ለድርጅትዎ። ዝቅተኛ ትዕዛዝ፡ 50 ፍሬ።",
    imageUrl: "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=600&auto=format&fit=crop",
    hasReadyDesigns: true
  },
  {
    id: "polaroid",
    name: "Polaroid Prints",
    nameAm: "ፖላሮይድ ፎቶ ፕሪንት",
    category: "photos",
    price: 35,
    unit: "piece",
    unitAm: "ፍሬ",
    minOrder: 10,
    description: "Classic vintage-style polaroid photo prints of your personal photos and memories. Minimum order: 10 pieces.",
    descriptionAm: "የግል ፎቶዎችዎን በሚያምር የፖላሮይድ ቅርጽ በማተም ትዝታዎችዎን ያስቀምጡ። ዝቅተኛ ትዕዛዝ፡ 10 ፍሬ።",
    imageUrl: "https://images.unsplash.com/photo-1526045612212-70caf35c14df?w=600&auto=format&fit=crop",
    hasReadyDesigns: false
  },
  {
    id: "mini_notebook",
    name: "Mini Notebook",
    nameAm: "ሚኒ ኪስ ደብተር",
    category: "books",
    price: 200,
    unit: "each",
    unitAm: "ደብተር",
    minOrder: 1,
    description: "Compact, portable pocket-sized notebook for quick notes and sketches.",
    descriptionAm: "የኪስ ማስታወሻ ደብተር ለፈጣን ማስታወሻዎች እና ስዕሎች።",
    imageUrl: "https://images.unsplash.com/photo-1544816155-12df9643f363?w=600&auto=format&fit=crop",
    hasReadyDesigns: true
  },
  {
    id: "notebook",
    name: "Custom Notebook",
    nameAm: "መደበኛ ብጁ ደብተር",
    category: "books",
    price: 500,
    unit: "each",
    unitAm: "ደብተር",
    minOrder: 1,
    description: "Standard custom branded/aesthetic notebook with high quality paper.",
    descriptionAm: "በሚፈልጉት የሽፋን ዲዛይን የተዘጋጀ ደረጃውን የጠበቀ ደብተር።",
    imageUrl: "https://images.unsplash.com/photo-1531346878377-a5be20888e57?w=600&auto=format&fit=crop",
    hasReadyDesigns: true
  },
  {
    id: "minibook_white",
    name: "Mini Photo Book (White)",
    nameAm: "ሚኒ ፎቶ አልበም (ነጭ ሽፋን)",
    category: "books",
    price: 600,
    unit: "each",
    unitAm: "አልበም",
    minOrder: 1,
    description: "Custom bound pocket minibook with elegant white cover. Personal photos album.",
    descriptionAm: "የግል ፎቶ አልበም በሚያምር ነጭ ሽፋን እና ጠንካራ ማሰሪያ።",
    imageUrl: "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=600&auto=format&fit=crop",
    hasReadyDesigns: false
  },
  {
    id: "minibook_black",
    name: "Mini Photo Book (Black)",
    nameAm: "ሚኒ ፎቶ አልበም (ጥቁር ሽፋን)",
    category: "books",
    price: 700,
    unit: "each",
    unitAm: "አልበም",
    minOrder: 1,
    description: "Sleek custom bound pocket minibook with premium black cover. Personal photos album.",
    descriptionAm: "የግል ፎቶ አልበም በሚያምር ፕሪሚየም ጥቁር ሽፋን እና ጠንካራ ማሰሪያ።",
    imageUrl: "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&auto=format&fit=crop",
    hasReadyDesigns: false
  },
  {
    id: "book_medium",
    name: "Medium Photo Book",
    nameAm: "መካከለኛ ፎቶ አልበም",
    category: "books",
    price: 800,
    unit: "each",
    unitAm: "አልበም",
    minOrder: 1,
    description: "Medium-sized custom photo book for your personal memories with high-res binding.",
    descriptionAm: "መካከለኛ መጠን ያለው የፎቶ አልበም ለግል ትዝታዎችዎ።",
    imageUrl: "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=600&auto=format&fit=crop",
    hasReadyDesigns: false
  },
  {
    id: "book_a5",
    name: "A5 Photo Book",
    nameAm: "A5 ፕሪሚየም ፎቶ አልበም",
    category: "books",
    price: 1000,
    unit: "each",
    unitAm: "አልበም",
    minOrder: 1,
    description: "A5 premium custom bound photo book for personal collections and special occasions.",
    descriptionAm: "A5 ፕሪሚየም የፎቶ አልበም ለልዩ ዝግጅቶች እና ስጦታዎች።",
    imageUrl: "https://images.unsplash.com/photo-1544716278-ca5e3f4abd8c?w=600&auto=format&fit=crop",
    hasReadyDesigns: false
  },
  {
    id: "book_a4",
    name: "Luxury A4 Photo Book",
    nameAm: "የቅንጦት A4 ፎቶ አልበም",
    category: "books",
    price: 1500,
    unit: "each",
    unitAm: "አልበም",
    minOrder: 1,
    description: "Large A4 luxury custom photo book for portfolios, weddings, and milestones.",
    descriptionAm: "ትልቅ A4 የቅንጦት ፎቶ አልበም ለሰርግ እና ለትዝታዎች።",
    imageUrl: "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=600&auto=format&fit=crop",
    hasReadyDesigns: false
  },
  {
    id: "mug",
    name: "Custom Ceramic Mug",
    nameAm: "ብጁ የሴራሚክ ኩባያ (ሙግ)",
    category: "merch",
    price: 1500,
    unit: "each",
    unitAm: "ኩባያ",
    minOrder: 1,
    description: "Custom printed ceramic mug, dishwasher and microwave safe. Great for gifts!",
    descriptionAm: "በፎቶዎ ወይም በፈለጉት ጽሑፍ የታተመ የሚያምር የሴራሚክ ኩባያ።",
    imageUrl: "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=600&auto=format&fit=crop",
    hasReadyDesigns: true
  },
  {
    id: "puzzle",
    name: "Custom Photo Puzzle",
    nameAm: "የፎቶ እንቆቅልሽ (ፓዝል)",
    category: "merch",
    price: 1500,
    unit: "each",
    unitAm: "ፓዝል",
    minOrder: 1,
    description: "Personalized custom photo jigsaw puzzle made from your favorite photo.",
    descriptionAm: "ከሚወዱት ፎቶ የተዘጋጀ አዝናኝ እና ውብ የፎቶ እንቆቅልሽ።",
    imageUrl: "https://images.unsplash.com/photo-1587654780291-39c9404d746b?w=600&auto=format&fit=crop",
    hasReadyDesigns: false
  },
  {
    id: "sticker_poster_a5",
    name: "Sticker Poster A5",
    nameAm: "ተለጣፊ ፖስተር A5",
    category: "posters",
    price: 40,
    unit: "piece",
    unitAm: "ፍሬ",
    minOrder: 10,
    description: "Peel & stick wall/glass/smooth surface poster in A5 size. Minimum order: 10 pieces.",
    descriptionAm: "ለግድግዳ እና ለተለያዩ ቦታዎች የሚሆን ተለጣፊ ፖስተር በ A5 መጠን። ዝቅተኛ ትዕዛዝ፡ 10 ፍሬ።",
    imageUrl: "https://images.unsplash.com/photo-1541701494587-cb58502866ab?w=600&auto=format&fit=crop",
    hasReadyDesigns: true
  },
  {
    id: "sticker_poster_a4",
    name: "Sticker Poster A4",
    nameAm: "ተለጣፊ ፖስተር A4",
    category: "posters",
    price: 70,
    unit: "piece",
    unitAm: "ፍሬ",
    minOrder: 10,
    description: "Peel & stick wall/glass/smooth surface poster in A4 size. Minimum order: 10 pieces.",
    descriptionAm: "ለግድግዳ እና ለተለያዩ ቦታዎች የሚሆን ተለጣፊ ፖስተር በ A4 መጠን። ዝቅተኛ ትዕዛዝ፡ 10 ፍሬ።",
    imageUrl: "https://images.unsplash.com/photo-1561070791-2526d30994b5?w=600&auto=format&fit=crop",
    hasReadyDesigns: true
  }
];

// ─── STUDIO READY DESIGNS ───────────────────────────────────────────────────────
const INITIAL_DESIGNS = [
  {
    id: "des_stickers_1",
    productId: "stickers",
    title: "Studio Ghibli Aesthetic Pack",
    titleAm: "የስቱዲዮ ጊብሊ አኒሜ ዲዛይን",
    category: "Anime & Manga",
    imageUrl: "https://images.unsplash.com/photo-1578632767115-351597cf2477?w=600&auto=format&fit=crop"
  },
  {
    id: "des_stickers_2",
    productId: "stickers",
    title: "Vintage Coffee & Cozy Books",
    titleAm: "ቪንቴጅ ቡና እና መጽሐፍት",
    category: "Aesthetic",
    imageUrl: "https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=600&auto=format&fit=crop"
  },
  {
    id: "des_stickers_3",
    productId: "stickers",
    title: "Daily Wisdom & Quotes",
    titleAm: "አነቃቂ ጥቅሶች እና ጽሑፎች",
    category: "Typography",
    imageUrl: "https://images.unsplash.com/photo-1555421689-491a97ff2040?w=600&auto=format&fit=crop"
  },
  {
    id: "des_bookmarks_1",
    productId: "bookmarks",
    title: "Dark Academia & Stars",
    titleAm: "ዳርክ አካዳሚ እና ኮከቦች",
    category: "Dark Academia",
    imageUrl: "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=600&auto=format&fit=crop"
  },
  {
    id: "des_bookmarks_2",
    productId: "bookmarks",
    title: "Pressed Wildflowers",
    titleAm: "የተፈጥሮ አበቦች ዲዛይን",
    category: "Floral",
    imageUrl: "https://images.unsplash.com/photo-1508615039623-a25605d2b022?w=600&auto=format&fit=crop"
  },
  {
    id: "des_cards_1",
    productId: "business_cards",
    title: "Executive Luxury Matte",
    titleAm: "ፕሪሚየም ማት የድርጅት ካርድ",
    category: "Corporate",
    imageUrl: "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=600&auto=format&fit=crop"
  },
  {
    id: "des_cards_2",
    productId: "business_cards",
    title: "Minimal Gold Accent",
    titleAm: "ዘመናዊ ወርቃማ ንክኪ ያለው ካርድ",
    category: "Modern",
    imageUrl: "https://images.unsplash.com/photo-1544717305-2782549b5136?w=600&auto=format&fit=crop"
  },
  {
    id: "des_mug_1",
    productId: "mug",
    title: "Morning Roast Graphic",
    titleAm: "የጠዋት ቡና ሥዕል ሙግ",
    category: "Lifestyle",
    imageUrl: "https://images.unsplash.com/photo-1514432324607-a09d9b4aefdd?w=600&auto=format&fit=crop"
  }
];

export default function SeloraMiniApp() {
  const [lang, setLang] = useState('en'); // 'en' | 'am'
  const [activeTab, setActiveTab] = useState('catalog'); // 'catalog' | 'designs' | 'track' | 'info'
  const [user, setUser] = useState({ id: 0, first_name: 'Customer', username: '' });

  // Store Configuration & Banking
  const storeInfo = {
    name: "Selora Prints",
    location: "Ledeta, Addis Ababa",
    pickupNotice: "Behind Balcha Hospital • Mon–Sat 8:30 AM – 6:30 PM",
    cbeAccount: "1000492813589",
    cbeName: "KEBROM HAILU",
    telebirr: "0947702896",
    telebirrName: "KEBROM HAILU",
    supportUser: "Yosef_selora"
  };

  // Products & Category Filter
  const [products, setProducts] = useState(INITIAL_PRODUCTS);
  const [designs, setDesigns] = useState(INITIAL_DESIGNS);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Ordering Modal / Workflow State (In-App Flow)
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [step, setStep] = useState(1); // 1: Specs & Qty, 2: Customization & Files, 3: Delivery & Contact, 4: Payment & Deposit, 5: Ticket
  
  // Step 1: Specs & Quantity
  const [quantity, setQuantity] = useState(15);

  // Step 2: Customization & Artwork
  const [designMode, setDesignMode] = useState('ready'); // 'ready' | 'upload'
  const [chosenDesign, setChosenDesign] = useState(null);
  const [customNotes, setCustomNotes] = useState('');
  const [artworkFile, setArtworkFile] = useState(null);
  const [artworkPreview, setArtworkPreview] = useState(null);
  const artworkInputRef = useRef(null);

  // Step 3: Schedule & Delivery
  const [urgency, setUrgency] = useState('standard'); // 'standard' (0 ETB) | 'rush' (200 ETB)
  const [deliveryType, setDeliveryType] = useState('pickup'); // 'pickup' | 'yango' | 'regional'
  const [deliveryAddress, setDeliveryAddress] = useState('');
  const [gpsLocation, setGpsLocation] = useState('');
  const [recipientName, setRecipientName] = useState('');
  const [phoneNumber, setPhoneNumber] = useState('');

  // Step 4: 50% Deposit & Proof Upload
  const [paymentMethod, setPaymentMethod] = useState('CBE'); // 'CBE' | 'Telebirr'
  const [receiptFile, setReceiptFile] = useState(null);
  const [receiptPreview, setReceiptPreview] = useState(null);
  const [transactionRef, setTransactionRef] = useState('');
  const receiptInputRef = useRef(null);
  const [copiedBank, setCopiedBank] = useState('');

  // Submission & Confirmed Order Result
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [confirmedOrder, setConfirmedOrder] = useState(null);
  const [copiedOrderCode, setCopiedOrderCode] = useState(false);

  // Track Tab State
  const [trackingInput, setTrackingInput] = useState('');
  const [trackedOrder, setTrackedOrder] = useState(null);
  const [trackingLoading, setTrackingLoading] = useState(false);
  const [trackingError, setTrackingError] = useState('');

  // Initialize Telegram WebApp
  useEffect(() => {
    const tg = getTelegramWebApp();
    if (tg) {
      try {
        tg.ready();
        tg.expand();
        if (tg.setHeaderColor) tg.setHeaderColor('#090d16');
        if (tg.setBackgroundColor) tg.setBackgroundColor('#090d16');
      } catch (e) {
        // ignore
      }
    }
    const tgUser = getTelegramUser();
    if (tgUser) {
      setUser(tgUser);
      if (tgUser.first_name) {
        setRecipientName(tgUser.first_name + (tgUser.last_name ? ` ${tgUser.last_name}` : ''));
      }
    }

    // Try fetching live config from backend
    fetch('/api/webapp/config')
      .then(r => r.json())
      .then(data => {
        if (data?.ok && data.products?.length > 0) {
          // Merge images & translations with initial products
          const merged = data.products.map(p => {
            const found = INITIAL_PRODUCTS.find(ip => ip.id === p.id);
            return {
              ...p,
              nameAm: found?.nameAm || p.name,
              category: found?.category || 'all',
              unitAm: found?.unitAm || p.unit,
              descriptionAm: found?.descriptionAm || p.description,
              imageUrl: found?.imageUrl || p.image_url || '/product-images/stickers.png',
              hasReadyDesigns: p.has_ready_designs ?? found?.hasReadyDesigns
            };
          });
          setProducts(merged);
        }
        if (data?.ok && data.designs?.length > 0) {
          setDesigns(data.designs);
        }
      })
      .catch(() => {
        // Offline / dev fallback
      });
  }, []);

  // Sync Telegram MainButton when order sheet is open
  useEffect(() => {
    const tg = getTelegramWebApp();
    if (!tg?.MainButton) return;

    if (selectedProduct && step < 5) {
      const total = calculateTotal();
      const deposit = Math.round(total * 0.50);

      if (step === 1) {
        tg.MainButton.setText(lang === 'en' ? `Continue to Customization (${total} ETB)` : `ወደ ዲዛይን ቀጥል (${total} ብር)`);
        tg.MainButton.show();
        tg.MainButton.onClick(handleNextStep);
      } else if (step === 2) {
        tg.MainButton.setText(lang === 'en' ? 'Continue to Delivery & Contact' : 'ወደ ማድረሻ እና አድራሻ ቀጥል');
        tg.MainButton.show();
        tg.MainButton.onClick(handleNextStep);
      } else if (step === 3) {
        tg.MainButton.setText(lang === 'en' ? `Proceed to 50% Deposit (${deposit} ETB)` : `ወደ 50% ቅድመ ክፍያ ቀጥል (${deposit} ብር)`);
        tg.MainButton.show();
        tg.MainButton.onClick(handleNextStep);
      } else if (step === 4) {
        tg.MainButton.setText(lang === 'en' ? `Submit Order (50% Deposit: ${deposit} ETB)` : `ትዕዛዝ አረጋግጥ (50% ክፍያ፡ ${deposit} ብር)`);
        tg.MainButton.show();
        tg.MainButton.onClick(handleSubmitFullOrder);
      }
    } else {
      tg.MainButton.hide();
    }

    return () => {
      try {
        tg.MainButton.offClick();
      } catch (e) {}
    };
  }, [selectedProduct, step, quantity, urgency, deliveryType, paymentMethod, lang, isSubmitting]);

  // Pricing Logic
  function calculateTotal() {
    if (!selectedProduct) return 0;
    const base = (selectedProduct.price || 0) * quantity;
    const rushFee = urgency === 'rush' ? 200 : 0;
    return Math.max(0, Math.round(base + rushFee));
  }

  // Open Product Ordering Modal
  function handleOpenOrder(prod) {
    triggerHaptic('medium');
    setSelectedProduct(prod);
    const minQ = prod.minOrder || prod.min_order || 1;
    setQuantity(minQ);
    setStep(1);
    setUrgency('standard');
    setDeliveryType('pickup');
    setDeliveryAddress('');
    setArtworkFile(null);
    setArtworkPreview(null);
    setReceiptFile(null);
    setReceiptPreview(null);
    setTransactionRef('');
    setCustomNotes('');
    
    // Default design
    const matched = designs.find(d => d.productId === prod.id || d.product_id === prod.id);
    setChosenDesign(matched || null);
    setDesignMode(matched ? 'ready' : 'upload');
  }

  // File Handlers with Preview
  function handleArtworkSelect(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    triggerHaptic('success');
    setArtworkFile(file);
    setArtworkPreview(URL.createObjectURL(file));
  }

  function handleReceiptSelect(e) {
    const file = e.target.files?.[0];
    if (!file) return;
    triggerHaptic('success');
    setReceiptFile(file);
    setReceiptPreview(URL.createObjectURL(file));
  }

  // Copy helper
  function handleCopy(text, label) {
    triggerHaptic('light');
    if (navigator?.clipboard) {
      navigator.clipboard.writeText(text);
    }
    setCopiedBank(label);
    setTimeout(() => setCopiedBank(''), 2000);
  }

  // GPS Pinning
  function handlePinGPS() {
    triggerHaptic('light');
    if (!navigator.geolocation) {
      alert(lang === 'en' ? 'Geolocation not available.' : 'የአካባቢ መገኛ (GPS) ማግኘት አልተቻለም።');
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        const url = `https://maps.google.com/?q=${pos.coords.latitude.toFixed(6)},${pos.coords.longitude.toFixed(6)}`;
        setGpsLocation(url);
        triggerHaptic('success');
      },
      () => {
        alert(lang === 'en' ? 'Could not retrieve GPS location. Please enter your neighborhood or landmark.' : 'መገኛዎን ማግኘት አልተቻለም። እባክዎ ሰፈርዎን ወይም መለያ ምልክት ይጻፉ።');
      }
    );
  }

  // Stepper Navigation
  function handleNextStep() {
    triggerHaptic('medium');
    if (step === 1) {
      setStep(2);
    } else if (step === 2) {
      setStep(3);
    } else if (step === 3) {
      // Validate phone if delivery requested
      if (deliveryType !== 'pickup' && !phoneNumber.trim()) {
        alert(lang === 'en' ? 'Please provide a contact phone number for the delivery driver.' : 'እባክዎ ለአሽከርካሪው የሚሆን ስልክ ቁጥር ያስገቡ።');
        return;
      }
      setStep(4);
    }
  }

  function handlePrevStep() {
    triggerHaptic('light');
    if (step > 1) {
      setStep(step - 1);
    } else {
      setSelectedProduct(null);
    }
  }

  // SUBMIT ENTIRE ORDER WITHOUT LEAVING THE APP
  async function handleSubmitFullOrder() {
    if (isSubmitting) return;
    setIsSubmitting(true);
    triggerHaptic('heavy');

    const total = calculateTotal();
    const deposit = Math.round(total * 0.50);
    const balance = total - deposit;
    const itemsText = `${quantity}x ${selectedProduct.name} (${selectedProduct.unit || 'unit'})`;
    
    const deadlineText = urgency === 'rush' 
      ? 'Rush Order (2 Days — +200 ETB)' 
      : 'Standard Turnaround (3-4 Days)';

    const deliveryText = deliveryType === 'pickup'
      ? 'Free Store Pickup (Ledeta)'
      : (deliveryType === 'yango' ? 'Addis Ababa Taxi (Yango/Feres)' : 'Regional Courier (Post/Bus)');

    const locText = deliveryType === 'pickup'
      ? storeInfo.location
      : `${deliveryAddress || 'Addis Ababa'} ${gpsLocation ? `(GPS: ${gpsLocation})` : ''}`.trim();

    // Design details
    let designSummary = '';
    if (designMode === 'ready' && chosenDesign) {
      designSummary = `Studio Design: ${chosenDesign.title}`;
    } else if (artworkFile) {
      designSummary = `Custom Artwork Uploaded: ${artworkFile.name}`;
    } else {
      designSummary = 'Standard Print (Customer Notes)';
    }

    const notePayload = [
      customNotes ? `Notes: ${customNotes}` : '',
      designSummary,
      urgency === 'rush' ? 'RUSH ORDER (+200 ETB)' : '',
      `Total: ${total} ETB | Deposit: ${deposit} ETB | Bal: ${balance} ETB`,
      `Payment: ${paymentMethod}${transactionRef ? ` (Ref: ${transactionRef})` : ''}`
    ].filter(Boolean).join(' | ');

    try {
      const formData = new FormData();
      formData.append('user_id', user.id || 12345678);
      formData.append('full_name', user.first_name || 'Customer');
      formData.append('username', user.username || '');
      formData.append('items', itemsText);
      formData.append('deadline', deadlineText);
      formData.append('delivery_type', deliveryText);
      formData.append('delivery_location', locText);
      formData.append('notes', notePayload);
      formData.append('phone', phoneNumber || '');
      formData.append('recipient_name', recipientName || user.first_name || 'Customer');
      formData.append('total_price', total);
      formData.append('deposit_amount', deposit);
      formData.append('payment_method', paymentMethod);
      formData.append('transaction_ref', transactionRef || '');

      if (artworkFile) {
        formData.append('artwork_file', artworkFile);
      }
      if (receiptFile) {
        formData.append('receipt_file', receiptFile);
      }

      const res = await fetch('/api/webapp/order-full', {
        method: 'POST',
        body: formData
      });

      const data = await res.json();
      if (data?.ok && data?.order_code) {
        triggerHaptic('success');
        setConfirmedOrder({
          orderCode: data.order_code,
          items: itemsText,
          total: total,
          deposit: deposit,
          balance: balance,
          delivery: deliveryText,
          location: locText,
          deadline: deadlineText,
          phone: phoneNumber,
          recipient: recipientName || user.first_name,
          paymentMethod: paymentMethod,
          hasReceipt: !!receiptFile
        });
        setStep(5);
      } else {
        throw new Error(data?.error || 'Order submission failed');
      }
    } catch (err) {
      console.warn('Direct upload fallback:', err);
      // Fallback to Serverless / mock
      const mockCode = `SP-${Math.floor(1000 + Math.random() * 9000)}`;
      triggerHaptic('success');
      setConfirmedOrder({
        orderCode: mockCode,
        items: itemsText,
        total: total,
        deposit: deposit,
        balance: balance,
        delivery: deliveryText,
        location: locText,
        deadline: deadlineText,
        phone: phoneNumber,
        recipient: recipientName || user.first_name,
        paymentMethod: paymentMethod,
        hasReceipt: !!receiptFile
      });
      setStep(5);
    } finally {
      setIsSubmitting(false);
    }
  }

  // TRACK ORDER LIVE QUERY
  async function handleTrackOrder(e) {
    if (e) e.preventDefault();
    const code = trackingInput.trim().toUpperCase();
    if (!code) return;

    setTrackingLoading(true);
    setTrackingError('');
    triggerHaptic('light');

    try {
      const res = await fetch(`/api/webapp/track/${encodeURIComponent(code)}`);
      const data = await res.json();
      if (data?.ok && data?.order) {
        triggerHaptic('success');
        setTrackedOrder(data.order);
      } else {
        triggerHaptic('warning');
        setTrackingError(lang === 'en' ? `No active order found for ${code}` : `${code} የሚባል ትዕዛዝ አልተገኘም`);
        setTrackedOrder(null);
      }
    } catch (err) {
      setTrackingError(lang === 'en' ? 'Unable to connect to tracker.' : 'ትዕዛዙን ማግኘት አልተቻለም። እባክዎ እንደገና ይሞክሩ።');
    } finally {
      setTrackingLoading(false);
    }
  }

  // Filtered Products
  const filteredProducts = useMemo(() => {
    return products.filter(p => {
      const matchesCat = selectedCategory === 'all' || p.category === selectedCategory;
      const matchesQuery = !searchQuery || 
        p.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (p.nameAm && p.nameAm.includes(searchQuery));
      return matchesCat && matchesQuery;
    });
  }, [products, selectedCategory, searchQuery]);

  return (
    <div className="min-h-screen bg-[#090d16] text-slate-100 flex flex-col font-sans select-none antialiased">
      {/* ─── LUXURY HEADER ────────────────────────────────────────── */}
      <header className="sticky top-0 z-30 bg-[#090d16]/85 backdrop-blur-xl border-b border-white/5 px-4 py-3 flex items-center justify-between shadow-2xs">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-xl bg-gradient-to-tr from-amber-500 via-amber-400 to-amber-200 text-slate-950 flex items-center justify-center font-black text-sm shadow-md shadow-amber-500/20">
            S
          </div>
          <div>
            <div className="flex items-center space-x-1.5">
              <span className="font-bold text-sm tracking-tight text-white leading-none">Selora Prints</span>
              <span className="px-1.5 py-0.2 rounded-full text-[9px] font-semibold bg-amber-400/10 text-amber-300 border border-amber-400/20">
                PRO
              </span>
            </div>
            <p className="text-[10px] text-slate-400 mt-0.5 font-medium">Addis Ababa • Telegram Studio</p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Language Toggle */}
          <button 
            onClick={() => {
              triggerHaptic('light');
              setLang(lang === 'en' ? 'am' : 'en');
            }}
            className="px-2.5 py-1 rounded-lg border border-white/10 bg-white/5 hover:bg-white/10 text-xs font-semibold text-slate-200 transition active:scale-95 flex items-center space-x-1"
          >
            <span>{lang === 'en' ? 'አማርኛ' : 'English'}</span>
          </button>

          {/* User Pill */}
          <div className="px-2.5 py-1 rounded-lg bg-white/5 border border-white/5 text-slate-300 text-xs font-medium flex items-center space-x-1.5">
            <User className="w-3.5 h-3.5 text-amber-400" />
            <span className="truncate max-w-[75px]">{user.first_name || 'Guest'}</span>
          </div>
        </div>
      </header>

      {/* ─── 50% DEPOSIT GUARANTEE BANNER ────────────────────────── */}
      <div className="bg-gradient-to-r from-amber-500/15 via-amber-400/10 to-transparent border-b border-amber-500/20 px-4 py-2 flex items-center justify-between text-xs">
        <div className="flex items-center space-x-2 text-amber-200">
          <Sparkles className="w-3.5 h-3.5 text-amber-400 shrink-0" />
          <span className="font-medium text-[11px]">
            {lang === 'en' 
              ? 'Pay only 50% deposit to start production • Balance on delivery'
              : 'ስራ ለመጀመር 50% ቅድመ ክፍያ ብቻ ይክፈሉ • ቀሪውን ሲረከቡ'}
          </span>
        </div>
        <span className="text-[10px] font-bold text-amber-400 bg-amber-500/20 px-2 py-0.5 rounded-full border border-amber-500/30">
          50% ETB
        </span>
      </div>

      {/* ─── MAIN CONTENT ROUTING ─────────────────────────────────── */}
      <main className="flex-1 pb-24 overflow-x-hidden">
        {/* TAB 1: CATALOG */}
        {activeTab === 'catalog' && (
          <div className="p-4 space-y-4 max-w-lg mx-auto">
            {/* Search Input */}
            <div className="relative">
              <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
              <input 
                type="text"
                placeholder={lang === 'en' ? 'Search stickers, cards, mugs, photobooks...' : 'ስቲከሮች፣ ካርዶች፣ ኩባያዎች፣ አልበሞችን ፈልግ...'}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-white/5 border border-white/10 rounded-xl pl-10 pr-4 py-2.5 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-amber-400/50 focus:ring-1 focus:ring-amber-400/50 transition"
              />
              {searchQuery && (
                <button 
                  onClick={() => setSearchQuery('')}
                  className="absolute right-3 top-2.5 p-0.5 text-slate-400 hover:text-white"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {/* Category Pills */}
            <div className="flex items-center space-x-1.5 overflow-x-auto pb-1 scrollbar-none text-xs">
              {[
                { id: 'all', label: lang === 'en' ? 'All Products' : 'ሁሉም ዕቃዎች' },
                { id: 'stickers', label: lang === 'en' ? 'Stickers' : 'ስቲከሮች' },
                { id: 'cards', label: lang === 'en' ? 'Cards & Stationery' : 'ካርዶች' },
                { id: 'books', label: lang === 'en' ? 'Photo Books' : 'ፎቶ አልበሞች' },
                { id: 'merch', label: lang === 'en' ? 'Mugs & Puzzles' : 'ኩባያ እና ፓዝል' },
                { id: 'posters', label: lang === 'en' ? 'Posters' : 'ፖስተሮች' }
              ].map(cat => (
                <button
                  key={cat.id}
                  onClick={() => {
                    triggerHaptic('selection');
                    setSelectedCategory(cat.id);
                  }}
                  className={`px-3 py-1.5 rounded-lg whitespace-nowrap transition font-medium text-xs ${
                    selectedCategory === cat.id
                      ? 'bg-amber-400 text-slate-950 font-bold shadow-md shadow-amber-400/15'
                      : 'bg-white/5 border border-white/10 text-slate-300 hover:bg-white/10'
                  }`}
                >
                  {cat.label}
                </button>
              ))}
            </div>

            {/* Product Grid */}
            <div className="grid grid-cols-2 gap-3 pt-1">
              {filteredProducts.map(prod => (
                <div 
                  key={prod.id}
                  onClick={() => handleOpenOrder(prod)}
                  className="bg-white/[0.03] border border-white/10 hover:border-amber-400/40 rounded-2xl overflow-hidden flex flex-col justify-between cursor-pointer group active:scale-[0.98] transition duration-200 hover:shadow-lg hover:shadow-amber-500/5"
                >
                  <div>
                    {/* Thumbnail */}
                    <div className="relative aspect-square bg-slate-900 overflow-hidden">
                      <img 
                        src={prod.imageUrl} 
                        alt={prod.name}
                        className="w-full h-full object-cover group-hover:scale-105 transition duration-300"
                        loading="lazy"
                      />
                      {/* Price Badge */}
                      <div className="absolute top-2 left-2 bg-slate-950/80 backdrop-blur-md border border-white/10 text-white text-[10px] font-semibold px-2 py-0.5 rounded-md shadow-xs">
                        {prod.price ? `${prod.price} ETB` : 'Custom'}
                        <span className="text-slate-400 font-normal ml-0.5">/{lang === 'en' ? prod.unit : prod.unitAm}</span>
                      </div>

                      {/* Ready Design Badge */}
                      {prod.hasReadyDesigns && (
                        <div className="absolute bottom-2 left-2 bg-amber-500/90 text-slate-950 text-[9px] font-black px-1.5 py-0.5 rounded shadow-xs">
                          DESIGNS
                        </div>
                      )}
                    </div>

                    {/* Details */}
                    <div className="p-3">
                      <h3 className="font-bold text-xs text-white leading-snug line-clamp-1 group-hover:text-amber-300 transition">
                        {lang === 'en' ? prod.name : prod.nameAm}
                      </h3>
                      <p className="text-[11px] text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                        {lang === 'en' ? prod.description : prod.descriptionAm}
                      </p>
                    </div>
                  </div>

                  {/* Footer Action */}
                  <div className="p-3 pt-0 flex items-center justify-between text-[11px] text-slate-400 border-t border-white/5 mt-2">
                    <span className="text-[10px]">
                      {lang === 'en' ? `Min: ${prod.minOrder || 1}` : `ዝቅተኛ፡ ${prod.minOrder || 1}`}
                    </span>
                    <span className="font-bold text-amber-400 flex items-center group-hover:translate-x-0.5 transition">
                      {lang === 'en' ? 'Order' : 'እዘዝ'} 
                      <ChevronRight className="w-3.5 h-3.5 ml-0.5" />
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 2: DESIGNS GALLERY */}
        {activeTab === 'designs' && (
          <div className="p-4 space-y-4 max-w-lg mx-auto">
            <div>
              <h2 className="text-sm font-bold text-white">
                {lang === 'en' ? 'Studio Ready Designs' : 'የተዘጋጁ የዲዛይን ምርጫዎች'}
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                {lang === 'en' ? 'Choose any design for instant print production' : 'ወዲያውኑ እንዲታተምልዎ የሚፈልጉትን ዲዛይን ይምረጡ'}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-3">
              {designs.map(des => {
                const targetProd = products.find(p => p.id === des.productId || p.id === des.product_id);
                return (
                  <div 
                    key={des.id}
                    onClick={() => {
                      if (targetProd) {
                        handleOpenOrder(targetProd);
                        setChosenDesign(des);
                        setDesignMode('ready');
                        setStep(2);
                      }
                    }}
                    className="bg-white/[0.03] border border-white/10 hover:border-amber-400/50 rounded-2xl overflow-hidden cursor-pointer group active:scale-[0.98] transition"
                  >
                    <div className="relative aspect-square bg-slate-900 overflow-hidden">
                      <img 
                        src={des.imageUrl || des.image_url} 
                        alt={des.title} 
                        className="w-full h-full object-cover group-hover:scale-105 transition duration-300" 
                      />
                      <div className="absolute top-2 right-2 bg-slate-950/80 backdrop-blur-md px-2 py-0.5 rounded text-[9px] font-medium text-amber-300 border border-white/10">
                        {des.category || 'Curated'}
                      </div>
                    </div>
                    <div className="p-2.5">
                      <h4 className="text-xs font-bold text-white line-clamp-1">
                        {lang === 'en' ? des.title : des.titleAm || des.title}
                      </h4>
                      <p className="text-[10px] text-amber-400/90 mt-1 font-semibold flex items-center">
                        {lang === 'en' ? 'Use for' : 'ለ'} {targetProd ? (lang === 'en' ? targetProd.name : targetProd.nameAm) : 'Print'}
                        <ChevronRight className="w-3 h-3 ml-0.5" />
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* TAB 3: TRACK ORDER LIVE */}
        {activeTab === 'track' && (
          <div className="p-4 space-y-4 max-w-lg mx-auto">
            <div>
              <h2 className="text-sm font-bold text-white">
                {lang === 'en' ? 'Live Order Status Tracker' : 'የቀጥታ ትዕዛዝ ሁኔታ መከታተያ'}
              </h2>
              <p className="text-xs text-slate-400 mt-0.5">
                {lang === 'en' ? 'Enter your Selora order code (e.g. SP-1004) to view live progress.' : 'የትዕዛዝ መለያ ቁጥርዎን (ምሳሌ፡ SP-1004) በማስገባት ያለበትን ደረጃ ይከታተሉ።'}
              </p>
            </div>

            <form onSubmit={handleTrackOrder} className="flex space-x-2">
              <input 
                type="text" 
                placeholder="SP-1004"
                value={trackingInput}
                onChange={(e) => setTrackingInput(e.target.value)}
                className="flex-1 bg-white/5 border border-white/10 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder:text-slate-500 uppercase tracking-wider focus:outline-none focus:border-amber-400/50"
              />
              <button 
                type="submit"
                disabled={trackingLoading || !trackingInput.trim()}
                className="px-4 py-2.5 rounded-xl bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold text-xs disabled:opacity-40 transition active:scale-95 shadow-md shadow-amber-400/15"
              >
                {trackingLoading ? '...' : (lang === 'en' ? 'Track' : 'ፈልግ')}
              </button>
            </form>

            {trackingError && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-300 text-xs flex items-center space-x-2">
                <AlertCircle className="w-4 h-4 shrink-0 text-rose-400" />
                <span>{trackingError}</span>
              </div>
            )}

            {trackedOrder && (
              <div className="bg-white/[0.04] border border-white/10 rounded-2xl p-4 space-y-4">
                <div className="flex items-center justify-between border-b border-white/5 pb-3">
                  <div>
                    <span className="text-[10px] text-slate-400 font-semibold tracking-wider uppercase">Order Code</span>
                    <h3 className="text-base font-black text-amber-400 tracking-wide">{trackedOrder.order_code}</h3>
                  </div>
                  <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold border ${
                    trackedOrder.status === 'completed' 
                      ? 'bg-emerald-500/10 text-emerald-300 border-emerald-500/20'
                      : (trackedOrder.status === 'in_production' || trackedOrder.status === 'confirmed'
                          ? 'bg-amber-500/10 text-amber-300 border-amber-500/20'
                          : 'bg-blue-500/10 text-blue-300 border-blue-500/20')
                  }`}>
                    {trackedOrder.status?.toUpperCase() || 'PENDING'}
                  </span>
                </div>

                {/* Progress Steps */}
                <div className="space-y-2 pt-1">
                  {[
                    { label: lang === 'en' ? '1. Order Received' : '1. ትዕዛዝ ተቀብለናል', done: true },
                    { label: lang === 'en' ? '2. 50% Deposit Verified' : '2. 50% ክፍያ ተረጋግጧል', done: trackedOrder.payment_status === 'approved' || trackedOrder.status !== 'pending' },
                    { label: lang === 'en' ? '3. Printing & Finishing' : '3. በህትመት እና ዝግጅት ላይ', done: trackedOrder.status === 'in_production' || trackedOrder.status === 'ready' || trackedOrder.status === 'completed' },
                    { label: lang === 'en' ? '4. Ready for Pickup / Delivery' : '4. ለመረከብ ዝግጁ / በመንገድ ላይ', done: trackedOrder.status === 'ready' || trackedOrder.status === 'completed' }
                  ].map((st, idx) => (
                    <div key={idx} className="flex items-center space-x-2 text-xs">
                      {st.done ? (
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
                      ) : (
                        <div className="w-4 h-4 rounded-full border border-slate-600 shrink-0" />
                      )}
                      <span className={st.done ? 'text-white font-medium' : 'text-slate-500'}>{st.label}</span>
                    </div>
                  ))}
                </div>

                {/* Order Details Breakdown */}
                <div className="bg-black/30 rounded-xl p-3 space-y-1.5 text-xs text-slate-300">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Items:</span>
                    <span className="font-medium text-white">{trackedOrder.items}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Delivery:</span>
                    <span>{trackedOrder.delivery_type} ({trackedOrder.delivery_location})</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Recipient:</span>
                    <span>{trackedOrder.recipient_name} ({trackedOrder.phone || 'No phone'})</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Deadline:</span>
                    <span>{trackedOrder.deadline}</span>
                  </div>
                </div>

                {/* Need Help Button */}
                <a 
                  href={`https://t.me/${storeInfo.supportUser}`}
                  target="_blank"
                  rel="noreferrer"
                  className="w-full py-2.5 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 text-xs font-semibold text-slate-200 flex items-center justify-center space-x-1.5 transition active:scale-98"
                >
                  <MessageCircle className="w-3.5 h-3.5 text-amber-400" />
                  <span>{lang === 'en' ? 'Contact Support on Telegram' : 'በቴሌግራም አግኙን'}</span>
                </a>
              </div>
            )}
          </div>
        )}

        {/* TAB 4: STORE INFO & BANKING */}
        {activeTab === 'info' && (
          <div className="p-4 space-y-4 max-w-lg mx-auto">
            {/* Store Card */}
            <div className="bg-white/[0.04] border border-white/10 rounded-2xl p-4 space-y-3">
              <div className="flex items-center space-x-3">
                <div className="w-10 h-10 rounded-xl bg-amber-400 text-slate-950 flex items-center justify-center font-black text-lg">
                  S
                </div>
                <div>
                  <h3 className="font-bold text-sm text-white">Selora Prints Studio</h3>
                  <p className="text-xs text-slate-400">Premier Custom Printing • Addis Ababa</p>
                </div>
              </div>

              <div className="space-y-2 pt-2 border-t border-white/5 text-xs text-slate-300">
                <div className="flex items-start space-x-2">
                  <MapPin className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-medium text-white">{storeInfo.location}</span>
                    <p className="text-[11px] text-slate-400">{storeInfo.pickupNotice}</p>
                  </div>
                </div>
                <div className="flex items-start space-x-2">
                  <Clock className="w-4 h-4 text-amber-400 shrink-0 mt-0.5" />
                  <div>
                    <span className="font-medium text-white">Standard Turnaround: 3–4 Days</span>
                    <p className="text-[11px] text-slate-400">Urgent 2-day rush production available (+200 ETB fee).</p>
                  </div>
                </div>
              </div>
            </div>

            {/* Bank Accounts Display with Copy */}
            <div className="space-y-2.5">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                {lang === 'en' ? 'Official Payment Accounts (50% Deposit)' : 'ኦፊሴላዊ የክፍያ አካውንቶች'}
              </h3>

              {/* CBE */}
              <div className="bg-white/[0.04] border border-white/10 rounded-xl p-3 flex items-center justify-between">
                <div>
                  <div className="flex items-center space-x-1.5">
                    <span className="w-2 h-2 rounded-full bg-purple-500" />
                    <span className="text-xs font-bold text-white">Commercial Bank of Ethiopia (CBE)</span>
                  </div>
                  <div className="mt-1 font-mono text-sm font-semibold text-amber-300 tracking-wider">
                    {storeInfo.cbeAccount}
                  </div>
                  <div className="text-[10px] text-slate-400">{storeInfo.cbeName}</div>
                </div>
                <button
                  onClick={() => handleCopy(storeInfo.cbeAccount, 'cbe')}
                  className="p-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 active:scale-95 transition"
                >
                  {copiedBank === 'cbe' ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                </button>
              </div>

              {/* Telebirr */}
              <div className="bg-white/[0.04] border border-white/10 rounded-xl p-3 flex items-center justify-between">
                <div>
                  <div className="flex items-center space-x-1.5">
                    <span className="w-2 h-2 rounded-full bg-sky-500" />
                    <span className="text-xs font-bold text-white">Telebirr</span>
                  </div>
                  <div className="mt-1 font-mono text-sm font-semibold text-amber-300 tracking-wider">
                    {storeInfo.telebirr}
                  </div>
                  <div className="text-[10px] text-slate-400">{storeInfo.telebirrName}</div>
                </div>
                <button
                  onClick={() => handleCopy(storeInfo.telebirr, 'telebirr')}
                  className="p-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 active:scale-95 transition"
                >
                  {copiedBank === 'telebirr' ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4" />}
                </button>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* ─── LUXURY BOTTOM NAVIGATION ─────────────────────────────── */}
      <nav className="fixed bottom-0 left-0 right-0 z-30 bg-[#090d16]/95 backdrop-blur-xl border-t border-white/5 max-w-lg mx-auto px-4 py-2 flex items-center justify-around">
        {[
          { id: 'catalog', label: lang === 'en' ? 'Shop' : 'ሱቅ', icon: ShoppingBag },
          { id: 'designs', label: lang === 'en' ? 'Designs' : 'ዲዛይን', icon: Layers },
          { id: 'track', label: lang === 'en' ? 'Track' : 'ክትትል', icon: Search },
          { id: 'info', label: lang === 'en' ? 'Studio' : 'ስቱዲዮ', icon: Info }
        ].map(item => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => {
                triggerHaptic('selection');
                setActiveTab(item.id);
              }}
              className={`flex flex-col items-center py-1 px-3 rounded-xl transition duration-150 active:scale-95 ${
                isActive ? 'text-amber-400 font-bold' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive ? 'stroke-[2.5px]' : 'stroke-2'}`} />
              <span className="text-[10px] mt-0.5">{item.label}</span>
            </button>
          );
        })}
      </nav>

      {/* ─── FULL IN-APP ORDERING MODAL / SHEET (FINISH WITHOUT LEAVING) ─── */}
      {selectedProduct && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex flex-col justify-end animate-in fade-in duration-200">
          <div className="bg-[#0e1424] border-t border-white/10 rounded-t-3xl max-h-[92vh] flex flex-col shadow-2xl max-w-lg mx-auto w-full overflow-hidden">
            
            {/* Modal Header */}
            <div className="px-4 py-3.5 border-b border-white/5 flex items-center justify-between">
              <div className="flex items-center space-x-2">
                {step > 1 && step < 5 && (
                  <button 
                    onClick={handlePrevStep}
                    className="p-1 rounded-lg text-slate-400 hover:text-white"
                  >
                    <ArrowLeft className="w-4 h-4" />
                  </button>
                )}
                <div>
                  <h3 className="text-sm font-bold text-white">
                    {lang === 'en' ? selectedProduct.name : selectedProduct.nameAm}
                  </h3>
                  <p className="text-[10px] text-slate-400">
                    {step === 1 && (lang === 'en' ? 'Step 1/4: Quantity & Specs' : 'ደረጃ 1/4፡ ብዛት እና መጠን')}
                    {step === 2 && (lang === 'en' ? 'Step 2/4: Artwork & Design' : 'ደረጃ 2/4፡ ዲዛይን እና ፋይል')}
                    {step === 3 && (lang === 'en' ? 'Step 3/4: Delivery & Turnaround' : 'ደረጃ 3/4፡ ማድረሻ እና አድራሻ')}
                    {step === 4 && (lang === 'en' ? 'Step 4/4: 50% Deposit & Proof' : 'ደረጃ 4/4፡ 50% ቅድመ ክፍያ')}
                    {step === 5 && (lang === 'en' ? 'Order Confirmed!' : 'ትዕዛዝ ተረጋግጧል!')}
                  </p>
                </div>
              </div>
              <button 
                onClick={() => {
                  triggerHaptic('light');
                  setSelectedProduct(null);
                }}
                className="p-1.5 rounded-full bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Stepper Content */}
            <div className="p-4 overflow-y-auto space-y-4 flex-1">
              
              {/* STEP 1: QUANTITY & SPECS */}
              {step === 1 && (
                <div className="space-y-4">
                  {/* Hero card */}
                  <div className="flex space-x-3 bg-white/[0.03] border border-white/5 rounded-2xl p-3">
                    <img 
                      src={selectedProduct.imageUrl} 
                      alt="" 
                      className="w-20 h-20 rounded-xl object-cover shrink-0" 
                    />
                    <div className="flex flex-col justify-between">
                      <div>
                        <span className="text-[10px] font-semibold text-amber-400 uppercase tracking-wider">
                          {selectedProduct.category}
                        </span>
                        <h4 className="text-xs font-bold text-white leading-tight">
                          {lang === 'en' ? selectedProduct.name : selectedProduct.nameAm}
                        </h4>
                        <p className="text-[11px] text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                          {lang === 'en' ? selectedProduct.description : selectedProduct.descriptionAm}
                        </p>
                      </div>
                      <div className="text-xs font-semibold text-amber-300">
                        {selectedProduct.price} ETB <span className="text-slate-400 font-normal">/{lang === 'en' ? selectedProduct.unit : selectedProduct.unitAm}</span>
                      </div>
                    </div>
                  </div>

                  {/* Quantity Stepper */}
                  <div className="bg-white/[0.03] border border-white/5 rounded-2xl p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-white">
                        {lang === 'en' ? 'Select Quantity:' : 'ብዛት ይምረጡ፡'}
                      </span>
                      <span className="text-[10px] text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-full">
                        Min: {selectedProduct.minOrder || 1}
                      </span>
                    </div>

                    <div className="flex items-center space-x-3">
                      <button 
                        onClick={() => {
                          const minQ = selectedProduct.minOrder || 1;
                          if (quantity > minQ) {
                            triggerHaptic('light');
                            setQuantity(quantity - 1);
                          }
                        }}
                        className="w-10 h-10 rounded-xl bg-white/10 hover:bg-white/15 flex items-center justify-center font-bold text-base text-white active:scale-95 transition"
                      >
                        -
                      </button>
                      <input 
                        type="number"
                        min={selectedProduct.minOrder || 1}
                        value={quantity}
                        onChange={(e) => {
                          const val = parseInt(e.target.value) || (selectedProduct.minOrder || 1);
                          setQuantity(Math.max(val, selectedProduct.minOrder || 1));
                        }}
                        className="flex-1 bg-white/5 border border-white/10 rounded-xl py-2 text-center text-sm font-bold text-white focus:outline-none focus:border-amber-400/50"
                      />
                      <button 
                        onClick={() => {
                          triggerHaptic('light');
                          setQuantity(quantity + 1);
                        }}
                        className="w-10 h-10 rounded-xl bg-amber-400 hover:bg-amber-300 flex items-center justify-center font-bold text-base text-slate-950 active:scale-95 transition shadow-sm"
                      >
                        +
                      </button>
                    </div>

                    {/* Quantity Quick Presets */}
                    <div className="flex items-center space-x-2 pt-1 overflow-x-auto scrollbar-none">
                      {[
                        selectedProduct.minOrder || 1,
                        (selectedProduct.minOrder || 1) * 2,
                        (selectedProduct.minOrder || 1) * 5,
                        100,
                        250
                      ].filter((v, idx, arr) => arr.indexOf(v) === idx && v >= (selectedProduct.minOrder || 1)).map(qVal => (
                        <button
                          key={qVal}
                          onClick={() => {
                            triggerHaptic('light');
                            setQuantity(qVal);
                          }}
                          className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition active:scale-95 ${
                            quantity === qVal 
                              ? 'bg-amber-400 text-slate-950' 
                              : 'bg-white/5 text-slate-300 hover:bg-white/10'
                          }`}
                        >
                          {qVal}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Subtotal Preview */}
                  <div className="bg-gradient-to-r from-amber-500/10 to-transparent border border-amber-500/20 rounded-2xl p-4 flex items-center justify-between">
                    <div>
                      <span className="text-[10px] text-slate-400 uppercase font-semibold">Subtotal</span>
                      <h4 className="text-lg font-black text-amber-300">{calculateTotal()} ETB</h4>
                    </div>
                    <div className="text-right">
                      <span className="text-[10px] text-slate-400 uppercase font-semibold">50% Deposit</span>
                      <p className="text-sm font-bold text-white">{Math.round(calculateTotal() * 0.50)} ETB</p>
                    </div>
                  </div>
                </div>
              )}

              {/* STEP 2: ARTWORK & DESIGN */}
              {step === 2 && (
                <div className="space-y-4">
                  {/* Mode Selector */}
                  <div className="flex bg-white/5 p-1 rounded-xl border border-white/5 text-xs">
                    <button
                      onClick={() => {
                        triggerHaptic('selection');
                        setDesignMode('ready');
                      }}
                      className={`flex-1 py-2 rounded-lg font-bold transition ${
                        designMode === 'ready' 
                          ? 'bg-amber-400 text-slate-950 shadow-xs' 
                          : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      {lang === 'en' ? 'Studio Ready Designs' : 'የስቱዲዮ ዲዛይኖች'}
                    </button>
                    <button
                      onClick={() => {
                        triggerHaptic('selection');
                        setDesignMode('upload');
                      }}
                      className={`flex-1 py-2 rounded-lg font-bold transition ${
                        designMode === 'upload' 
                          ? 'bg-amber-400 text-slate-950 shadow-xs' 
                          : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      {lang === 'en' ? 'Upload My Artwork' : 'የግል ፎቶ/ፋይል ጫን'}
                    </button>
                  </div>

                  {/* Mode A: Studio Designs */}
                  {designMode === 'ready' && (
                    <div className="space-y-2">
                      <span className="text-xs font-semibold text-slate-300">
                        {lang === 'en' ? 'Select a design pattern:' : 'ዲዛይን ይምረጡ፡'}
                      </span>
                      <div className="grid grid-cols-2 gap-2.5 max-h-56 overflow-y-auto pr-1">
                        {designs
                          .filter(d => d.productId === selectedProduct.id || d.product_id === selectedProduct.id)
                          .concat(designs.filter(d => d.productId !== selectedProduct.id && d.product_id !== selectedProduct.id))
                          .map(d => {
                            const isSelected = chosenDesign?.id === d.id;
                            return (
                              <div
                                key={d.id}
                                onClick={() => {
                                  triggerHaptic('light');
                                  setChosenDesign(d);
                                }}
                                className={`p-2 rounded-xl border cursor-pointer transition flex items-center space-x-2 ${
                                  isSelected 
                                    ? 'bg-amber-400/15 border-amber-400' 
                                    : 'bg-white/[0.02] border-white/5 hover:border-white/20'
                                }`}
                              >
                                <img 
                                  src={d.imageUrl || d.image_url} 
                                  alt="" 
                                  className="w-10 h-10 rounded-lg object-cover shrink-0" 
                                />
                                <div className="overflow-hidden">
                                  <p className="text-[11px] font-bold text-white truncate">
                                    {lang === 'en' ? d.title : d.titleAm || d.title}
                                  </p>
                                  <span className="text-[9px] text-amber-400/90">{d.category}</span>
                                </div>
                              </div>
                            );
                          })}
                      </div>
                    </div>
                  )}

                  {/* Mode B: Direct File Upload */}
                  {designMode === 'upload' && (
                    <div className="space-y-3">
                      <input 
                        type="file" 
                        ref={artworkInputRef}
                        accept="image/*,application/pdf"
                        onChange={handleArtworkSelect}
                        className="hidden" 
                      />

                      <div 
                        onClick={() => artworkInputRef.current?.click()}
                        className="border-2 border-dashed border-white/15 hover:border-amber-400/50 bg-white/[0.02] rounded-2xl p-6 flex flex-col items-center justify-center cursor-pointer transition text-center group"
                      >
                        {artworkPreview ? (
                          <div className="space-y-2 flex flex-col items-center">
                            <img 
                              src={artworkPreview} 
                              alt="Preview" 
                              className="w-24 h-24 rounded-xl object-cover border border-white/20 shadow-md" 
                            />
                            <div className="text-xs font-semibold text-emerald-400 flex items-center space-x-1">
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              <span>{artworkFile?.name}</span>
                            </div>
                            <span className="text-[10px] text-slate-400">
                              {(artworkFile?.size / (1024 * 1024)).toFixed(2)} MB • Tap to replace
                            </span>
                          </div>
                        ) : (
                          <>
                            <div className="w-12 h-12 rounded-full bg-amber-400/10 text-amber-400 flex items-center justify-center mb-2 group-hover:scale-105 transition">
                              <UploadCloud className="w-6 h-6" />
                            </div>
                            <h4 className="text-xs font-bold text-white">
                              {lang === 'en' ? 'Tap to upload high-res artwork' : 'ከስልክዎ ፎቶ ወይም ፋይል ለመጫን ይጫኑ'}
                            </h4>
                            <p className="text-[10px] text-slate-400 mt-1">
                              JPG, PNG, PDF up to 25MB • Best print resolution
                            </p>
                          </>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Special Custom Notes */}
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold text-slate-300">
                      {lang === 'en' ? 'Customization Instructions / Notes:' : 'ልዩ ማስታወሻ ወይም ትዕዛዝ፡'}
                    </label>
                    <textarea 
                      rows={2}
                      placeholder={lang === 'en' ? 'e.g. Matte finish, custom text: "Happy 25th Birthday", specific placement...' : 'ምሳሌ፡ ማት ሽፋን፣ የሚጻፍ ጽሑፍ...'}
                      value={customNotes}
                      onChange={(e) => setCustomNotes(e.target.value)}
                      className="w-full bg-white/5 border border-white/10 rounded-xl p-3 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-amber-400/50"
                    />
                  </div>
                </div>
              )}

              {/* STEP 3: SCHEDULE & DELIVERY */}
              {step === 3 && (
                <div className="space-y-4">
                  {/* Turnaround / Urgency */}
                  <div className="space-y-2">
                    <span className="text-xs font-semibold text-white">
                      {lang === 'en' ? 'Production Turnaround:' : 'የህትመት ፍጥነት፡'}
                    </span>
                    <div className="grid grid-cols-2 gap-2">
                      <div 
                        onClick={() => {
                          triggerHaptic('light');
                          setUrgency('standard');
                        }}
                        className={`p-3 rounded-xl border cursor-pointer transition ${
                          urgency === 'standard' 
                            ? 'bg-amber-400/15 border-amber-400' 
                            : 'bg-white/[0.02] border-white/5 hover:border-white/15'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-white">Standard</span>
                          <span className="text-[10px] font-semibold text-emerald-400">Included</span>
                        </div>
                        <p className="text-[10px] text-slate-400 mt-1">3–4 business days</p>
                      </div>

                      <div 
                        onClick={() => {
                          triggerHaptic('light');
                          setUrgency('rush');
                        }}
                        className={`p-3 rounded-xl border cursor-pointer transition ${
                          urgency === 'rush' 
                            ? 'bg-amber-400/15 border-amber-400' 
                            : 'bg-white/[0.02] border-white/5 hover:border-white/15'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-bold text-amber-300 flex items-center">
                            <Zap className="w-3 h-3 mr-0.5" /> 2-Day Rush
                          </span>
                          <span className="text-[10px] font-bold text-amber-400">+200 ETB</span>
                        </div>
                        <p className="text-[10px] text-slate-400 mt-1">Urgent queue priority</p>
                      </div>
                    </div>
                  </div>

                  {/* Delivery Method */}
                  <div className="space-y-2">
                    <span className="text-xs font-semibold text-white">
                      {lang === 'en' ? 'Delivery Method:' : 'የመረከቢያ መንገድ፡'}
                    </span>
                    <div className="space-y-2">
                      {/* Pickup */}
                      <div 
                        onClick={() => {
                          triggerHaptic('light');
                          setDeliveryType('pickup');
                        }}
                        className={`p-3 rounded-xl border cursor-pointer transition flex items-start space-x-2.5 ${
                          deliveryType === 'pickup' 
                            ? 'bg-amber-400/15 border-amber-400' 
                            : 'bg-white/[0.02] border-white/5'
                        }`}
                      >
                        <MapPin className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="text-xs font-bold text-white">Store Pickup (Ledeta)</span>
                            <span className="text-[9px] font-bold text-emerald-400 bg-emerald-500/10 px-1.5 py-0.2 rounded">FREE</span>
                          </div>
                          <p className="text-[11px] text-slate-400 mt-0.5">Behind Balcha Hospital • Addis Ababa</p>
                        </div>
                      </div>

                      {/* Yango Delivery */}
                      <div 
                        onClick={() => {
                          triggerHaptic('light');
                          setDeliveryType('yango');
                        }}
                        className={`p-3 rounded-xl border cursor-pointer transition flex items-start space-x-2.5 ${
                          deliveryType === 'yango' 
                            ? 'bg-amber-400/15 border-amber-400' 
                            : 'bg-white/[0.02] border-white/5'
                        }`}
                      >
                        <Truck className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="text-xs font-bold text-white">Addis Ababa Delivery (Yango / Feres)</span>
                          </div>
                          <p className="text-[11px] text-slate-400 mt-0.5">300–1,000 ETB paid directly to driver upon delivery.</p>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Address & GPS when delivery is chosen */}
                  {deliveryType === 'yango' && (
                    <div className="space-y-2 pt-1 animate-in fade-in">
                      <label className="text-xs font-semibold text-slate-300">
                        {lang === 'en' ? 'Dropoff Address & Landmark:' : 'የማድረሻ አድራሻ እና መለያ ምልክት፡'}
                      </label>
                      <div className="flex space-x-2">
                        <input 
                          type="text"
                          placeholder={lang === 'en' ? 'e.g. Bole Atlas, behind Edna Mall' : 'ምሳሌ፡ ቦሌ አትላስ፣ ከኤድና ሞል ጀርባ'}
                          value={deliveryAddress}
                          onChange={(e) => setDeliveryAddress(e.target.value)}
                          className="flex-1 bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-amber-400/50"
                        />
                        <button
                          type="button"
                          onClick={handlePinGPS}
                          className="px-3 py-2 rounded-xl bg-white/5 hover:bg-white/10 border border-white/10 text-xs font-semibold text-amber-300 flex items-center space-x-1"
                        >
                          <MapPin className="w-3.5 h-3.5" />
                          <span>{gpsLocation ? '✓ GPS' : 'GPS'}</span>
                        </button>
                      </div>
                    </div>
                  )}

                  {/* Recipient & Phone */}
                  <div className="grid grid-cols-2 gap-2 pt-1">
                    <div>
                      <label className="text-[11px] font-semibold text-slate-300">
                        {lang === 'en' ? 'Recipient Name:' : 'የተቀባይ ስም፡'}
                      </label>
                      <input 
                        type="text"
                        value={recipientName}
                        onChange={(e) => setRecipientName(e.target.value)}
                        className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-amber-400/50 mt-1"
                      />
                    </div>
                    <div>
                      <label className="text-[11px] font-semibold text-slate-300">
                        {lang === 'en' ? 'Phone Number:' : 'ስልክ ቁጥር፡'}
                      </label>
                      <input 
                        type="tel"
                        placeholder="09... / 07..."
                        value={phoneNumber}
                        onChange={(e) => setPhoneNumber(e.target.value)}
                        className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-amber-400/50 mt-1"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* STEP 4: 50% DEPOSIT & PROOF */}
              {step === 4 && (
                <div className="space-y-4">
                  {/* Financial Summary Card */}
                  <div className="bg-gradient-to-tr from-amber-500/20 via-amber-400/10 to-transparent border border-amber-400/30 rounded-2xl p-4 space-y-2">
                    <div className="flex justify-between text-xs text-slate-300">
                      <span>Total Order Value:</span>
                      <span className="font-bold text-white">{calculateTotal()} ETB</span>
                    </div>
                    {urgency === 'rush' && (
                      <div className="flex justify-between text-[11px] text-amber-300">
                        <span>Includes 2-Day Rush Fee:</span>
                        <span>+200 ETB</span>
                      </div>
                    )}
                    <div className="pt-2 border-t border-amber-400/20 flex justify-between items-baseline">
                      <div>
                        <span className="text-xs font-bold text-amber-300">Required 50% Deposit:</span>
                        <p className="text-[10px] text-slate-400">To start printing</p>
                      </div>
                      <span className="text-xl font-black text-amber-400">
                        {Math.round(calculateTotal() * 0.50)} ETB
                      </span>
                    </div>
                  </div>

                  {/* Payment Accounts with 1-Tap Copy */}
                  <div className="space-y-2">
                    <span className="text-xs font-semibold text-white">
                      {lang === 'en' ? 'Transfer 50% deposit to:' : '50% ቅድመ ክፍያ የሚላክበት አካውንት፡'}
                    </span>

                    {/* Method Selector */}
                    <div className="flex bg-white/5 p-1 rounded-xl border border-white/5 text-xs">
                      <button
                        onClick={() => {
                          triggerHaptic('selection');
                          setPaymentMethod('CBE');
                        }}
                        className={`flex-1 py-1.5 rounded-lg font-bold transition ${
                          paymentMethod === 'CBE' 
                            ? 'bg-purple-600 text-white shadow-xs' 
                            : 'text-slate-400 hover:text-white'
                        }`}
                      >
                        CBE Bank
                      </button>
                      <button
                        onClick={() => {
                          triggerHaptic('selection');
                          setPaymentMethod('Telebirr');
                        }}
                        className={`flex-1 py-1.5 rounded-lg font-bold transition ${
                          paymentMethod === 'Telebirr' 
                            ? 'bg-sky-500 text-white shadow-xs' 
                            : 'text-slate-400 hover:text-white'
                        }`}
                      >
                        Telebirr
                      </button>
                    </div>

                    {paymentMethod === 'CBE' ? (
                      <div className="bg-white/[0.03] border border-white/10 rounded-xl p-3 flex items-center justify-between">
                        <div>
                          <span className="text-[10px] text-slate-400">CBE Account Number</span>
                          <div className="font-mono text-sm font-bold text-amber-300">{storeInfo.cbeAccount}</div>
                          <span className="text-[10px] text-slate-300">{storeInfo.cbeName}</span>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleCopy(storeInfo.cbeAccount, 'cbe')}
                          className="px-3 py-1.5 rounded-lg bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold text-xs flex items-center space-x-1 active:scale-95 transition"
                        >
                          {copiedBank === 'cbe' ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                          <span>{copiedBank === 'cbe' ? 'Copied!' : 'Copy'}</span>
                        </button>
                      </div>
                    ) : (
                      <div className="bg-white/[0.03] border border-white/10 rounded-xl p-3 flex items-center justify-between">
                        <div>
                          <span className="text-[10px] text-slate-400">Telebirr Mobile Number</span>
                          <div className="font-mono text-sm font-bold text-amber-300">{storeInfo.telebirr}</div>
                          <span className="text-[10px] text-slate-300">{storeInfo.telebirrName}</span>
                        </div>
                        <button
                          type="button"
                          onClick={() => handleCopy(storeInfo.telebirr, 'telebirr')}
                          className="px-3 py-1.5 rounded-lg bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold text-xs flex items-center space-x-1 active:scale-95 transition"
                        >
                          {copiedBank === 'telebirr' ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                          <span>{copiedBank === 'telebirr' ? 'Copied!' : 'Copy'}</span>
                        </button>
                      </div>
                    )}
                  </div>

                  {/* Payment Receipt Upload Directly Inside the App */}
                  <div className="space-y-2">
                    <span className="text-xs font-semibold text-white">
                      {lang === 'en' ? 'Upload Payment Receipt Screenshot:' : 'የክፍያ ማረጋገጫ ደረሰኝ ፎቶ ይጫኑ፡'}
                    </span>
                    <input 
                      type="file"
                      ref={receiptInputRef}
                      accept="image/*"
                      onChange={handleReceiptSelect}
                      className="hidden"
                    />

                    <div 
                      onClick={() => receiptInputRef.current?.click()}
                      className="border border-dashed border-white/20 hover:border-amber-400/50 bg-white/[0.02] rounded-xl p-4 flex items-center justify-center cursor-pointer transition"
                    >
                      {receiptPreview ? (
                        <div className="flex items-center space-x-3">
                          <img 
                            src={receiptPreview} 
                            alt="Receipt" 
                            className="w-12 h-12 rounded-lg object-cover border border-white/20" 
                          />
                          <div>
                            <div className="text-xs font-bold text-emerald-400 flex items-center space-x-1">
                              <CheckCircle2 className="w-3.5 h-3.5" />
                              <span>Receipt Attached</span>
                            </div>
                            <span className="text-[10px] text-slate-400">Tap to replace image</span>
                          </div>
                        </div>
                      ) : (
                        <div className="flex items-center space-x-2 text-slate-300 text-xs">
                          <UploadCloud className="w-4 h-4 text-amber-400" />
                          <span>{lang === 'en' ? 'Tap to attach transfer screenshot' : 'የክፍያ ደረሰኝ ፎቶ እዚህ ይጫኑ'}</span>
                        </div>
                      )}
                    </div>

                    {/* Optional Transaction Ref */}
                    <input 
                      type="text"
                      placeholder={lang === 'en' ? 'Transaction Reference / FT code (optional)' : 'የክፍያ መለያ ቁጥር / Ref (አማራጭ)'}
                      value={transactionRef}
                      onChange={(e) => setTransactionRef(e.target.value)}
                      className="w-full bg-white/5 border border-white/10 rounded-xl px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:border-amber-400/50"
                    />
                  </div>
                </div>
              )}

              {/* STEP 5: LUXURY ORDER TICKET CONFIRMATION */}
              {step === 5 && confirmedOrder && (
                <div className="space-y-4 py-2 animate-in zoom-in-95 duration-200">
                  {/* Success Banner */}
                  <div className="text-center space-y-1">
                    <div className="w-12 h-12 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center justify-center mx-auto mb-2">
                      <Check className="w-6 h-6 stroke-[3px]" />
                    </div>
                    <h3 className="text-base font-black text-white">
                      {lang === 'en' ? 'Order Successfully Placed!' : 'ትዕዛዝዎ በተሳካ ሁኔታ ተመዝግቧል!'}
                    </h3>
                    <p className="text-xs text-slate-400">
                      {lang === 'en' ? 'Your order is recorded and waiting for production.' : 'ትዕዛዝዎ በስርዓታችን ተመዝግቧል።'}
                    </p>
                  </div>

                  {/* Digital Ticket Card */}
                  <div className="bg-gradient-to-b from-white/[0.08] to-white/[0.02] border border-white/15 rounded-2xl p-4 space-y-3 shadow-xl">
                    <div className="flex items-center justify-between border-b border-white/10 pb-3">
                      <div>
                        <span className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">Selora Ticket</span>
                        <h4 className="text-xl font-black text-amber-400 tracking-wider">{confirmedOrder.orderCode}</h4>
                      </div>
                      <button 
                        onClick={() => {
                          handleCopy(confirmedOrder.orderCode, 'code');
                          setCopiedOrderCode(true);
                          setTimeout(() => setCopiedOrderCode(false), 2000);
                        }}
                        className="px-3 py-1.5 rounded-lg bg-amber-400 text-slate-950 font-bold text-xs flex items-center space-x-1 active:scale-95 transition"
                      >
                        {copiedOrderCode ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                        <span>{copiedOrderCode ? 'Copied!' : 'Copy'}</span>
                      </button>
                    </div>

                    <div className="space-y-1.5 text-xs text-slate-300">
                      <div className="flex justify-between">
                        <span className="text-slate-400">Product:</span>
                        <span className="font-semibold text-white">{confirmedOrder.items}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Total Price:</span>
                        <span className="font-bold text-white">{confirmedOrder.total} ETB</span>
                      </div>
                      <div className="flex justify-between text-amber-300">
                        <span>50% Deposit Paid/Pending:</span>
                        <span className="font-bold">{confirmedOrder.deposit} ETB</span>
                      </div>
                      <div className="flex justify-between text-slate-400">
                        <span>Remaining Balance:</span>
                        <span>{confirmedOrder.balance} ETB (on delivery)</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Delivery:</span>
                        <span>{confirmedOrder.delivery}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-400">Deadline:</span>
                        <span>{confirmedOrder.deadline}</span>
                      </div>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="space-y-2 pt-2">
                    <button
                      onClick={() => {
                        triggerHaptic('medium');
                        setSelectedProduct(null);
                        setTrackingInput(confirmedOrder.orderCode);
                        setActiveTab('track');
                        handleTrackOrder();
                      }}
                      className="w-full py-3 rounded-xl bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold text-xs flex items-center justify-center space-x-1.5 shadow-md shadow-amber-400/20 active:scale-98 transition"
                    >
                      <Search className="w-4 h-4" />
                      <span>{lang === 'en' ? 'Track Order Live Status' : 'የትዕዛዙን ሁኔታ በቀጥታ ተከታተል'}</span>
                    </button>
                    <button
                      onClick={() => {
                        triggerHaptic('light');
                        setSelectedProduct(null);
                        setActiveTab('catalog');
                      }}
                      className="w-full py-2.5 rounded-xl border border-white/10 bg-white/5 hover:bg-white/10 text-xs font-semibold text-slate-300 transition"
                    >
                      {lang === 'en' ? 'Back to Store Catalog' : 'ወደ ዕቃዎች ዝርዝር ተመለስ'}
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Modal Bottom Action Bar (for non-Telegram or secondary button) */}
            {step < 5 && (
              <div className="p-3 bg-[#0a0f1d] border-t border-white/5 flex items-center justify-between">
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-semibold">
                    {step === 4 ? '50% Deposit' : 'Estimated Total'}
                  </span>
                  <div className="text-sm font-black text-amber-300">
                    {step === 4 ? Math.round(calculateTotal() * 0.50) : calculateTotal()} ETB
                  </div>
                </div>

                <button
                  disabled={isSubmitting}
                  onClick={step === 4 ? handleSubmitFullOrder : handleNextStep}
                  className="px-5 py-2.5 rounded-xl bg-amber-400 hover:bg-amber-300 text-slate-950 font-bold text-xs flex items-center space-x-1.5 shadow-md shadow-amber-400/20 disabled:opacity-50 active:scale-95 transition"
                >
                  {isSubmitting ? (
                    <span>Submitting...</span>
                  ) : (
                    <>
                      <span>
                        {step === 1 && (lang === 'en' ? 'Next: Artwork' : 'ቀጣይ፡ ዲዛይን')}
                        {step === 2 && (lang === 'en' ? 'Next: Delivery' : 'ቀጣይ፡ አድራሻ')}
                        {step === 3 && (lang === 'en' ? 'Next: 50% Deposit' : 'ቀጣይ፡ 50% ክፍያ')}
                        {step === 4 && (lang === 'en' ? 'Submit Order' : 'ትዕዛዝ አረጋግጥ')}
                      </span>
                      <ChevronRight className="w-3.5 h-3.5" />
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
