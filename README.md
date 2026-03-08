# 🧱 LEGO Minifigure Price Finder — Telegram Mini App

A Telegram Mini App for LEGO collectors to search real-time prices of minifigures on **BrickLink** and **Avito**, plus **AI-powered photo recognition**.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🔍 Price Search | Search by name or BrickLink ID (e.g. `sw0001`) |
| 💰 BrickLink Prices | Average, min, max prices in USD |
| 🛒 Avito Prices | Russian market listings in RUB |
| 📷 AI Photo Scan | Photo → Claude AI → identifies the figure |
| 🌐 Bilingual | English & Russian interface |

---

## 🚀 Quick Start

### 1. Clone & configure

```bash
git clone <repo>
cd lego-miniapp
cp .env.example .env
# Edit .env with your API keys
```

### 2. Get API Keys

#### Telegram Bot
1. Message [@BotFather](https://t.me/BotFather) → `/newbot`
2. Copy the token → `BOT_TOKEN`

#### BrickLink API
1. Go to [BrickLink Developer Console](https://www.bricklink.com/v3/api.page)
2. Register an app → get OAuth1 credentials
3. Fill: `BRICKLINK_CONSUMER_KEY`, `BRICKLINK_CONSUMER_SECRET`, `BRICKLINK_TOKEN`, `BRICKLINK_TOKEN_SECRET`

#### Avito API
1. Register at [Avito Developers](https://developers.avito.ru/)
2. Create an app → get `AVITO_CLIENT_ID` and `AVITO_CLIENT_SECRET`
3. Generate token → `AVITO_API_TOKEN`

#### Anthropic (for AI photo recognition)
1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create API key → `ANTHROPIC_API_KEY`

### 3. Deploy

```bash
# Option A: Docker Compose (recommended)
docker-compose up -d

# Option B: Manual
pip install -r backend/requirements.txt
# Terminal 1 - Web server:
uvicorn backend.server:app --host 0.0.0.0 --port 8000 --reload
# Terminal 2 - Bot:
python backend/bot.py
```

### 4. Setup Telegram Mini App

1. Message [@BotFather](https://t.me/BotFather)
2. `/newapp` → select your bot
3. Set **Web App URL** to your public HTTPS URL (e.g. via [ngrok](https://ngrok.com) for local dev)

```bash
# Local dev with ngrok:
ngrok http 8000
# Copy the https URL → set WEBAPP_URL in .env
```

---

## 📁 Project Structure

```
lego-miniapp/
├── backend/
│   ├── bot.py          # aiogram Telegram bot
│   ├── server.py       # FastAPI server + price search logic
│   └── requirements.txt
├── frontend/
│   └── index.html      # Full Mini App (HTML/CSS/JS)
├── .env.example
├── docker-compose.yml
├── Dockerfile
└── README.md
```

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Serve Mini App frontend |
| `POST` | `/api/search` | Search prices by name/ID |
| `POST` | `/api/identify` | Identify figure from photo |
| `GET` | `/health` | Health check |

### Search Request
```json
POST /api/search
{
  "query": "sw0001",
  "language": "en"
}
```

### Response
```json
{
  "query": "sw0001",
  "name": "Luke Skywalker (Tatooine)",
  "bricklink": {
    "avg_price": 12.50,
    "min_price": 8.00,
    "max_price": 25.00,
    "qty_sold": 47,
    "currency": "USD",
    "url": "https://www.bricklink.com/..."
  },
  "avito": {
    "avg_price": 1150,
    "min_price": 700,
    "max_price": 2200,
    "listings_count": 12,
    "currency": "RUB",
    "url": "https://www.avito.ru/..."
  }
}
```

---

## 🎨 UI Screens

1. **Language Selection** — Choose English or Russian on first launch
2. **Search Tab** — Type figure name/ID, see BrickLink + Avito prices side-by-side
3. **AI Photo Tab** — Take or upload photo, AI identifies the figure and shows prices

---

## ⚙️ Notes

- Without API keys configured, the app returns **demo data** for testing
- BrickLink API uses **OAuth 1.0a** — implement proper HMAC-SHA1 signing in production
- Avito scraping is a fallback — use official API token for reliability
- The Mini App requires **HTTPS** in production (use nginx + Let's Encrypt or Cloudflare)

---

## 🧱 Example BrickLink IDs to try

| ID | Figure |
|---|---|
| `sw0001` | Luke Skywalker |
| `hp001` | Harry Potter |
| `col001` | Collectible Series 1 |
| `njo001` | Lloyd (Ninja) |
| `cas001` | Black Knight |


