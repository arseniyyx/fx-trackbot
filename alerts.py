import asyncio
import logging
from typing import Dict, List, Any
from aiogram import Bot
from services.forex_service import analyze_pair, normalize_symbol
from config import SYMBOL_NAMES
from locales import get_text

user_alerts: Dict[int, List[Dict[str, Any]]] = {}
_alert_id_counter = 1


def add_alert(user_id: int, symbol: str, target_price: float, current_price: float) -> Dict[str, Any]:
    """Adds a new price alert for a user."""
    global _alert_id_counter
    clean_symbol = symbol.upper().replace("/", "").replace(" ", "").replace("-", "").replace("=X", "")
    condition = "ABOVE" if target_price >= current_price else "BELOW"

    alert = {
        "id": _alert_id_counter,
        "symbol": clean_symbol,
        "target_price": target_price,
        "condition": condition,
    }
    _alert_id_counter += 1

    if user_id not in user_alerts:
        user_alerts[user_id] = []
    user_alerts[user_id].append(alert)
    return alert


def get_user_alerts(user_id: int) -> List[Dict[str, Any]]:
    """Returns list of active alerts for a user."""
    return user_alerts.get(user_id, [])


def delete_alert(user_id: int, alert_id: int) -> bool:
    """Deletes a specific alert by ID."""
    if user_id in user_alerts:
        initial_len = len(user_alerts[user_id])
        user_alerts[user_id] = [a for a in user_alerts[user_id] if a["id"] != alert_id]
        return len(user_alerts[user_id]) < initial_len
    return False


def clear_user_alerts(user_id: int):
    """Clears all alerts for a user."""
    if user_id in user_alerts:
        user_alerts[user_id] = []


async def check_alerts_loop(bot: Bot):
    """Background task running every 60 seconds to check active price alerts."""
    logging.info("Starting background Price Alert Monitoring task...")
    while True:
        try:
            await asyncio.sleep(60)
            if not user_alerts:
                continue

            # Group symbols to minimize API calls
            symbols_to_check = set()
            for alerts in user_alerts.values():
                for alert in alerts:
                    symbols_to_check.add(alert["symbol"])

            market_data = {}
            for sym in symbols_to_check:
                data = analyze_pair(sym, "1h")
                if data:
                    market_data[sym] = data

            # Check alerts
            for user_id, alerts in list(user_alerts.items()):
                triggered = []
                for alert in list(alerts):
                    sym = alert["symbol"]
                    if sym not in market_data:
                        continue
                    data = market_data[sym]
                    price = data["price"]
                    target = alert["target_price"]
                    cond = alert["condition"]

                    should_trigger = False
                    if cond == "ABOVE" and price >= target:
                        should_trigger = True
                    elif cond == "BELOW" and price <= target:
                        should_trigger = True

                    if should_trigger:
                        triggered.append(alert)
                        display_name = SYMBOL_NAMES.get(normalize_symbol(sym), sym)
                        dir_icon = "📈 🚀" if cond == "ABOVE" else "📉 💥"

                        hdr = get_text(user_id, "alert_triggered")
                        lbl_price = get_text(user_id, "curr_price")
                        lbl_time = get_text(user_id, "last_candle")

                        msg = (
                            f"{hdr} {dir_icon}\n\n"
                            f"💱 **{display_name}**\n"
                            f"{lbl_price} `{price:.5f}`\n"
                            f"🎯 Target ({cond}): `{target:.5f}`\n"
                            f"⚡ RSI (14): `{data['rsi']:.1f}`\n\n"
                            f"{lbl_time} `{data['timestamp']}`"
                        )
                        try:
                            await bot.send_message(user_id, msg, parse_mode="Markdown")
                        except Exception as e:
                            logging.error(f"Failed to send alert to {user_id}: {e}")

                # Remove triggered alerts
                if triggered:
                    user_alerts[user_id] = [a for a in user_alerts[user_id] if a not in triggered]

        except Exception as e:
            logging.error(f"Error in alert monitoring loop: {e}")
