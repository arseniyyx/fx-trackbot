import json
import os
from pathlib import Path
from typing import Dict

SETTINGS_FILE = Path(__file__).parent / "user_settings.json"

# In-memory storage with JSON file backing:
user_languages: Dict[int, str] = {}
user_pairs: Dict[int, str] = {}
user_chart_styles: Dict[int, str] = {}
user_states: Dict[int, str] = {}

DEFAULT_LANG = "ru"
DEFAULT_PAIR = "EURUSD"
DEFAULT_CHART_STYLE = "tradingview_live"


def load_settings():
    """Loads user settings from user_settings.json file on startup."""
    global user_languages, user_pairs, user_chart_styles
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                user_languages = {int(k): v for k, v in data.get("languages", {}).items()}
                user_pairs = {int(k): v for k, v in data.get("pairs", {}).items()}
                user_chart_styles = {int(k): v for k, v in data.get("styles", {}).items()}
        except Exception as e:
            print(f"Error loading user_settings.json: {e}")


def save_settings():
    """Saves user settings to user_settings.json file."""
    try:
        data = {
            "languages": {str(k): v for k, v in user_languages.items()},
            "pairs": {str(k): v for k, v in user_pairs.items()},
            "styles": {str(k): v for k, v in user_chart_styles.items()},
        }
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving user_settings.json: {e}")


# Initialize settings from file on module import
load_settings()

SUPPORTED_LANGUAGES = {
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
    "uk": "🇺🇦 Українська"
}

SUPPORTED_CHART_STYLES = {
    "tradingview_live": "🔴 Live TradingView Real-Time",
    "tradingview": "📺 TradingView Dark (Fast)",
    "technical": "⚡ Cyber Technical",
    "smooth": "🎨 Smooth Gradient"
}

TEXTS = {
    "ru": {
        "welcome": (
            "🤖 **Добро пожаловать в Forex, Metals & Crypto Analytics Bot!**\n\n"
            "Я предоставляю **живые графики с TradingView**, онлайн-котировки, теханализ, **новости & процентные ставки ФРС**, а также **уведомления по цене** для любых активов: **Forex, Золото, Металлы, Нефть, Криптовалюта (BTC, ETH, SOL, TON)**.\n\n"
            "⏱ **Доступные таймфреймы:** `1m`, `15m`, `30m`, `1h`, `4h`, `24h`, `1W`\n\n"
            "👇 Используйте нижнее меню для быстрой навигации или выберите актив ниже:"
        ),
        "help": (
            "📊 **Инструкция и индикаторы теханализа**\n\n"
            "🔴 **Живые Графики TradingView:**\n"
            "Бот автоматически рендерит настоящие графики TradingView в реальном времени!\n\n"
            "📰 **Новости и Ставки ЦБ (ФРС / ЕЦБ / BoJ):**\n"
            "Нажмите `📰 Новости & ФРС` для получения свежих финансовых новостей по активу и актуальных процентных ставок центробанков!\n\n"
            "🌐 **Поддерживаемые активы:**\n"
            "• **Forex пары:** `EURUSD`, `GBPUSD`, `USDJPY` и др.\n"
            "• **Металлы & Нефть:** `GOLD` (XAU/USD), `SILVER` (XAG/USD), `OIL` (WTI)\n"
            "• **Криптовалюта:** `BTC`, `ETH`, `SOL`, `TON`, `XRP`, `DOGE`\n"
            "• **Поиск тикеров:** Отправьте любое название актива сообщением в чат!\n\n"
            "🔔 **Настройка Алерт:**\n"
            "Нажмите `🔔 Алерты` ➔ `➕ Добавить алерт` ➔ выберите актив или введите свой тикер ➔ введите цену.\n\n"
            "🔴 **RSI (14):**\n"
            "• `RSI >= 70`: Перекупленность (Продажа 🔴)\n"
            "• `RSI <= 30`: Перепроданность (Покупка 🟢)"
        ),
        "select_pair": "🌐 **Выберите актив из меню или отправьте название (GOLD, BTC, EURUSD):**",
        "select_alert_pair": "🔔 **Выберите актив для установки алерта по цене:**",
        "prompt_custom_symbol": "🔍 **Поиск любого актива на рынке**\n\nОтправьте название или тикер в чат:\n• **Металлы:** `GOLD`, `XAU`, `SILVER`, `OIL`\n• **Крипта:** `BTC`, `ETH`, `SOL`, `TON`, `XRP`\n• **Forex:** `EURUSD`, `GBPJPY`, `AUDCAD`\n• **Акции:** `NVDA`, `AAPL`, `TSLA`",
        "select_tf": "⏱ **Выберите таймфрейм для {pair}:**",
        "settings_title": "⚙️ **Настройки бота**\n\nВыберите категорию настроек:",
        "settings_lang_title": "🌐 **Выбор языка интерфейса:**",
        "settings_style_title": "🎨 **Выбор стиля оформления графиков:**",
        "lang_updated": "✅ Язык интерфейса успешно изменен на **Русский 🇷🇺**",
        "style_updated": "✅ Стиль оформления графиков успешно изменен на **{style}**",
        "pair_selected": "📌 Текущий отслеживаемый актив: **{pair}**",
        "btn_dashboard": "📊 Дашборд {pair}",
        "btn_pairs": "💱 Выбрать актив",
        "btn_timeframes": "⏱ Таймфреймы",
        "btn_all_currencies": "📈 Все рынки",
        "btn_news": "📰 Новости & ФРС",
        "btn_alerts": "🔔 Алерты",
        "btn_settings": "⚙️ Настройки",
        "btn_help": "❓ Справка",
        "btn_change_pair": "💱 Сменить актив",
        "btn_refresh": "🔄 Обновить",
        "btn_add_alert": "➕ Добавить алерт",
        "btn_clear_alerts": "🗑 Удалить все алерты",
        "btn_set_lang": "🌐 Мова / Language",
        "btn_set_style": "🎨 Стиль графика / Chart Style",
        "btn_inline_news": "📰 Новости & ФРС",
        "btn_inline_alert": "🔔 + Алерт",
        "btn_inline_search": "🔍 Ввести любой тикер",
        "btn_back_dashboard": "📊 Вернуться к дашборду",
        "btn_refresh_news": "🔄 Обновить новости",
        "alerts_title": "🔔 **Мои активные алерты по цене**\n\n",
        "no_alerts": "ℹ️ У вас пока нет активных алеров.\n\nНажмите `➕ Добавить алерт`, чтобы выбрать актив и установить цену!",
        "prompt_alert_price": "🎯 **Установка алерта по цене для {pair}**\n\nТекущая цена: `{price:.5f}`\n\nОтправьте желаемую цену числом (например: `{example:.5f}`):",
        "alert_added": "✅ **Алерт успешно создан!**\n\n💱 Актив: **{pair}**\n🎯 Целевая цена: `{target:.5f}` ({condition})\n\nБот пришлет вам уведомление, как только рынок достигнет этой цены!",
        "invalid_price": "❌ **Неверный формат цены.** Пожалуйста, введите число (например: `2450.50` или `65000`).",
        "report_title": "💱 **Дашборд {name}**",
        "curr_price": "💰 **Текущая цена:**",
        "change_tf": "⏱ **Изменение ({tf}):**",
        "change_24h": "📅 **Изменение (24h):**",
        "rsi_label": "⚡ **RSI (14):**",
        "trend_label": "📉 **Тренд (EMA 9/21):**",
        "ma_title": "📏 **Средние скользящие ({tf}):**",
        "last_candle": "🕒 **Время свечи (UTC):**",
        "click_below": "👇 *Нажмите кнопку ниже для смены таймфрейма или новостей:*",
        "all_pairs_title": "💱 **Сводка по популярным рынкам (1h):**",
        "loading": "⏳ Загрузка котировок TradingView...",
        "news_title": "📰 **Новости рынка & Процентные ставки для {pair}**",
        "fed_rates_title": "🏛 **Макроэкономика & Процентные Ставки:**",
        "sig_bullish": "БЫЧИЙ 🟢",
        "sig_bearish": "МЕДВЕЖИЙ 🔴",
        "sig_neutral": "НЕЙТРАЛЬНЫЙ ⚡",
        "sig_overbought": "ПЕРЕКУПЛЕННОСТЬ 🔴 (Продажа)",
        "sig_oversold": "ПЕРЕПРОДАННОСТЬ 🟢 (Покупка)",
        "lbl_next_meeting": "📅 **След. заседание:**",
        "lbl_market_odds": "📊 **Ожидания рынка (CME FedWatch):**",
        "lbl_latest_news": "📰 **Последние рыночные новости:**",
        "lbl_no_news": "ℹ️ Свежих новостей по данному активу временно не найдено.",
        "alert_triggered": "🚨 **СРАБОТАЛ АЛЕРТ ПО ЦЕНЕ!**"
    },
    "en": {
        "welcome": (
            "🤖 **Welcome to Forex, Metals & Crypto Analytics Bot!**\n\n"
            "I provide **Live TradingView Charts**, real-time prices, Technical Analysis, **News & Fed Rates**, and **price alerts** for any asset: **Forex, Gold, Metals, Oil, Cryptocurrencies (BTC, ETH, SOL, TON)**.\n\n"
            "⏱ **Supported Timeframes:** `1m`, `15m`, `30m`, `1h`, `4h`, `24h`, `1W`\n\n"
            "👇 Use bottom menu for quick navigation or choose an asset below:"
        ),
        "help": (
            "📊 **Interactive Timeframe & Technical Analysis Guide**\n\n"
            "🔴 **Live TradingView Charts:**\n"
            "Bot renders authentic live TradingView interactive candlestick charts!\n\n"
            "📰 **Market News & Central Bank Rates (Fed / ECB / BoJ):**\n"
            "Click `📰 News & Fed` to view real-time financial market headlines and central bank interest rates!\n\n"
            "🌐 **Supported Assets:**\n"
            "• **Forex Pairs:** `EURUSD`, `GBPUSD`, `USDJPY` etc.\n"
            "• **Metals & Oil:** `GOLD` (XAU/USD), `SILVER` (XAG/USD), `OIL` (WTI)\n"
            "• **Crypto:** `BTC`, `ETH`, `SOL`, `TON`, `XRP`, `DOGE`\n"
            "• **Ticker Search:** Send any ticker as a text message in chat!\n\n"
            "🔔 **Setting Price Alerts:**\n"
            "Click `🔔 Alerts` ➔ `➕ Add Alert` ➔ choose an asset or type ticker ➔ enter price level.\n\n"
            "🔴 **RSI (14):**\n"
            "• `RSI >= 70`: Overbought (Sell 🔴)\n"
            "• `RSI <= 30`: Oversold (Buy 🟢)"
        ),
        "select_pair": "🌐 **Select an asset from the menu or send ticker name (GOLD, BTC, EURUSD):**",
        "select_alert_pair": "🔔 **Select an asset to set a price alert:**",
        "prompt_custom_symbol": "🔍 **Market Asset Search**\n\nSend any ticker or symbol name in chat:\n• **Metals:** `GOLD`, `XAU`, `SILVER`, `OIL`\n• **Crypto:** `BTC`, `ETH`, `SOL`, `TON`, `XRP`\n• **Forex:** `EURUSD`, `GBPJPY`, `AUDCAD`\n• **Stocks:** `NVDA`, `AAPL`, `TSLA`",
        "select_tf": "⏱ **Select a timeframe for {pair}:**",
        "settings_title": "⚙️ **Bot Settings**\n\nSelect settings category:",
        "settings_lang_title": "🌐 **Language Settings:**",
        "settings_style_title": "🎨 **Chart Visual Style Settings:**",
        "lang_updated": "✅ Interface language updated to **English 🇬🇧**",
        "style_updated": "✅ Chart visual style updated to **{style}**",
        "pair_selected": "📌 Current tracked asset: **{pair}**",
        "btn_dashboard": "📊 Dashboard {pair}",
        "btn_pairs": "💱 Select Asset",
        "btn_timeframes": "⏱ Timeframes",
        "btn_all_currencies": "📈 All Markets",
        "btn_news": "📰 News & Fed",
        "btn_alerts": "🔔 Alerts",
        "btn_settings": "⚙️ Settings",
        "btn_help": "❓ Help",
        "btn_change_pair": "💱 Change Asset",
        "btn_refresh": "🔄 Refresh",
        "btn_add_alert": "➕ Add Alert",
        "btn_clear_alerts": "🗑 Delete All Alerts",
        "btn_set_lang": "🌐 Language",
        "btn_set_style": "🎨 Chart Visual Style",
        "btn_inline_news": "📰 News & Fed",
        "btn_inline_alert": "🔔 + Alert",
        "btn_inline_search": "🔍 Ticker Search",
        "btn_back_dashboard": "📊 Back to Dashboard",
        "btn_refresh_news": "🔄 Refresh News",
        "alerts_title": "🔔 **My Active Price Alerts**\n\n",
        "no_alerts": "ℹ️ You don't have any active price alerts yet.\n\nClick `➕ Add Alert` to pick an asset and set a target price!",
        "prompt_alert_price": "🎯 **Set Price Alert for {pair}**\n\nCurrent Price: `{price:.5f}`\n\nSend desired target price as a number (e.g.: `{example:.5f}`):",
        "alert_added": "✅ **Alert created successfully!**\n\n💱 Asset: **{pair}**\n🎯 Target Price: `{target:.5f}` ({condition})\n\nYou will receive a notification as soon as the market reaches this price!",
        "invalid_price": "❌ **Invalid price format.** Please enter a valid number (e.g.: `2450.50` or `65000`).",
        "report_title": "💱 **Dashboard {name}**",
        "curr_price": "💰 **Current Price:**",
        "change_tf": "⏱ **Change ({tf}):**",
        "change_24h": "📅 **Change (24h):**",
        "rsi_label": "⚡ **RSI (14):**",
        "trend_label": "📉 **Trend (EMA 9/21):**",
        "ma_title": "📏 **Moving Averages ({tf}):**",
        "last_candle": "🕒 **Candle Time (UTC):**",
        "click_below": "👇 *Click buttons below to change timeframe or news:*",
        "all_pairs_title": "💱 **Popular Markets Summary (1h):**",
        "loading": "⏳ Loading TradingView chart...",
        "news_title": "📰 **Market News & Interest Rates for {pair}**",
        "fed_rates_title": "🏛 **Macroeconomics & Central Bank Rates:**",
        "sig_bullish": "BULLISH 🟢",
        "sig_bearish": "BEARISH 🔴",
        "sig_neutral": "NEUTRAL ⚡",
        "sig_overbought": "OVERBOUGHT 🔴 (Sell Signal)",
        "sig_oversold": "OVERSOLD 🟢 (Buy Signal)",
        "lbl_next_meeting": "📅 **Next Meeting:**",
        "lbl_market_odds": "📊 **Market Odds (CME FedWatch):**",
        "lbl_latest_news": "📰 **Latest Market News:**",
        "lbl_no_news": "ℹ️ No recent news found for this asset.",
        "alert_triggered": "🚨 **PRICE ALERT TRIGGERED!**"
    },
    "uk": {
        "welcome": (
            "🤖 **Ласкаво просимо до Forex, Metals & Crypto Analytics Bot!**\n\n"
            "Я надаю **живі графіки з TradingView**, онлайн-котирування, теханаліз, **новини та ставки ФРС**, а також **цінові сповіщення** для будь-яких активів: **Forex, Золото, Метали, Нафта, Криптовалюта (BTC, ETH, SOL, TON)**.\n\n"
            "⏱ **Доступні таймфрейми:** `1m`, `15m`, `30m`, `1h`, `4h`, `24h`, `1W`\n\n"
            "👇 Використовуйте нижнє меню для швидкої навігації або оберіть актив нижче:"
        ),
        "help": (
            "📊 **Інструкція та індикатори теханалізу**\n\n"
            "🔴 **Живі Графіки TradingView:**\n"
            "Бот автоматично рендерить справжні графіки TradingView у реальному часі!\n\n"
            "📰 **Новини та Ставки ЦБ (ФРС / ЕЦБ / BoJ):**\n"
            "Натисніть `📰 Новини & ФРС` для отримання свіжих фінансових новин по активу та актуальних процентних ставок центральних банків!\n\n"
            "🌐 **Підтримувані активи:**\n"
            "• **Forex пари:** `EURUSD`, `GBPUSD`, `USDJPY` тощо.\n"
            "• **Метали & Нафта:** `GOLD` (XAU/USD), `SILVER` (XAG/USD), `OIL` (WTI)\n"
            "• **Криптовалюта:** `BTC`, `ETH`, `SOL`, `TON`, `XRP`, `DOGE`\n"
            "• **Пошук тікерів:** Надішліть будь-яку назву активу повідомленням в чат!\n\n"
            "🔔 **Налаштування Алертів:**\n"
            "Натисніть `🔔 Алерти` ➔ `➕ Додати алерт` ➔ оберіть актив або введіть свій тікер ➔ введіть ціну.\n\n"
            "🔴 **RSI (14):**\n"
            "• `RSI >= 70`: Перекупленість (Продаж 🔴)\n"
            "• `RSI <= 30`: Перепроданість (Купівля 🟢)"
        ),
        "select_pair": "🌐 **Оберіть актив з меню або надішліть назву (GOLD, BTC, EURUSD):**",
        "select_alert_pair": "🔔 **Оберіть актив для встановлення алерту по ціні:**",
        "prompt_custom_symbol": "🔍 **Пошук будь-якого активу на ринку**\n\nНадішліть назву або тікер у чат:\n• **Метали:** `GOLD`, `XAU`, `SILVER`, `OIL`\n• **Крипта:** `BTC`, `ETH`, `SOL`, `TON`, `XRP`\n• **Forex:** `EURUSD`, `GBPJPY`, `AUDCAD`\n• **Акції:** `NVDA`, `AAPL`, `TSLA`",
        "select_tf": "⏱ **Оберіть таймфрейм для {pair}:**",
        "settings_title": "⚙️ **Налаштування бота**\n\nОберіть категорію налаштувань:",
        "settings_lang_title": "🌐 **Вибір мови інтерфейсу:**",
        "settings_style_title": "🎨 **Вибір стилю оформлення графіків:**",
        "lang_updated": "✅ Мову інтерфейсу успішно змінено на **Українську 🇺🇦**",
        "style_updated": "✅ Стиль оформлення графіків успішно змінено на **{style}**",
        "pair_selected": "📌 Поточний актив: **{pair}**",
        "btn_dashboard": "📊 Дашборд {pair}",
        "btn_pairs": "💱 Обрати актив",
        "btn_timeframes": "⏱ Таймфрейми",
        "btn_all_currencies": "📈 Усі ринки",
        "btn_news": "📰 Новини & ФРС",
        "btn_alerts": "🔔 Сповіщення",
        "btn_settings": "⚙️ Налаштування",
        "btn_help": "❓ Довідка",
        "btn_change_pair": "💱 Змінити актив",
        "btn_refresh": "🔄 Оновити",
        "btn_add_alert": "➕ Додати сповіщення",
        "btn_clear_alerts": "🗑 Видалити всі сповіщення",
        "btn_set_lang": "🌐 Мова / Language",
        "btn_set_style": "🎨 Стиль графіка / Chart Style",
        "btn_inline_news": "📰 Новини & ФРС",
        "btn_inline_alert": "🔔 + Сповіщення",
        "btn_inline_search": "🔍 Ввести будь-який тікер",
        "btn_back_dashboard": "📊 Повернутися до дашборду",
        "btn_refresh_news": "🔄 Оновити новини",
        "alerts_title": "🔔 **Мої активні алерти по ціні**\n\n",
        "no_alerts": "ℹ️ У вас поки немає активних алертів.\n\nНатисніть `➕ Додати сповіщення`, щоб обрати актив та встановити ціновий рівень!",
        "prompt_alert_price": "🎯 **Встановлення алерту по ціні для {pair}**\n\nПоточна ціна: `{price:.5f}`\n\nНадішліть бажану ціну числом (наприклад: `{example:.5f}`):",
        "alert_added": "✅ **Алерт успішно створено!**\n\n💱 Актив: **{pair}**\n🎯 Цільова ціна: `{target:.5f}` ({condition})\n\nБот надішле вам сповіщення, як тільки ринок досягне цієї ціни!",
        "invalid_price": "❌ **Невірний формат ціни.** Будь ласка, введіть число (наприклад: `2450.50` або `65000`).",
        "report_title": "💱 **Дашборд {name}**",
        "curr_price": "💰 **Поточна ціна:**",
        "change_tf": "⏱ **Зміна ({tf}):**",
        "change_24h": "📅 **Зміна (24h):**",
        "rsi_label": "⚡ **RSI (14):**",
        "trend_label": "📉 **Тренд (EMA 9/21):**",
        "ma_title": "📏 **Ковзні середні ({tf}):**",
        "last_candle": "🕒 **Час свічки (UTC):**",
        "click_below": "👇 *Натисніть кнопку нижче для зміни таймфрейму або новин:*",
        "all_pairs_title": "💱 **Зведення по популярних ринках (1h):**",
        "loading": "⏳ Завантаження графіку TradingView...",
        "news_title": "📰 **Новини ринку & Процентні ставки для {pair}**",
        "fed_rates_title": "🏛 **Макроекономіка & Процентні Ставки:**",
        "sig_bullish": "БИЧИЙ 🟢",
        "sig_bearish": "ВЕДМЕЖИЙ 🔴",
        "sig_neutral": "НЕЙТРАЛЬНИЙ ⚡",
        "sig_overbought": "ПЕРЕКУПЛЕНІСТЬ 🔴 (Продаж)",
        "sig_oversold": "ПЕРЕПРОДАНІСТЬ 🟢 (Купівля)",
        "lbl_next_meeting": "📅 **Слід. засідання:**",
        "lbl_market_odds": "📊 **Очікування ринку (CME FedWatch):**",
        "lbl_latest_news": "📰 **Останні ринкові новини:**",
        "lbl_no_news": "ℹ️ Свіжих новин по даному активу тимчасово не знайдено.",
        "alert_triggered": "🚨 **СПРАЦЮВАВ ЦІНОВИЙ АЛЕРТ!**"
    }
}


def get_user_lang(user_id: int) -> str:
    """Returns user's language preference or default ('ru')."""
    return user_languages.get(user_id, DEFAULT_LANG)


def set_user_lang(user_id: int, lang: str):
    """Sets user's language preference and saves to disk."""
    if lang in SUPPORTED_LANGUAGES:
        user_languages[user_id] = lang
        save_settings()


def get_user_pair(user_id: int) -> str:
    """Returns user's selected Forex/Asset symbol or default ('EURUSD')."""
    return user_pairs.get(user_id, DEFAULT_PAIR)


def set_user_pair(user_id: int, symbol: str):
    """Sets user's selected Forex/Asset symbol and saves to disk."""
    user_pairs[user_id] = symbol.strip()
    save_settings()


def get_user_chart_style(user_id: int) -> str:
    """Returns user's selected chart style."""
    return user_chart_styles.get(user_id, DEFAULT_CHART_STYLE)


def set_user_chart_style(user_id: int, style: str):
    """Sets user's selected chart style and saves to disk."""
    if style in SUPPORTED_CHART_STYLES:
        user_chart_styles[user_id] = style
        save_settings()


def get_user_state(user_id: int) -> str:
    """Returns user's current state."""
    return user_states.get(user_id, "")


def set_user_state(user_id: int, state: str):
    """Sets user's state."""
    user_states[user_id] = state


def get_text(user_id: int, key: str, **kwargs) -> str:
    """Retrieves localized text for given key and formats kwargs."""
    lang = get_user_lang(user_id)
    template = TEXTS.get(lang, TEXTS[DEFAULT_LANG]).get(key, TEXTS[DEFAULT_LANG].get(key, ""))
    if kwargs:
        return template.format(**kwargs)
    return template
