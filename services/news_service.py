import yfinance as yf
import datetime
from typing import Dict, Any, List, Optional
from services.forex_service import normalize_symbol

CENTRAL_BANK_RATES = {
    "ru": {
        "FED": {
            "name": "ФРС США (Fed)",
            "rate": "4.25% - 4.50%",
            "next_meeting": "30 Июля 2026 / 17 Сентября 2026",
            "expectations": "78% Снижение (-25 б.п.) | 22% Сохранение",
            "bias": "Нейтральный / Смягчение 🕊️",
            "flag": "🇺🇸"
        },
        "ECB": {
            "name": "ЕЦБ Еврозоны (ECB)",
            "rate": "3.15%",
            "next_meeting": "10 Сентября 2026",
            "expectations": "65% Снижение (-25 б.п.)",
            "bias": "Смягчение 🕊️",
            "flag": "🇪🇺"
        },
        "BOE": {
            "name": "Банк Англии (BoE)",
            "rate": "4.75%",
            "next_meeting": "24 Сентября 2026",
            "expectations": "80% Сохранение",
            "bias": "Умеренный ⚖️",
            "flag": "🇬🇧"
        },
        "BOJ": {
            "name": "Банк Японии (BoJ)",
            "rate": "0.50%",
            "next_meeting": "18 Сентября 2026",
            "expectations": "55% Повышение (+15 б.п.)",
            "bias": "Повышение / Ужесточение 🦅",
            "flag": "🇯🇵"
        },
        "SNB": {
            "name": "Швейцарский НБ (SNB)",
            "rate": "0.50%",
            "next_meeting": "24 Сентября 2026",
            "expectations": "70% Сохранение",
            "bias": "Смягчение 🕊️",
            "flag": "🇨🇭"
        },
        "RBA": {
            "name": "РБА Австралии (RBA)",
            "rate": "4.35%",
            "next_meeting": "29 Сентября 2026",
            "expectations": "85% Сохранение",
            "bias": "Удерживание ⚖️",
            "flag": "🇦🇺"
        },
    },
    "en": {
        "FED": {
            "name": "US Federal Reserve (Fed)",
            "rate": "4.25% - 4.50%",
            "next_meeting": "30 July 2026 / 17 Sept 2026",
            "expectations": "78% Rate Cut (-25 bps) | 22% Hold",
            "bias": "Neutral / Dovish 🕊️",
            "flag": "🇺🇸"
        },
        "ECB": {
            "name": "European Central Bank (ECB)",
            "rate": "3.15%",
            "next_meeting": "10 Sept 2026",
            "expectations": "65% Rate Cut (-25 bps)",
            "bias": "Dovish 🕊️",
            "flag": "🇪🇺"
        },
        "BOE": {
            "name": "Bank of England (BoE)",
            "rate": "4.75%",
            "next_meeting": "24 Sept 2026",
            "expectations": "80% Hold Rate",
            "bias": "Moderate ⚖️",
            "flag": "🇬🇧"
        },
        "BOJ": {
            "name": "Bank of Japan (BoJ)",
            "rate": "0.50%",
            "next_meeting": "18 Sept 2026",
            "expectations": "55% Rate Hike (+15 bps)",
            "bias": "Hawkish 🦅",
            "flag": "🇯🇵"
        },
        "SNB": {
            "name": "Swiss National Bank (SNB)",
            "rate": "0.50%",
            "next_meeting": "24 Sept 2026",
            "expectations": "70% Hold Rate",
            "bias": "Dovish 🕊️",
            "flag": "🇨🇭"
        },
        "RBA": {
            "name": "Reserve Bank of Australia (RBA)",
            "rate": "4.35%",
            "next_meeting": "29 Sept 2026",
            "expectations": "85% Hold Rate",
            "bias": "Neutral ⚖️",
            "flag": "🇦🇺"
        },
    },
    "uk": {
        "FED": {
            "name": "ФРС США (Fed)",
            "rate": "4.25% - 4.50%",
            "next_meeting": "30 Липня 2026 / 17 Вересня 2026",
            "expectations": "78% Зниження (-25 б.п.) | 22% Утримання",
            "bias": "Нейтральний / Пом'якшення 🕊️",
            "flag": "🇺🇸"
        },
        "ECB": {
            "name": "ЕЦБ Єврозони (ECB)",
            "rate": "3.15%",
            "next_meeting": "10 Вересня 2026",
            "expectations": "65% Зниження (-25 б.п.)",
            "bias": "Пом'якшення 🕊️",
            "flag": "🇪🇺"
        },
        "BOE": {
            "name": "Банк Англії (BoE)",
            "rate": "4.75%",
            "next_meeting": "24 Вересня 2026",
            "expectations": "80% Утримання",
            "bias": "Помірний ⚖️",
            "flag": "🇬🇧"
        },
        "BOJ": {
            "name": "Банк Японії (BoJ)",
            "rate": "0.50%",
            "next_meeting": "18 Вересня 2026",
            "expectations": "55% Підвищення (+15 б.п.)",
            "bias": "Підвищення / Жорсткість 🦅",
            "flag": "🇯🇵"
        },
        "SNB": {
            "name": "Швейцарський НБ (SNB)",
            "rate": "0.50%",
            "next_meeting": "24 Вересня 2026",
            "expectations": "70% Утримання",
            "bias": "Пом'якшення 🕊️",
            "flag": "🇨🇭"
        },
        "RBA": {
            "name": "РБА Австралії (RBA)",
            "rate": "4.35%",
            "next_meeting": "29 Вересня 2026",
            "expectations": "85% Утримання",
            "bias": "Утримування ⚖️",
            "flag": "🇦🇺"
        },
    }
}

ASSET_CB_MAP = {
    "EURUSD=X": ("FED", "ECB"),
    "GBPUSD=X": ("FED", "BOE"),
    "USDJPY=X": ("FED", "BOJ"),
    "USDCHF=X": ("FED", "SNB"),
    "AUDUSD=X": ("FED", "RBA"),
    "GC=F": ("FED", None),
    "SI=F": ("FED", None),
    "CL=F": ("FED", None),
    "BTC-USD": ("FED", None),
    "ETH-USD": ("FED", None),
}


def fetch_asset_news(symbol: str, max_items: int = 4) -> List[Dict[str, str]]:
    """Fetches real-time financial headlines for given symbol from yfinance."""
    norm = normalize_symbol(symbol)
    articles = []

    try:
        ticker = yf.Ticker(norm)
        raw_news = ticker.news

        if not raw_news:
            fallback_sym = "GC=F" if "GC" in norm or "XAU" in norm else "EURUSD=X"
            ticker = yf.Ticker(fallback_sym)
            raw_news = ticker.news

        if raw_news:
            for item in raw_news:
                # Handle nested 'content' structure in yfinance output
                content = item.get("content", {}) if isinstance(item, dict) and "content" in item else item

                title = content.get("title") or content.get("summary") or item.get("title") or "Market Update"
                provider = content.get("provider", {})
                publisher = provider.get("displayName") if isinstance(provider, dict) else "Financial News"
                
                url_data = content.get("clickThroughUrl") or content.get("canonicalUrl") or {}
                url = url_data.get("url") if isinstance(url_data, dict) else ""
                
                pub_date = content.get("pubDate") or content.get("displayTime")

                date_str = ""
                if pub_date:
                    try:
                        if isinstance(pub_date, (int, float)):
                            dt = datetime.datetime.fromtimestamp(pub_date, tz=datetime.timezone.utc)
                            date_str = dt.strftime("%d %b %H:%M UTC")
                        else:
                            dt = datetime.datetime.fromisoformat(str(pub_date).replace("Z", "+00:00"))
                            date_str = dt.strftime("%d %b %H:%M UTC")
                    except Exception:
                        date_str = ""

                # Avoid duplicate titles
                if title and title not in [a["title"] for a in articles]:
                    articles.append({
                        "title": title.strip(),
                        "publisher": publisher,
                        "link": url if url else "https://finance.yahoo.com",
                        "date": date_str
                    })

                if len(articles) >= max_items:
                    break

    except Exception as e:
        print(f"Error fetching news for {symbol}: {e}")

    return articles


def get_macro_rates_summary(symbol: str, lang: str = "ru") -> Dict[str, Any]:
    """Generates localized macro interest rate & FOMC meeting expectations summary."""
    norm = normalize_symbol(symbol)
    cb_keys = ASSET_CB_MAP.get(norm, ("FED", None))

    rates_db = CENTRAL_BANK_RATES.get(lang, CENTRAL_BANK_RATES["ru"])

    primary_cb = rates_db.get(cb_keys[0], rates_db["FED"])
    secondary_cb = rates_db.get(cb_keys[1]) if cb_keys[1] else None

    return {
        "fed": rates_db["FED"],
        "primary_cb": primary_cb,
        "secondary_cb": secondary_cb
    }
