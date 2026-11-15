# 💛 Selora Prints — Multi-Platform Architecture

This repository contains two dedicated applications for Selora Prints:

```
Kebrons/
├── bot/        # Python Aiogram 3 Bot + FastAPI Web Dashboard + SQLite/Postgres DB
└── miniapp/    # Telegram Serverless Next.js 14 Mini App (@tgcloud)
```

---

## 🤖 1. The Bot & Web Dashboard (`/bot`)
The full-featured Python printing business bot and staff operations dashboard.
- **Aiogram 3** Telegram bot with interactive product ordering, 50% deposit receipts, design galleries, and bilingual support (EN/አማ).
- **FastAPI Web Dashboard** for production staff with separate columns (Items Ordered, Artwork/Design, Customer Notes, Pricing, Delivery, Status, Actions), packing slip printing, invoice generation, sales analytics with Chart.js, and admin security settings.
- **Deploy:** Ready for Render, Docker, or local execution (`cd bot && python main.py`).

---

## 📱 2. The Next.js Telegram Serverless Mini App (`/miniapp`)
A modern, zero-hosting-cost Telegram Mini App built on **Next.js 14** and **Telegram Native Serverless (`@tgcloud`)**.
- Built with **Next.js**, **React 18**, and **Tailwind CSS**.
- Runs directly on Telegram's native V8 isolate cloud — no external VPS or cloud provider bills.
- Built-in SQLite database powered by `@tgcloud/sdk`.
- Complete catalog, real-time 50% deposit calculations, CBE/Telebirr payment copy, GPS pin capture, and live order tracking pipeline.
- **Deploy:** `cd miniapp && npm run deploy` (automatically runs `next build && tgcloud push`).
