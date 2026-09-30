import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the current directory
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN or BOT_TOKEN == "your_telegram_bot_token_here":
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in .env file!")

CHECK_INTERVAL_MINUTES = int(os.getenv("CHECK_INTERVAL_MINUTES", "15"))

raw_pairs = os.getenv("DEFAULT_PAIRS", "EURUSD=X,GBPUSD=X,USDJPY=X,GC=F,BTC-USD,ETH-USD")
DEFAULT_PAIRS = [p.strip() for p in raw_pairs.split(",") if p.strip()]

# Friendly display names for symbols
SYMBOL_NAMES = {
    # Forex
    "EURUSD=X": "EUR/USD",
    "GBPUSD=X": "GBP/USD",
    "USDJPY=X": "USD/JPY",
    "AUDUSD=X": "AUD/USD",
    "USDCAD=X": "USD/CAD",
    "USDCHF=X": "USD/CHF",
    "NZDUSD=X": "NZD/USD",
    "EURGBP=X": "EUR/GBP",
    "EURJPY=X": "EUR/JPY",
    "GBPJPY=X": "GBP/JPY",

    # Metals & Commodities
    "GC=F": "🥇 Gold (XAU/USD)",
    "XAUUSD=X": "🥇 Gold (XAU/USD)",
    "SI=F": "🥈 Silver (XAG/USD)",
    "XAGUSD=X": "🥈 Silver (XAG/USD)",
    "CL=F": "🛢️ Oil (WTI)",

    # Crypto
    "BTC-USD": "🪙 Bitcoin (BTC)",
    "ETH-USD": "💎 Ethereum (ETH)",
    "SOL-USD": "☀️ Solana (SOL)",
    "TON11419-USD": "💎 TON",
    "TON-USD": "💎 TON",
    "XRP-USD": "🚀 XRP",
}
