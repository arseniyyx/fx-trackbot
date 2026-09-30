from typing import Optional
from aiogram import Router, F
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    BufferedInputFile,
    InputMediaPhoto
)
from aiogram.filters import Command, CommandObject
from config import DEFAULT_PAIRS, SYMBOL_NAMES
from services.forex_service import analyze_pair, normalize_symbol, fetch_forex_data, TIMEFRAME_CONFIG
from services.chart_service import generate_trend_chart, fetch_tradingview_live_snapshot
from services.news_service import fetch_asset_news, get_macro_rates_summary
from locales import (
    get_text,
    set_user_lang,
    get_user_lang,
    get_user_pair,
    set_user_pair,
    get_user_chart_style,
    set_user_chart_style,
    get_user_state,
    set_user_state,
    SUPPORTED_LANGUAGES,
    SUPPORTED_CHART_STYLES
)
from alerts import (
    add_alert,
    get_user_alerts,
    delete_alert,
    clear_user_alerts
)

router = Router()

AVAILABLE_TIMEFRAMES = [
    ("1m", "1m"),
    ("15m", "15m"),
    ("30m", "30m"),
    ("1h", "1h"),
    ("4h", "4h"),
    ("24h", "24h"),
    ("1w", "1W"),
]


async def safe_edit_content(query: CallbackQuery, text: str, reply_markup: InlineKeyboardMarkup = None):
    """Safely edits text or photo caption of callback query message."""
    try:
        await query.message.edit_text(text, reply_markup=reply_markup, parse_mode="Markdown", disable_web_page_preview=True)
    except Exception:
        try:
            await query.message.edit_caption(caption=text, reply_markup=reply_markup, parse_mode="Markdown")
        except Exception:
            await query.message.answer(text, reply_markup=reply_markup, parse_mode="Markdown", disable_web_page_preview=True)


def get_display_pair_name(raw_symbol: str) -> str:
    """Helper to convert symbol or ticker to friendly display name."""
    norm = normalize_symbol(raw_symbol)
    if norm in SYMBOL_NAMES:
        return SYMBOL_NAMES[norm]
    return norm.replace("=X", "").replace("-USD", "/USD").replace("=F", "")


def get_main_reply_keyboard(user_id: int) -> ReplyKeyboardMarkup:
    """Generates localized persistent bottom menu buttons with user's selected asset."""
    current_pair = get_user_pair(user_id)
    display_name = get_display_pair_name(current_pair)
    dash_label = get_text(user_id, "btn_dashboard", pair=display_name)

    kb = [
        [
            KeyboardButton(text=dash_label),
            KeyboardButton(text=get_text(user_id, "btn_pairs"))
        ],
        [
            KeyboardButton(text=get_text(user_id, "btn_timeframes")),
            KeyboardButton(text=get_text(user_id, "btn_all_currencies")),
            KeyboardButton(text=get_text(user_id, "btn_news"))
        ],
        [
            KeyboardButton(text=get_text(user_id, "btn_alerts")),
            KeyboardButton(text=get_text(user_id, "btn_settings")),
            KeyboardButton(text=get_text(user_id, "btn_help"))
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


def get_timeframe_keyboard(user_id: int, symbol: str, active_tf: str = "1h") -> InlineKeyboardMarkup:
    """Generates localized inline buttons for selecting timeframes, alerts, and news."""
    clean_sym = symbol.replace("=X", "")
    row1 = []
    row2 = []

    for tf_code, tf_label in AVAILABLE_TIMEFRAMES[:4]:
        btn_text = f"✅ {tf_label}" if tf_code == active_tf else f"⏱ {tf_label}"
        row1.append(InlineKeyboardButton(text=btn_text, callback_data=f"tf_{tf_code}_{clean_sym}"))

    for tf_code, tf_label in AVAILABLE_TIMEFRAMES[4:]:
        btn_text = f"✅ {tf_label}" if tf_code == active_tf else f"⏱ {tf_label}"
        row2.append(InlineKeyboardButton(text=btn_text, callback_data=f"tf_{tf_code}_{clean_sym}"))

    row3 = [
        InlineKeyboardButton(text=get_text(user_id, "btn_inline_news"), callback_data=f"news_{clean_sym}"),
        InlineKeyboardButton(text=get_text(user_id, "btn_inline_alert"), callback_data=f"addalert_{clean_sym}"),
        InlineKeyboardButton(text=get_text(user_id, "btn_change_pair"), callback_data=f"menu_pairs_{active_tf}"),
    ]

    return InlineKeyboardMarkup(inline_keyboard=[row1, row2, row3])


def get_pairs_keyboard(user_id: int = 0, active_tf: str = "1h") -> InlineKeyboardMarkup:
    """Generates categorized inline buttons for Forex, Gold/Metals, and Crypto."""
    search_text = get_text(user_id, "btn_inline_search") if user_id else "🔍 Enter any ticker / Ввести тикер"

    r1 = [
        InlineKeyboardButton(text="EUR/USD", callback_data=f"tf_{active_tf}_EURUSD"),
        InlineKeyboardButton(text="GBP/USD", callback_data=f"tf_{active_tf}_GBPUSD"),
        InlineKeyboardButton(text="USD/JPY", callback_data=f"tf_{active_tf}_USDJPY"),
    ]
    r2 = [
        InlineKeyboardButton(text="🥇 Gold (XAU)", callback_data=f"tf_{active_tf}_GC=F"),
        InlineKeyboardButton(text="🥈 Silver (XAG)", callback_data=f"tf_{active_tf}_SI=F"),
        InlineKeyboardButton(text="🛢️ Oil (WTI)", callback_data=f"tf_{active_tf}_CL=F"),
    ]
    r3 = [
        InlineKeyboardButton(text="🪙 BTC", callback_data=f"tf_{active_tf}_BTC-USD"),
        InlineKeyboardButton(text="💎 ETH", callback_data=f"tf_{active_tf}_ETH-USD"),
        InlineKeyboardButton(text="☀️ SOL", callback_data=f"tf_{active_tf}_SOL-USD"),
        InlineKeyboardButton(text="💎 TON", callback_data=f"tf_{active_tf}_TON11419-USD"),
    ]
    r4 = [
        InlineKeyboardButton(text=search_text, callback_data="prompt_custom_symbol")
    ]
    return InlineKeyboardMarkup(inline_keyboard=[r1, r2, r3, r4])


def get_alert_pairs_keyboard(user_id: int = 0) -> InlineKeyboardMarkup:
    """Generates asset selection buttons specifically for setting an alert."""
    search_text = get_text(user_id, "btn_inline_search") if user_id else "🔍 Enter ticker / Ввести тикер"

    r1 = [
        InlineKeyboardButton(text="EUR/USD", callback_data="addalert_EURUSD"),
        InlineKeyboardButton(text="GBP/USD", callback_data="addalert_GBPUSD"),
        InlineKeyboardButton(text="USD/JPY", callback_data="addalert_USDJPY"),
    ]
    r2 = [
        InlineKeyboardButton(text="🥇 Gold (XAU)", callback_data="addalert_GC=F"),
        InlineKeyboardButton(text="🥈 Silver (XAG)", callback_data="addalert_SI=F"),
        InlineKeyboardButton(text="🛢️ Oil (WTI)", callback_data="addalert_CL=F"),
    ]
    r3 = [
        InlineKeyboardButton(text="🪙 BTC", callback_data="addalert_BTC-USD"),
        InlineKeyboardButton(text="💎 ETH", callback_data="addalert_ETH-USD"),
        InlineKeyboardButton(text="☀️ SOL", callback_data="addalert_SOL-USD"),
        InlineKeyboardButton(text="💎 TON", callback_data="addalert_TON11419-USD"),
    ]
    r4 = [
        InlineKeyboardButton(text=search_text, callback_data="prompt_custom_alert_symbol")
    ]
    return InlineKeyboardMarkup(inline_keyboard=[r1, r2, r3, r4])


def get_settings_main_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Generates category selection keyboard for Settings."""
    btn_lang = InlineKeyboardButton(text=get_text(user_id, "btn_set_lang"), callback_data="menu_settings_lang")
    btn_style = InlineKeyboardButton(text=get_text(user_id, "btn_set_style"), callback_data="menu_settings_style")
    return InlineKeyboardMarkup(inline_keyboard=[[btn_lang], [btn_style]])


def get_language_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Generates inline buttons for language selection."""
    current_lang = get_user_lang(user_id)
    buttons = []

    for lang_code, lang_name in SUPPORTED_LANGUAGES.items():
        prefix = "✅ " if lang_code == current_lang else ""
        buttons.append([InlineKeyboardButton(text=f"{prefix}{lang_name}", callback_data=f"setlang_{lang_code}")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_style_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Generates inline buttons for chart visual style selection."""
    current_style = get_user_chart_style(user_id)
    buttons = []

    for style_code, style_name in SUPPORTED_CHART_STYLES.items():
        prefix = "✅ " if style_code == current_style else ""
        buttons.append([InlineKeyboardButton(text=f"{prefix}{style_name}", callback_data=f"setstyle_{style_code}")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_alerts_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Generates inline keyboard for user alert management."""
    alerts = get_user_alerts(user_id)
    buttons = []

    buttons.append([
        InlineKeyboardButton(
            text=f"➕ {get_text(user_id, 'btn_add_alert')}",
            callback_data="menu_alert_pairs"
        )
    ])

    for alert in alerts:
        sym_name = get_display_pair_name(alert['symbol'])
        cond_icon = "⬆️" if alert['condition'] == "ABOVE" else "⬇️"
        btn_text = f"❌ {sym_name} {cond_icon} {alert['target_price']:.5f}"
        buttons.append([InlineKeyboardButton(text=btn_text, callback_data=f"delalert_{alert['id']}")])

    if alerts:
        buttons.append([InlineKeyboardButton(text=get_text(user_id, "btn_clear_alerts"), callback_data="clear_all_alerts")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("start"))
async def cmd_start(message: Message):
    user_id = message.from_user.id
    welcome_text = get_text(user_id, "welcome")
    await message.answer(welcome_text, reply_markup=get_main_reply_keyboard(user_id), parse_mode="Markdown")
    await message.answer(get_text(user_id, "select_pair"), reply_markup=get_pairs_keyboard(user_id, "1h"), parse_mode="Markdown")


@router.message(Command("help"))
@router.message(F.text.in_({"❓ Справка", "❓ Help", "❓ Довідка"}))
async def cmd_help(message: Message):
    user_id = message.from_user.id
    help_text = get_text(user_id, "help")
    await message.answer(help_text, reply_markup=get_pairs_keyboard(user_id, "1h"), parse_mode="Markdown")


@router.message(Command("settings"))
@router.message(Command("language"))
@router.message(F.text.in_({"⚙️ Настройки", "⚙️ Settings", "⚙️ Налаштування"}))
async def cmd_settings(message: Message):
    user_id = message.from_user.id
    title = get_text(user_id, "settings_title")
    await message.answer(title, reply_markup=get_settings_main_keyboard(user_id), parse_mode="Markdown")


@router.message(Command("alerts"))
@router.message(F.text.in_({"🔔 Алерты", "🔔 Alerts", "🔔 Сповіщення"}))
async def cmd_alerts(message: Message):
    user_id = message.from_user.id
    alerts = get_user_alerts(user_id)

    if not alerts:
        text = get_text(user_id, "no_alerts")
    else:
        text = get_text(user_id, "alerts_title")
        for a in alerts:
            name = get_display_pair_name(a["symbol"])
            icon = "📈 (>)" if a["condition"] == "ABOVE" else "📉 (<)"
            text += f"• **{name}:** `{a['target_price']:.5f}` {icon}\n"

    await message.answer(text, reply_markup=get_alerts_keyboard(user_id), parse_mode="Markdown")


@router.message(Command("news"))
@router.message(F.text.in_({"📰 Новости & ФРС", "📰 News & Fed", "📰 Новини & ФРС"}))
async def cmd_news(message: Message, command: CommandObject = None):
    user_id = message.from_user.id
    if command and command.args:
        symbol = command.args.strip()
        set_user_pair(user_id, symbol)
    else:
        symbol = get_user_pair(user_id)

    await render_news_report(message, symbol, user_id=user_id)


@router.message(Command("pairs"))
@router.message(F.text.in_({"💱 Выбрать актив", "💱 Select Asset", "💱 Обрати актив", "💱 Выбрать пару"}))
async def cmd_pairs(message: Message):
    user_id = message.from_user.id
    text = get_text(user_id, "select_pair")
    await message.answer(text, reply_markup=get_pairs_keyboard(user_id, "1h"), parse_mode="Markdown")


@router.message(F.text.in_({"⏱ Таймфреймы", "⏱ Timeframes"}))
async def cmd_timeframes_menu(message: Message):
    user_id = message.from_user.id
    current_pair = get_user_pair(user_id)
    display_name = get_display_pair_name(current_pair)
    text = get_text(user_id, "select_tf", pair=display_name)
    await message.answer(text, reply_markup=get_timeframe_keyboard(user_id, current_pair, "1h"), parse_mode="Markdown")


@router.message(F.text.in_({"📈 Все рынки", "📈 All Markets", "📈 Усі ринки", "📈 Все валюты"}))
async def cmd_all_currencies(message: Message):
    user_id = message.from_user.id
    msg = await message.answer(get_text(user_id, "loading"))
    results = []

    for symbol in DEFAULT_PAIRS:
        data = analyze_pair(symbol, "1h")
        if data:
            dir_1h = "+" if data["change_tf_pct"] >= 0 else ""
            dir_24h = "+" if data["change_24h_pct"] >= 0 else ""
            results.append(
                f"• **{data['name']}:** `{data['price']:.5f}` | 1h: `{dir_1h}{data['change_tf_pct']:.2f}%` | 24h: `{dir_24h}{data['change_24h_pct']:.2f}%`"
            )

    if not results:
        await msg.edit_text("❌ Error fetching market data.")
        return

    response = get_text(user_id, "all_pairs_title") + "\n\n" + "\n".join(results)
    await msg.edit_text(response, reply_markup=get_pairs_keyboard(user_id, "1h"), parse_mode="Markdown")


@router.message(Command("price"))
@router.message(F.text.startswith("📊 "))
async def cmd_price(message: Message, command: CommandObject = None):
    user_id = message.from_user.id
    if command and command.args:
        symbol = command.args.strip()
        set_user_pair(user_id, symbol)
    else:
        symbol = get_user_pair(user_id)

    timeframe = "1h"
    msg = await message.answer(f"⏳ **{symbol.upper()}** ({timeframe})...")
    await render_report(msg, symbol, timeframe, user_id=user_id)


@router.message(Command("analytics"))
async def cmd_analytics(message: Message, command: CommandObject = None):
    user_id = message.from_user.id
    if command and command.args:
        symbol = command.args.strip()
        set_user_pair(user_id, symbol)
    else:
        symbol = get_user_pair(user_id)

    timeframe = "1h"
    msg = await message.answer(f"⏳ **{symbol.upper()}** ({timeframe})...")
    await render_report(msg, symbol, timeframe, user_id=user_id)


# Handler for user entering alert target price string
@router.message(lambda msg: get_user_state(msg.from_user.id) == "WAITING_FOR_PRICE_ALERT")
async def process_alert_price_input(message: Message):
    user_id = message.from_user.id
    text = message.text.strip().replace(",", ".")

    try:
        target_price = float(text)
    except ValueError:
        await message.answer(get_text(user_id, "invalid_price"), parse_mode="Markdown")
        return

    symbol = get_user_pair(user_id)
    display_name = get_display_pair_name(symbol)

    data = analyze_pair(symbol, "1h")
    current_price = data["price"] if data else target_price

    alert = add_alert(user_id, symbol, target_price, current_price)
    set_user_state(user_id, "")  # Reset state

    lang = get_user_lang(user_id)
    cond_text = "ABOVE 📈" if alert["condition"] == "ABOVE" else "BELOW 📉"
    if lang == "ru":
        cond_text = "ВЫШЕ 📈" if alert["condition"] == "ABOVE" else "НИЖЕ 📉"
    elif lang == "uk":
        cond_text = "ВИЩЕ 📈" if alert["condition"] == "ABOVE" else "НИЖЧЕ 📉"

    msg_text = get_text(user_id, "alert_added", pair=display_name, target=target_price, condition=cond_text)
    await message.answer(msg_text, reply_markup=get_alerts_keyboard(user_id), parse_mode="Markdown")


# Handler for user entering a custom ticker string
@router.message(lambda msg: get_user_state(msg.from_user.id) == "WAITING_FOR_CUSTOM_SYMBOL")
async def process_custom_symbol_input(message: Message):
    user_id = message.from_user.id
    symbol_input = message.text.strip()

    set_user_state(user_id, "")
    norm_symbol = normalize_symbol(symbol_input)
    set_user_pair(user_id, norm_symbol)

    msg = await message.answer(f"⏳ Loading **{symbol_input.upper()}**...")
    await render_report(msg, norm_symbol, "1h", user_id=user_id)


# Catch-all text handler for direct ticker queries (e.g. user sends "gold" or "btc")
@router.message(F.text & ~F.text.startswith("/"))
async def handle_direct_text_query(message: Message):
    user_id = message.from_user.id
    text = message.text.strip()

    # Skip known menu buttons
    if text.startswith("📊") or text.startswith("💱") or text.startswith("⏱") or text.startswith("📈") or text.startswith("🔔") or text.startswith("⚙️") or text.startswith("❓") or text.startswith("📰"):
        return

    norm_symbol = normalize_symbol(text)
    data = analyze_pair(norm_symbol, "1h")
    if data:
        set_user_pair(user_id, norm_symbol)
        msg = await message.answer(f"⏳ Loading **{data['name']}**...")
        await render_report(msg, norm_symbol, "1h", user_id=user_id)
    else:
        await message.answer(f"❌ Asset `{text}` not found on Yahoo Finance. Try ticker like `GOLD`, `BTC`, `SOL`, `EURUSD`.", parse_mode="Markdown")


async def render_news_report(message_or_query, symbol: str, user_id: Optional[int] = None):
    """Renders real-time financial market news & Central Bank Interest Rates (Fed / ECB / BoJ)."""
    if user_id is None:
        user_id = message_or_query.from_user.id

    lang = get_user_lang(user_id)
    norm_symbol = normalize_symbol(symbol)
    display_name = get_display_pair_name(norm_symbol)

    rates = get_macro_rates_summary(norm_symbol, lang=lang)
    news_items = fetch_asset_news(norm_symbol, max_items=4)

    fed = rates["fed"]
    secondary_cb = rates["secondary_cb"]

    title = get_text(user_id, "news_title", pair=display_name)
    cb_title = get_text(user_id, "fed_rates_title")

    lbl_meeting = get_text(user_id, "lbl_next_meeting")
    lbl_odds = get_text(user_id, "lbl_market_odds")
    lbl_latest = get_text(user_id, "lbl_latest_news")

    cb_lines = [
        f"• {fed['flag']} **{fed['name']}:** `{fed['rate']}` | **{fed['bias']}**\n"
        f"  {lbl_meeting} `{fed['next_meeting']}`\n"
        f"  {lbl_odds} `{fed['expectations']}`"
    ]

    if secondary_cb and secondary_cb["name"] != fed["name"]:
        cb_lines.append(
            f"• {secondary_cb['flag']} **{secondary_cb['name']}:** `{secondary_cb['rate']}` | **{secondary_cb['bias']}**\n"
            f"  {lbl_meeting} `{secondary_cb['next_meeting']}` | {lbl_odds} `{secondary_cb['expectations']}`"
        )

    news_text_lines = []
    if news_items:
        for idx, item in enumerate(news_items, 1):
            date_str = f" ({item['date']})" if item['date'] else ""
            news_text_lines.append(f"**{idx}. [{item['title']}]({item['link']})**\n🏛 _{item['publisher']}{date_str}_")
    else:
        news_text_lines.append(get_text(user_id, "lbl_no_news"))

    response = (
        f"{title}\n\n"
        f"{cb_title}\n" +
        "\n\n".join(cb_lines) +
        f"\n\n{lbl_latest}\n\n" +
        "\n\n".join(news_text_lines)
    )

    clean_sym = norm_symbol.replace("=X", "")
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text=get_text(user_id, "btn_back_dashboard"), callback_data=f"tf_1h_{clean_sym}"),
        InlineKeyboardButton(text=get_text(user_id, "btn_refresh_news"), callback_data=f"news_{clean_sym}")
    ]])

    if isinstance(message_or_query, Message):
        await message_or_query.answer(response, reply_markup=kb, parse_mode="Markdown", disable_web_page_preview=True)
    else:
        await safe_edit_content(message_or_query, response, reply_markup=kb)


async def render_report(message_or_query, symbol: str, timeframe: str = "1h", user_id: Optional[int] = None):
    """Fetches data, renders TA analysis text, and fetches live TradingView or custom dark chart photo."""
    if user_id is None:
        user_id = message_or_query.from_user.id

    set_user_pair(user_id, symbol)

    data = analyze_pair(symbol, timeframe)
    if not data:
        text = f"❌ Error loading `{symbol}`."
        if isinstance(message_or_query, Message):
            await message_or_query.answer(text, parse_mode="Markdown")
        else:
            await safe_edit_content(message_or_query, text)
        return

    dir_tf = "🟢 +" if data["change_tf_pct"] >= 0 else "🔴 "
    dir_24h = "🟢 +" if data["change_24h_pct"] >= 0 else "🔴 "

    # Fully Localized Signals
    rsi_val = data["rsi"]
    if rsi_val >= 70:
        rsi_sig_text = get_text(user_id, "sig_overbought")
    elif rsi_val <= 30:
        rsi_sig_text = get_text(user_id, "sig_oversold")
    elif rsi_val > 55:
        rsi_sig_text = get_text(user_id, "sig_bullish")
    elif rsi_val < 45:
        rsi_sig_text = get_text(user_id, "sig_bearish")
    else:
        rsi_sig_text = get_text(user_id, "sig_neutral")

    trend_sig_text = get_text(user_id, "sig_bullish") if data["ema_9"] > data["ema_21"] else get_text(user_id, "sig_bearish")

    title = get_text(user_id, "report_title", name=data['name'])
    price_str = f"{get_text(user_id, 'curr_price')} `{data['price']:.5f}`"
    change_tf_str = f"{get_text(user_id, 'change_tf', tf=data['timeframe'].upper())} `{dir_tf}{data['change_tf_pct']:.2f}%`"
    change_24h_str = f"{get_text(user_id, 'change_24h')} `{dir_24h}{data['change_24h_pct']:.2f}%`"
    rsi_str = f"{get_text(user_id, 'rsi_label')} `{data['rsi']:.1f}` ({rsi_sig_text})"
    trend_str = f"{get_text(user_id, 'trend_label')} {trend_sig_text}"
    ma_title = get_text(user_id, "ma_title", tf=data['timeframe'].upper())
    last_candle_str = f"{get_text(user_id, 'last_candle')} `{data['timestamp']}`"
    click_below_str = get_text(user_id, "click_below")

    response = (
        f"{title}\n\n"
        f"{price_str}\n"
        f"{change_tf_str}\n"
        f"{change_24h_str}\n"
        f"{rsi_str}\n"
        f"{trend_str}\n\n"
        f"{ma_title}\n"
        f"• EMA 9: `{data['ema_9']:.5f}` | EMA 21: `{data['ema_21']:.5f}`\n"
        f"• SMA 20: `{data['sma_20']:.5f}` | SMA 50: `{data['sma_50']:.5f}`\n\n"
        f"{last_candle_str}\n"
        f"{click_below_str}"
    )

    kb = get_timeframe_keyboard(user_id, data["symbol"], data["timeframe"])

    # Fetch Chart Image using selected style
    user_style = get_user_chart_style(user_id)
    chart_bytes = None

    tf_info = TIMEFRAME_CONFIG.get(timeframe.lower(), TIMEFRAME_CONFIG["1h"])
    df = fetch_forex_data(data["symbol"], period=tf_info["period"], interval=tf_info["interval"])

    if user_style == "tradingview_live":
        chart_bytes = await fetch_tradingview_live_snapshot(data["symbol"], timeframe, df=df)
    else:
        chart_bytes = generate_trend_chart(df, data["name"], data["timeframe_label"], style=user_style)

    if not chart_bytes:
        chart_bytes = generate_trend_chart(df, data["name"], data["timeframe_label"], style="tradingview")

    photo_file = BufferedInputFile(chart_bytes, filename=f"{data['symbol']}_chart.png") if chart_bytes else None

    if isinstance(message_or_query, Message):
        if photo_file:
            await message_or_query.answer_photo(photo=photo_file, caption=response, reply_markup=kb, parse_mode="Markdown")
            try:
                await message_or_query.delete()
            except Exception:
                pass
        else:
            await message_or_query.edit_text(response, reply_markup=kb, parse_mode="Markdown")
    else:
        # Callback query from inline button
        if photo_file and message_or_query.message.photo:
            try:
                media = InputMediaPhoto(media=photo_file, caption=response, parse_mode="Markdown")
                await message_or_query.message.edit_media(media=media, reply_markup=kb)
            except Exception:
                pass
        else:
            if photo_file:
                await message_or_query.message.answer_photo(photo=photo_file, caption=response, reply_markup=kb, parse_mode="Markdown")
            else:
                await safe_edit_content(message_or_query, response, reply_markup=kb)


@router.callback_query(F.data.startswith("news_"))
async def handle_news_callback(query: CallbackQuery):
    user_id = query.from_user.id
    symbol = query.data.split("_")[1]
    norm_symbol = normalize_symbol(symbol)
    set_user_pair(user_id, norm_symbol)

    await query.answer("Loading Market News & Fed Rates...")
    await render_news_report(query, norm_symbol, user_id=user_id)


@router.callback_query(F.data == "prompt_custom_symbol")
async def handle_prompt_custom_symbol_callback(query: CallbackQuery):
    user_id = query.from_user.id
    set_user_state(user_id, "WAITING_FOR_CUSTOM_SYMBOL")
    await query.answer()
    await query.message.answer(get_text(user_id, "prompt_custom_symbol"), parse_mode="Markdown")


@router.callback_query(F.data == "menu_alert_pairs")
async def handle_alert_pairs_menu_callback(query: CallbackQuery):
    user_id = query.from_user.id
    await query.answer()
    await safe_edit_content(
        query,
        get_text(user_id, "select_alert_pair"),
        reply_markup=get_alert_pairs_keyboard(user_id)
    )


@router.callback_query(F.data == "prompt_custom_alert_symbol")
async def handle_prompt_custom_alert_symbol_callback(query: CallbackQuery):
    user_id = query.from_user.id
    set_user_state(user_id, "WAITING_FOR_CUSTOM_SYMBOL")
    await query.answer()
    await query.message.answer(get_text(user_id, "prompt_custom_symbol"), parse_mode="Markdown")


@router.callback_query(F.data.startswith("addalert_"))
async def handle_add_alert_callback(query: CallbackQuery):
    user_id = query.from_user.id
    symbol = query.data.split("_")[1]
    norm_symbol = normalize_symbol(symbol)
    set_user_pair(user_id, norm_symbol)
    set_user_state(user_id, "WAITING_FOR_PRICE_ALERT")

    display_name = get_display_pair_name(norm_symbol)
    data = analyze_pair(norm_symbol, "1h")
    curr_p = data["price"] if data else 155.0

    example_price = curr_p * 1.005
    prompt = get_text(user_id, "prompt_alert_price", pair=display_name, price=curr_p, example=example_price)
    await query.answer()
    await query.message.answer(prompt, parse_mode="Markdown")


@router.callback_query(F.data.startswith("delalert_"))
async def handle_delete_alert_callback(query: CallbackQuery):
    user_id = query.from_user.id
    alert_id = int(query.data.split("_")[1])
    delete_alert(user_id, alert_id)

    await query.answer("Alert deleted")
    await cmd_alerts(query.message)


@router.callback_query(F.data == "clear_all_alerts")
async def handle_clear_alerts_callback(query: CallbackQuery):
    user_id = query.from_user.id
    clear_user_alerts(user_id)
    await query.answer("Alerts deleted")
    await cmd_alerts(query.message)


@router.callback_query(F.data == "menu_settings_lang")
async def handle_settings_lang_menu(query: CallbackQuery):
    user_id = query.from_user.id
    await query.answer()
    await safe_edit_content(query, get_text(user_id, "settings_lang_title"), reply_markup=get_language_keyboard(user_id))


@router.callback_query(F.data == "menu_settings_style")
async def handle_settings_style_menu(query: CallbackQuery):
    user_id = query.from_user.id
    await query.answer()
    await safe_edit_content(query, get_text(user_id, "settings_style_title"), reply_markup=get_style_keyboard(user_id))


@router.callback_query(F.data.startswith("setlang_"))
async def handle_set_language_callback(query: CallbackQuery):
    user_id = query.from_user.id
    lang_code = query.data.split("_")[1]
    set_user_lang(user_id, lang_code)

    updated_msg = get_text(user_id, "lang_updated")
    await query.answer(updated_msg)
    
    # 1. Update inline language settings menu to reflect selected checkmark ✅
    await safe_edit_content(query, get_text(user_id, "settings_lang_title"), reply_markup=get_language_keyboard(user_id))

    # 2. Update persistent bottom reply keyboard buttons immediately
    await query.message.answer(
        updated_msg,
        reply_markup=get_main_reply_keyboard(user_id),
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("setstyle_"))
async def handle_set_style_callback(query: CallbackQuery):
    user_id = query.from_user.id
    style_code = query.data.split("_")[1]
    set_user_chart_style(user_id, style_code)

    style_name = SUPPORTED_CHART_STYLES.get(style_code, style_code)
    await query.answer(f"Style updated: {style_name}")

    # Immediately render and show fresh chart with newly selected style!
    symbol = get_user_pair(user_id)
    await render_report(query, symbol, "1h", user_id=user_id)


@router.callback_query(F.data.startswith("tf_"))
async def handle_timeframe_callback(query: CallbackQuery):
    user_id = query.from_user.id
    parts = query.data.split("_")
    if len(parts) >= 3:
        timeframe = parts[1]
        raw_symbol = parts[2]
        symbol = normalize_symbol(raw_symbol)

        old_pair = get_user_pair(user_id)
        set_user_pair(user_id, symbol)

        await query.answer(f"Loading {get_display_pair_name(symbol)} ({timeframe.upper()})...")
        await render_report(query, symbol, timeframe, user_id=user_id)

        if old_pair != get_user_pair(user_id):
            display_name = get_display_pair_name(symbol)
            msg_text = get_text(user_id, "pair_selected", pair=display_name)
            await query.message.answer(msg_text, reply_markup=get_main_reply_keyboard(user_id), parse_mode="Markdown")
    else:
        await query.answer()


@router.callback_query(F.data.startswith("menu_pairs_"))
async def handle_pairs_menu_callback(query: CallbackQuery):
    user_id = query.from_user.id
    parts = query.data.split("_")
    tf = parts[2] if len(parts) >= 3 else "1h"
    await query.answer()
    await safe_edit_content(
        query,
        get_text(user_id, "select_pair"),
        reply_markup=get_pairs_keyboard(user_id, tf)
    )
