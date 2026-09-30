import io
import asyncio
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for server rendering
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.interpolate import make_interp_spline
from typing import Optional

TV_SYMBOL_MAP = {
    # Forex
    "EURUSD=X": "FX:EURUSD",
    "GBPUSD=X": "FX:GBPUSD",
    "USDJPY=X": "FX:USDJPY",
    "AUDUSD=X": "FX:AUDUSD",
    "USDCAD=X": "FX:USDCAD",
    "USDCHF=X": "FX:USDCHF",
    "NZDUSD=X": "FX:NZDUSD",
    "EURGBP=X": "FX:EURGBP",
    "EURJPY=X": "FX:EURJPY",
    "GBPJPY=X": "FX:GBPJPY",

    # Gold & Commodities
    "GC=F": "OANDA:XAUUSD",
    "XAUUSD=X": "OANDA:XAUUSD",
    "SI=F": "OANDA:XAGUSD",
    "XAGUSD=X": "OANDA:XAGUSD",
    "CL=F": "TVC:USOIL",

    # Crypto
    "BTC-USD": "BINANCE:BTCUSDT",
    "ETH-USD": "BINANCE:ETHUSDT",
    "SOL-USD": "BINANCE:SOLUSDT",
    "TON11419-USD": "OKX:TONUSDT",
    "TON-USD": "OKX:TONUSDT",
    "XRP-USD": "BINANCE:XRPUSDT",
    "DOGE-USD": "BINANCE:DOGEUSDT",
}

TV_INTERVAL_MAP = {
    "1m": "1",
    "15m": "15",
    "30m": "30",
    "1h": "60",
    "4h": "240",
    "24h": "D",
    "1d": "D",
    "1w": "W"
}


def get_tradingview_symbol(symbol: str) -> str:
    """Helper to convert internal symbol to TradingView widget symbol."""
    sym = symbol.upper().strip()
    if sym in TV_SYMBOL_MAP:
        return TV_SYMBOL_MAP[sym]

    clean = sym.replace("=X", "").replace("-USD", "USD").replace("=F", "")
    if len(clean) == 6 and clean.isalpha():
        return f"FX:{clean}"
    return f"BINANCE:{clean}USDT" if "USD" not in clean else f"CAPITALCOM:{clean}"


def get_tradingview_interval(timeframe: str) -> str:
    """Helper to convert timeframe code to TradingView interval."""
    return TV_INTERVAL_MAP.get(timeframe.lower(), "60")


async def fetch_tradingview_live_snapshot(symbol: str, timeframe: str = "1h", df: Optional[pd.DataFrame] = None) -> Optional[bytes]:
    """Renders a clean real-time live TradingView chart snapshot via Playwright Chromium headless browser."""
    tv_symbol = get_tradingview_symbol(symbol)
    tv_interval = get_tradingview_interval(timeframe)
    url = (
        f"https://s.tradingview.com/widgetembed/?"
        f"frameElementId=tradingview_widget&symbol={tv_symbol}&interval={tv_interval}"
        f"&hidesidetoolbar=1&symboledit=0&saveimage=0&toolbarbg=131722&theme=dark&style=1"
        f"&timezone=Etc%2FUTC"
    )

    try:
        from playwright.async_api import async_playwright
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage"]
            )
            page = await browser.new_page(viewport={"width": 1000, "height": 600})
            
            # Use domcontentloaded for fast reliable load instead of waiting for networkidle websocket
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(2000)  # Wait 2 sec for TradingView candles to render
            
            screenshot_bytes = await page.screenshot(type="png")
            await browser.close()
            return screenshot_bytes

    except Exception as e:
        print(f"Error fetching live TradingView chart for {symbol}: {e}")
        return None


def generate_trend_chart(
    df: pd.DataFrame,
    display_name: str,
    timeframe_label: str,
    style: str = "tradingview"
) -> Optional[bytes]:
    """Generates a dynamic Dark-Mode Price Chart with selectable visual style (clean without SMC overlays)."""
    if df is None or len(df) < 5:
        return None

    try:
        close = df["Close"]
        ema_9 = close.ewm(span=min(9, len(close)), adjust=False).mean()
        ema_21 = close.ewm(span=min(21, len(close)), adjust=False).mean()
        sma_50 = close.rolling(min(50, len(close))).mean()

        # Calculate RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).copy()
        loss = (-delta.where(delta < 0, 0)).copy()
        period = 14 if len(close) >= 15 else max(2, len(close) - 1)
        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()

        for i in range(period, len(close)):
            avg_gain.iloc[i] = (avg_gain.iloc[i - 1] * (period - 1) + gain.iloc[i]) / period
            avg_loss.iloc[i] = (avg_loss.iloc[i - 1] * (period - 1) + loss.iloc[i]) / period

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        # Fill NaNs for plot safety
        close_vals = close.bfill().ffill().values
        ema9_vals = ema_9.bfill().ffill().values
        ema21_vals = ema_21.bfill().ffill().values
        sma50_vals = sma_50.bfill().ffill().values
        rsi_vals = rsi.fillna(50.0).bfill().ffill().values

        plt.style.use("dark_background")
        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=(10, 6), gridspec_kw={"height_ratios": [3, 1]}, sharex=True
        )

        x_raw = np.arange(len(close))
        curr_p = close.iloc[-1]
        prev_p = close.iloc[-2] if len(close) >= 2 else curr_p
        is_bullish = curr_p >= prev_p

        latest_ema9 = ema9_vals[-1]
        latest_ema21 = ema21_vals[-1]
        trend_str = "BULLISH" if latest_ema9 > latest_ema21 else "BEARISH"

        # STYLE 1: TradingView Dark (Classic Matplotlib)
        if style == "tradingview":
            fig.patch.set_facecolor("#131722")
            ax1.set_facecolor("#1e222d")
            ax2.set_facecolor("#1e222d")

            price_color = "#00F5D4" if is_bullish else "#FF4757"
            ax1.plot(x_raw, close_vals, label=f"Price ({curr_p:.5f})", color=price_color, linewidth=2.2)
            ax1.plot(x_raw, ema9_vals, label="EMA 9", color="#00E676", linestyle="--", linewidth=1.3)
            ax1.plot(x_raw, ema21_vals, label="EMA 21", color="#FF9100", linestyle="--", linewidth=1.3)
            ax1.plot(x_raw, sma50_vals, label="SMA 50", color="#D500F9", linestyle=":", linewidth=1.2)

            ax1.set_title(f"TradingView: {display_name} - {timeframe_label} | Trend: {trend_str}", color="#FFFFFF", fontsize=12, fontweight="bold", pad=10)
            ax1.set_ylabel("Price", color="#B2B5BE", fontsize=10)
            ax1.legend(loc="upper left", facecolor="#1e222d", edgecolor="#2a2e39", labelcolor="#D1D4DC", fontsize=8)
            ax1.grid(True, color="#2a2e39", linestyle="--", alpha=0.4)

            ax2.plot(x_raw, rsi_vals, label="RSI (14)", color="#7000FF", linewidth=1.5)
            ax2.axhline(70, color="#FF4757", linestyle="--", alpha=0.7)
            ax2.axhline(30, color="#2ED573", linestyle="--", alpha=0.7)
            ax2.fill_between(x_raw, 70, 30, color="#7000FF", alpha=0.08)
            ax2.set_ylabel("RSI", color="#B2B5BE", fontsize=10)
            ax2.set_ylim(10, 90)
            ax2.legend(loc="upper left", facecolor="#1e222d", edgecolor="#2a2e39", labelcolor="#D1D4DC", fontsize=8)
            ax2.grid(True, color="#2a2e39", linestyle="--", alpha=0.4)

        # STYLE 2: Technical (High-Contrast Cyberpunk)
        elif style == "technical":
            fig.patch.set_facecolor("#05070F")
            ax1.set_facecolor("#0B0F19")
            ax2.set_facecolor("#0B0F19")

            price_color = "#00FF66" if is_bullish else "#FF0055"
            ax1.plot(x_raw, close_vals, label=f"Price ({curr_p:.5f})", color=price_color, linewidth=2.5)
            ax1.plot(x_raw, ema9_vals, label="EMA 9", color="#00E5FF", linewidth=1.4)
            ax1.plot(x_raw, ema21_vals, label="EMA 21", color="#FFD600", linewidth=1.4)

            ax1.set_title(f"Cyber Technical: {display_name} - {timeframe_label} | Trend: {trend_str}", color="#00E5FF", fontsize=12, fontweight="bold", pad=10)
            ax1.set_ylabel("Price Level", color="#64748B", fontsize=10)
            ax1.legend(loc="upper left", facecolor="#0B0F19", edgecolor="#1E293B", labelcolor="#94A3B8", fontsize=8)
            ax1.grid(True, color="#1E293B", linestyle="-", alpha=0.6)

            ax2.plot(x_raw, rsi_vals, label="RSI (14)", color="#00E5FF", linewidth=1.8)
            ax2.axhline(70, color="#FF0055", linestyle="-", alpha=0.8)
            ax2.axhline(30, color="#00FF66", linestyle="-", alpha=0.8)
            ax2.fill_between(x_raw, 70, 30, color="#00E5FF", alpha=0.05)
            ax2.set_ylabel("RSI", color="#64748B", fontsize=10)
            ax2.set_ylim(10, 90)
            ax2.legend(loc="upper left", facecolor="#0B0F19", edgecolor="#1E293B", labelcolor="#94A3B8", fontsize=8)
            ax2.grid(True, color="#1E293B", linestyle="-", alpha=0.6)

        # STYLE 3: Smooth (Smooth Gradient Modern)
        else:
            fig.patch.set_facecolor("#0F172A")
            ax1.set_facecolor("#1E293B")
            ax2.set_facecolor("#1E293B")

            if len(x_raw) >= 4:
                x_smooth = np.linspace(x_raw.min(), x_raw.max(), 300)
                close_smooth = make_interp_spline(x_raw, close_vals, k=3)(x_smooth)
                ema9_smooth = make_interp_spline(x_raw, ema9_vals, k=3)(x_smooth)
                ema21_smooth = make_interp_spline(x_raw, ema21_vals, k=3)(x_smooth)
                rsi_smooth = make_interp_spline(x_raw, rsi_vals, k=3)(x_smooth)
            else:
                x_smooth = x_raw
                close_smooth = close_vals
                ema9_smooth = ema9_vals
                ema21_smooth = ema21_vals
                rsi_smooth = rsi_vals

            main_color = "#10B981" if is_bullish else "#F43F5E"

            ax1.plot(x_smooth, close_smooth, label=f"Smooth ({curr_p:.5f})", color=main_color, linewidth=2.5)
            min_y = close_vals.min()
            ax1.fill_between(x_smooth, close_smooth, min_y, color=main_color, alpha=0.15)

            ax1.plot(x_smooth, ema9_smooth, label="EMA 9", color="#38BDF8", linestyle="--", linewidth=1.3, alpha=0.85)
            ax1.plot(x_smooth, ema21_smooth, label="EMA 21", color="#F59E0B", linestyle="--", linewidth=1.3, alpha=0.85)

            ax1.set_title(f"Smooth Gradient: {display_name} - {timeframe_label} | Trend: {trend_str}", color="#F8FAFC", fontsize=12, fontweight="bold", pad=10)
            ax1.set_ylabel("Price", color="#94A3B8", fontsize=10)
            ax1.legend(loc="upper left", facecolor="#1E293B", edgecolor="#334155", labelcolor="#CBD5E1", fontsize=8)
            ax1.grid(True, color="#334155", linestyle=":", alpha=0.5)

            ax2.plot(x_smooth, rsi_smooth, label="RSI (14)", color="#A855F7", linewidth=1.8)
            ax2.axhline(70, color="#F43F5E", linestyle=":", alpha=0.8)
            ax2.axhline(30, color="#10B981", linestyle=":", alpha=0.8)
            ax2.fill_between(x_smooth, 70, 30, color="#A855F7", alpha=0.08)
            ax2.set_ylabel("RSI", color="#94A3B8", fontsize=10)
            ax2.set_ylim(10, 90)
            ax2.legend(loc="upper left", facecolor="#1E293B", edgecolor="#334155", labelcolor="#CBD5E1", fontsize=8)
            ax2.grid(True, color="#334155", linestyle=":", alpha=0.5)

        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format="png", dpi=120, bbox_inches="tight", facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)
        return buf.getvalue()

    except Exception as e:
        print(f"Error generating chart for {display_name}: {e}")
        return None
