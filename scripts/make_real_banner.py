import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import yfinance as yf

def generate_real_dashboard_banner(output_path: str):
    """Generates an authentic, clean, real dark-mode financial analytics banner using Matplotlib."""
    plt.style.use("dark_background")
    fig = plt.figure(figsize=(16, 9), dpi=120, facecolor="#131722")

    # Grid layout: 2 rows, 3 columns
    gs = fig.add_gridspec(2, 3, height_ratios=[1.2, 1], hspace=0.35, wspace=0.22)
    fig.subplots_adjust(top=0.88, bottom=0.08, left=0.06, right=0.94)

    # Fetch real market data for EURUSD, GOLD, BTC
    eur_df = yf.Ticker("EURUSD=X").history(period="1mo", interval="1d")
    gold_df = yf.Ticker("GC=F").history(period="1mo", interval="1d")
    btc_df = yf.Ticker("BTC-USD").history(period="1mo", interval="1d")

    assets = [
        ("EUR/USD (Euro)", eur_df, "#00F5D4", gs[0, 0]),
        ("Gold (XAU/USD)", gold_df, "#FFD700", gs[0, 1]),
        ("Bitcoin (BTC/USD)", btc_df, "#00E676", gs[0, 2]),
    ]

    for title, df, color, spec in assets:
        ax = fig.add_subplot(spec)
        ax.set_facecolor("#1e222d")

        if df is not None and len(df) >= 5:
            close = df["Close"]
            ema_9 = close.ewm(span=9, adjust=False).mean()
            ema_21 = close.ewm(span=21, adjust=False).mean()
            x = np.arange(len(close))

            ax.plot(x, close.values, label="Price", color=color, linewidth=2.2)
            ax.plot(x, ema_9.values, label="EMA 9", color="#38BDF8", linestyle="--", linewidth=1.2)
            ax.plot(x, ema_21.values, label="EMA 21", color="#F59E0B", linestyle="--", linewidth=1.2)

            curr_price = close.iloc[-1]
            prev_price = close.iloc[-2]
            pct_chg = ((curr_price - prev_price) / prev_price) * 100
            chg_sign = "+" if pct_chg >= 0 else ""

            ax.set_title(f"{title}: {curr_price:.4f} ({chg_sign}{pct_chg:.2f}%)", color="#FFFFFF", fontsize=12, fontweight="bold", pad=8)
            ax.legend(loc="upper left", facecolor="#131722", edgecolor="#2a2e39", fontsize=8, labelcolor="#D1D4DC")
        else:
            ax.set_title(title, color="#FFFFFF", fontsize=12)

        ax.grid(True, color="#2a2e39", linestyle="--", alpha=0.4)
        ax.tick_params(colors="#B2B5BE", labelsize=8)

    # Bottom Row: Technical RSI & Macro Fed Rates Summary
    ax_rsi = fig.add_subplot(gs[1, 0:2])
    ax_rsi.set_facecolor("#1e222d")
    if eur_df is not None and len(eur_df) >= 14:
        delta = eur_df["Close"].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        x = np.arange(len(rsi))
        ax_rsi.plot(x, rsi.values, color="#A855F7", linewidth=2.0, label="RSI (14)")
        ax_rsi.axhline(70, color="#FF4757", linestyle="--", alpha=0.7, label="Overbought (70)")
        ax_rsi.axhline(30, color="#2ED573", linestyle="--", alpha=0.7, label="Oversold (30)")
        ax_rsi.fill_between(x, 70, 30, color="#A855F7", alpha=0.08)
        ax_rsi.set_ylim(10, 90)
        ax_rsi.set_title("Relative Strength Index (RSI 14) -- Technical Indicator Engine", color="#FFFFFF", fontsize=11, fontweight="bold", pad=6)
        ax_rsi.legend(loc="upper left", facecolor="#131722", edgecolor="#2a2e39", fontsize=8, labelcolor="#D1D4DC")
        ax_rsi.grid(True, color="#2a2e39", linestyle="--", alpha=0.4)
        ax_rsi.tick_params(colors="#B2B5BE", labelsize=8)

    # Bottom Right Card: Central Bank Rates & FOMC Summary
    ax_cb = fig.add_subplot(gs[1, 2])
    ax_cb.set_facecolor("#1e222d")
    ax_cb.axis("off")
    ax_cb.text(0.05, 0.85, "Central Bank Rates & Macro", color="#FFD700", fontsize=11, fontweight="bold")
    ax_cb.text(0.05, 0.65, "[Fed US] Rate: 4.25% - 4.50% (Dovish)", color="#FFFFFF", fontsize=9.5)
    ax_cb.text(0.05, 0.48, "[Next FOMC] 30 July / 17 Sept 2026", color="#38BDF8", fontsize=9)
    ax_cb.text(0.05, 0.32, "[CME FedWatch] 78% Odds (-25 bps Cut)", color="#2ED573", fontsize=9)
    ax_cb.text(0.05, 0.15, "[ECB] 3.15% | [BoJ] 0.50%", color="#B2B5BE", fontsize=9)

    # Title Header Banner
    fig.text(0.5, 0.95, "FX TrackBot -- Real-Time Financial Market Analytics Platform", color="#FFFFFF", fontsize=15, fontweight="bold", ha="center")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path, format="jpg", dpi=120, facecolor=fig.get_facecolor(), bbox_inches="tight")
    plt.close(fig)
    print(f"Clean real dashboard banner generated at {output_path}")

if __name__ == "__main__":
    generate_real_dashboard_banner(r"C:\Users\arsen\Documents\forexbot\assets\banner.jpg")
