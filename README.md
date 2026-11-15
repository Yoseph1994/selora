# 💛 Selora Prints — Telegram Bot & Dynamic Dashboard

A complete automated business system for **Selora Prints**, featuring:
- **50% Pre-payment Deposit & Receipt Verification Flow**
- **1-Click Telegram Approval Buttons**
- **Dynamic Web Dashboard** (Real-time orders, payment receipts viewer, and dynamic price manager)
- **Telegram Premium Business Assistant** (Auto-replies to DMs on the owner's personal account)
- **Standalone Customer Bot** (@SeloraPrintsBot)
- **Multilingual AI Assistant** (English & Amharic powered by Gemini)

---

## 💰 50% Pre-payment & Approval Workflow

```
Customer Places Order
        │
        ▼
Bot prompts 50% Advance Deposit (shows CBE & Telebirr account numbers)
        │
        ▼
Customer transfers deposit & uploads payment screenshot
        │
        ▼
Bot saves order (Code: SP-1001) & stores receipt image
        │
        ▼
┌──────────────────────────────────────────────────────────────┐
│  Alert sent to Owner's Telegram & Dynamic Web Dashboard:     │
│  • View receipt image                                        │
│  • [✅ Approve Payment]  [❌ Reject]                        │
└───────────────────────────────┬──────────────────────────────┘
                                │
                        Owner Approves
                                │
                                ▼
Customer receives instant celebratory confirmation:
"🎉 Your 50% deposit for Order #SP-1001 is verified! Order is now in production!"
```

---

## 🌐 Dynamic Web Dashboard

Run `main.py` or double-click `start_selora.bat`, then open:
👉 **`http://localhost:8000`**

### 🔒 Dashboard Authentication
The dashboard is password-protected.
- **Default Username:** `admin`
- **Default Password:** `selora2026`
*(You can customize these anytime in [.env](file:///c:/Users/hp/Desktop/Kebrons/.env) via `DASHBOARD_USERNAME` and `DASHBOARD_PASSWORD`)*

### Features on the Dashboard:
1. **Live Order Pipeline:** Filter by *Review Pending*, *In Production*, *Completed*, or *Cancelled*.
2. **Receipt Inspector:** Click **"View Receipt"** to view the customer's full-resolution payment screenshot modal.
3. **1-Click Actions:** Approve deposit, mark completed, or cancel with automatic customer notification in Telegram!
4. **Dynamic Price Manager:** Change any product price live. Changes sync instantly across the Telegram Bot and AI without restarting!
5. **Export CSV:** One-click spreadsheet download for bookkeeping.

---

## 🚀 Quick Setup

### 1. Configure `.env`
Edit [.env](file:///c:/Users/hp/Desktop/Kebrons/.env):
```ini
# Bot Token from @BotFather
BOT_TOKEN=123456789:ABC...

# Owner's numeric Telegram User ID (get from @userinfobot)
ADMIN_CHAT_ID=123456789

# Owner's Telegram username
ADMIN_USERNAME=selora_prints

# 50% Pre-payment Accounts
PAYMENT_CBE_ACCOUNT=1000123456789
PAYMENT_TELEBIRR=0911223344
PAYMENT_ACCOUNT_NAME=Selora Prints
PAYMENT_DEPOSIT_PERCENT=50

# Optional: Google Gemini API key for smart AI answers
GEMINI_API_KEY=AIzaSy...
```

### 2. Connect Telegram Business (Telegram Premium)
1. On the phone with Telegram Premium, open **Settings** > **Telegram Business** > **Chatbots**.
2. Select your bot (`@SeloraPrintsBot`).
3. Turn on **"Reply to messages"**.
4. Save!

### 3. Start Both Services
Double-click **`start_selora.bat`** or run:
```powershell
python main.py
```
Both the Telegram Bot and the Dynamic Web Dashboard (`http://localhost:8000`) will be live!
