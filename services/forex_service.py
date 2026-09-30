import logging
import pandas as pd
import yfinance as yf
from typing import Dict, Any, Optional
from config import SYMBOL_NAMES
from services.smc_service import analyze_smc

logger = logging.getLogger(__name__)

TIMEFRAME_CONFIG = {
    "1m": {"period": "1d", "interval": "1m", "label": "1 Minute (1m)"},
    "15m": {"period": "5d", "interval": "15m", "label": "15 Minutes (15m)"},
    "30m": {"period": "1mo", "interval": "30m", "label": "30 Minutes (30m)"},
    "1h": {"period": "1mo", "interval": "1h", "label": "1 Hour (1h)"},
    "4h": {"period": "3mo", "interval": "1h", "label": "4 Hours (4h)"},
    "24h": {"period": "1y", "interval": "1d", "label": "24 Hours / 1 Day (24h)"},
    "1d": {"period": "1y", "interval": "1d", "label": "24 Hours / 1 Day (24h)"},
    "1w": {"period": "2y", "interval": "1wk", "label": "1 Week (1W)"},
}

ALIAS_MAP = {
    # Gold & Metals & Commodities
    "GOLD": "GC=F",
    "XAU": "GC=F",
    "XAUUSD": "GC=F",
    "ЗОЛОТО": "GC=F",
    "SILVER": "SI=F",
    "XAG": "SI=F",
    "XAGUSD": "SI=F",
    "СЕРЕБРО": "SI=F",
    "OIL": "CL=F",
    "WTI": "CL=F",
    "НЕФТЬ": "CL=F",

    # Crypto
    "BTC": "BTC-USD",
    "BITCOIN": "BTC-USD",
    "БИТКОИН": "BTC-USD",
    "BTCUSD": "BTC-USD",
    "ETH": "ETH-USD",
    "ETHEREUM": "ETH-USD",
    "ЭФИР": "ETH-USD",
    "ETHUSD": "ETH-USD",
    "SOL": "SOL-USD",
    "SOLANA": "SOL-USD",
    "SOLUSD": "SOL-USD",
    "TON": "TON11419-USD",
    "TONUSD": "TON11419-USD",
    "XRP": "XRP-USD",
    "XRPUSD": "XRP-USD",
    "DOGE": "DOGE-USD",
    "DOGEUSD": "DOGE-USD",
}


def normalize_symbol(symbol: str) -> str:
    """Normalizes input for Forex, Gold/Metals, Commodities, and Crypto."""
    raw = symbol.upper().strip()
    
    if raw in ALIAS_MAP:
        return ALIAS_MAP[raw]
        
    clean = raw.replace("/", "").replace(" ", "").replace("-", "").replace("=X", "").replace("=F", "")
    if clean in ALIAS_MAP:
        return ALIAS_MAP[clean]

    # Standard 6-letter Forex pair (e.g., EURUSD, GBPJPY)
    if len(clean) == 6 and clean.isalpha():
        return f"{clean}=X"

    # Default fallback
    return raw


def calculate_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Calculates Relative Strength Index (RSI)."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).copy()
    loss = (-delta.where(delta < 0, 0)).copy()

    avg_gain = gain.rolling(window=period, min_periods=period).mean()
    avg_loss = loss.rolling(window=period, min_periods=period).mean()

    for i in range(period, len(series)):
        avg_gain.iloc[i] = (avg_gain.iloc[i - 1] * (period - 1) + gain.iloc[i]) / period
        avg_loss.iloc[i] = (avg_loss.iloc[i - 1] * (period - 1) + loss.iloc[i]) / period

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def fetch_forex_data(symbol: str, period: str = "1mo", interval: str = "1h") -> Optional[pd.DataFrame]:
    """Fetches market history from Yahoo Finance for Forex, Gold, Commodities or Crypto."""
    ticker_symbol = normalize_symbol(symbol)
    try:
        ticker = yf.Ticker(ticker_symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            return None
        return df
    except Exception as e:
        logger.warning(f"Error fetching data for {ticker_symbol}: {e}")
        return None


def analyze_pair(symbol: str, timeframe: str = "1h") -> Optional[Dict[str, Any]]:
    """Analyzes any Forex, Gold, Commodity, or Crypto asset for specified timeframe."""
    ticker_symbol = normalize_symbol(symbol)
    
    # Custom display name
    display_name = SYMBOL_NAMES.get(ticker_symbol)
    if not display_name:
        display_name = ticker_symbol.replace("=X", "").replace("-USD", "/USD").replace("=F", "")

    tf_key = timeframe.lower()
    if tf_key not in TIMEFRAME_CONFIG:
        tf_key = "1h"
    tf_info = TIMEFRAME_CONFIG[tf_key]

    df = fetch_forex_data(ticker_symbol, period=tf_info["period"], interval=tf_info["interval"])
    if df is None or len(df) < 5:
        # Fallback to 1h if timeframe data is unavailable
        df = fetch_forex_data(ticker_symbol, period="1mo", interval="1h")
        tf_key = "1h"
        tf_info = TIMEFRAME_CONFIG["1h"]
        if df is None or len(df) < 5:
            return None

    # Handle 4h resampling if requested
    if timeframe.lower() == "4h" and len(df) >= 4:
        df = df.resample("4h").agg({
            "Open": "first",
            "High": "max",
            "Low": "min",
            "Close": "last",
            "Volume": "sum"
        }).dropna()

    close = df["Close"]
    current_price = close.iloc[-1]

    # Timeframe price change calculation
    if len(close) >= 2:
        prev_price = close.iloc[-2]
        change_tf_pct = ((current_price - prev_price) / prev_price) * 100
    else:
        change_tf_pct = 0.0

    # 24h change for reference
    lookback_24h = min(24, len(close) - 1)
    prev_24h = close.iloc[-(lookback_24h + 1)] if len(close) > lookback_24h else close.iloc[0]
    change_24h_pct = ((current_price - prev_24h) / prev_24h) * 100

    # Timestamp
    last_time = df.index[-1]
    time_str = last_time.strftime("%Y-%m-%d %H:%M UTC") if hasattr(last_time, "strftime") else str(last_time)

    # Technical Indicators
    rsi_series = calculate_rsi(close, 14 if len(close) >= 15 else max(2, len(close)-1))
    current_rsi = rsi_series.iloc[-1] if not rsi_series.empty and not pd.isna(rsi_series.iloc[-1]) else 50.0

    sma_20 = close.rolling(min(20, len(close))).mean().iloc[-1]
    sma_50 = close.rolling(min(50, len(close))).mean().iloc[-1]
    ema_9 = close.ewm(span=min(9, len(close)), adjust=False).mean().iloc[-1]
    ema_21 = close.ewm(span=min(21, len(close)), adjust=False).mean().iloc[-1]

    # Signal determination
    rsi_signal = "NEUTRAL ⚡"
    if current_rsi >= 70:
        rsi_signal = "OVERBOUGHT 🔴 (Sell Signal)"
    elif current_rsi <= 30:
        rsi_signal = "OVERSOLD 🟢 (Buy Signal)"
    elif current_rsi > 55:
        rsi_signal = "BULLISH 📈"
    elif current_rsi < 45:
        rsi_signal = "BEARISH 📉"

    trend_signal = "BULLISH 🟢" if ema_9 > ema_21 else "BEARISH 🔴"

    # Smart Money Concepts (SMC) Analysis
    smc_data = analyze_smc(df)

    return {
        "symbol": ticker_symbol,
        "name": display_name,
        "price": current_price,
        "timeframe": tf_key,
        "timeframe_label": tf_info["label"],
        "change_tf_pct": change_tf_pct,
        "change_24h_pct": change_24h_pct,
        "timestamp": time_str,
        "rsi": current_rsi,
        "rsi_signal": rsi_signal,
        "sma_20": sma_20,
        "sma_50": sma_50,
        "ema_9": ema_9,
        "ema_21": ema_21,
        "trend_signal": trend_signal,
        "smc": smc_data,
    }
