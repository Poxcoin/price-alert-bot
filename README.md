# Crypto Price Alert Bot

Telegram bot that notifies you when a cryptocurrency hits your target price. Uses Binance API for real-time prices — no API key required.

## Features

- Set price alerts for any coin: `/alert BTC below 50000`
- Supports `above` and `below` conditions
- Checks prices every 30 seconds
- Multiple alerts per user
- Persistent storage (SQLite)

## Commands

| Command | Description |
|---------|-------------|
| `/alert BTC below 50000` | Notify when BTC drops under $50,000 |
| `/alert ETH above 3000` | Notify when ETH rises above $3,000 |
| `/alerts` | List your active alerts with current prices |
| `/remove 1` | Delete alert by ID |

## Setup

```bash
git clone https://github.com/Poxcoin/price-alert-bot.git
cd price-alert-bot
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your bot token
python bot.py
```

Get a bot token from [@BotFather](https://t.me/BotFather) on Telegram.

## Tech Stack

- **Python 3.10+**
- **python-telegram-bot v20** (async)
- **Binance REST API** (free, no key needed)
- **SQLite** (zero-config storage)
