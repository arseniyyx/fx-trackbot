import pandas as pd
from typing import Dict, Any, Optional, List


def analyze_smc(df: pd.DataFrame) -> Dict[str, Any]:
    """Analyzes Smart Money Concepts (SMC/ICT): Order Blocks, Fair Value Gaps (FVG), Equilibrium & Market Structure Shift."""
    if df is None or len(df) < 15:
        return {
            "smc_signal": "NEUTRAL ⚡",
            "zone": "EQUILIBRIUM ⚖️",
            "ob_status": "No clear OB detected",
            "fvg_status": "No FVG detected",
            "liquidity_status": "Ranging liquidity"
        }

    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    open_p = df["Open"]
    curr_price = close.iloc[-1]

    # 1. Swing High & Swing Low (Lookback 20 bars)
    lookback = min(30, len(df))
    recent_high = high.tail(lookback).max()
    recent_low = low.tail(lookback).min()
    eq_level = (recent_high + recent_low) / 2.0

    # Premium vs Discount Pricing
    if curr_price > eq_level:
        zone_str = f"PREMIUM 🔴 (Sell Zone, Eq: `{eq_level:.5f}`)"
    else:
        zone_str = f"DISCOUNT 🟢 (Buy Zone, Eq: `{eq_level:.5f}`)"

    # 2. Fair Value Gap (FVG) Detection (Lookback last 5 candles)
    fvg_status = "No Active FVG"
    for i in range(len(df) - 1, len(df) - 6, -1):
        if i >= 2:
            # Bullish FVG: Low of candle i > High of candle i-2
            if low.iloc[i] > high.iloc[i - 2]:
                gap_size = low.iloc[i] - high.iloc[i - 2]
                fvg_status = f"Bullish FVG 🟢 [`{high.iloc[i-2]:.5f}` - `{low.iloc[i]:.5f}`]"
                break
            # Bearish FVG: High of candle i < Low of candle i-2
            elif high.iloc[i] < low.iloc[i - 2]:
                gap_size = low.iloc[i - 2] - high.iloc[i]
                fvg_status = f"Bearish FVG 🔴 [`{high.iloc[i]:.5f}` - `{low.iloc[i-2]:.5f}`]"
                break

    # 3. Order Block (OB) Detection
    # Bullish OB: last bearish candle before bullish BOS
    # Bearish OB: last bullish candle before bearish BOS
    ob_status = "Neutral Order Block"
    smc_signal = "NEUTRAL ⚡"

    # Check for recent displacement
    last_3_return = ((close.iloc[-1] - close.iloc[-4]) / close.iloc[-4]) * 100 if len(close) >= 4 else 0

    if last_3_return > 0.4:
        # Bullish displacement
        for i in range(len(df) - 2, len(df) - 8, -1):
            if close.iloc[i] < open_p.iloc[i]:  # Bearish candle
                ob_price = close.iloc[i]
                ob_status = f"Bullish OB 🟢 [`{low.iloc[i]:.5f}` - `{high.iloc[i]:.5f}`]"
                smc_signal = "INSTITUTIONAL ACCUMULATION 🟢 (Smart Money Buy)"
                break
    elif last_3_return < -0.4:
        # Bearish displacement
        for i in range(len(df) - 2, len(df) - 8, -1):
            if close.iloc[i] > open_p.iloc[i]:  # Bullish candle
                ob_price = close.iloc[i]
                ob_status = f"Bearish OB 🔴 [`{low.iloc[i]:.5f}` - `{high.iloc[i]:.5f}`]"
                smc_signal = "INSTITUTIONAL DISTRIBUTION 🔴 (Smart Money Sell)"
                break
    else:
        if curr_price < eq_level:
            smc_signal = "DISCOUNT BUY AREA 🟢"
        else:
            smc_signal = "PREMIUM SELL AREA 🔴"

    # 4. Liquidity Sweep (BSL / SSL)
    last_high = high.iloc[-1]
    last_low = low.iloc[-1]
    prev_high = high.iloc[-20:-2].max() if len(high) >= 22 else high.iloc[0]
    prev_low = low.iloc[-20:-2].min() if len(low) >= 22 else low.iloc[0]

    liquidity_status = "No Liquidity Sweep"
    if last_high > prev_high and close.iloc[-1] < prev_high:
        liquidity_status = "BSL Sweep ⚡ (Buy-Side Liquidity Swept - Reversal Signal)"
    elif last_low < prev_low and close.iloc[-1] > prev_low:
        liquidity_status = "SSL Sweep ⚡ (Sell-Side Liquidity Swept - Reversal Signal)"

    return {
        "smc_signal": smc_signal,
        "zone": zone_str,
        "ob_status": ob_status,
        "fvg_status": fvg_status,
        "liquidity_status": liquidity_status,
        "eq_level": eq_level,
        "swing_high": recent_high,
        "swing_low": recent_low
    }
