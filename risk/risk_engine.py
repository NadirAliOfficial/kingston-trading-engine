import json
import math
from datetime import date, timedelta

STATE_FILE = "state/positions.json"


def _load():
    with open(STATE_FILE, encoding="utf-8") as f:
        return json.load(f)


def _save(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def get_open_positions():
    return _load()["open_positions"]


def calculate_position_size(account_value, price, config):
    risk_amount = account_value * config.RISK_PER_TRADE
    shares = math.floor(risk_amount / (price * config.HARD_STOP_PCT))
    return max(shares, 1)


def can_trade(ticker, config):
    state = _load()
    today = str(date.today())

    if state["cooldown_until"] and today <= state["cooldown_until"]:
        return False, f"cooldown active until {state['cooldown_until']}"

    open_tickers = [p["ticker"] for p in state["open_positions"]]
    if ticker in open_tickers:
        return False, f"already holding {ticker}"

    if len(state["open_positions"]) >= config.MAX_POSITIONS:
        return False, f"max positions reached ({config.MAX_POSITIONS})"

    daily_losses = state["daily_losses"].get(today, 0)
    if daily_losses >= config.DAILY_LOSS_LIMIT:
        return False, f"daily loss limit reached ({config.DAILY_LOSS_LIMIT} losses)"

    return True, "risk checks passed"


def record_entry(ticker, shares, entry_price):
    state = _load()
    state["open_positions"].append({
        "ticker": ticker,
        "shares": shares,
        "entry_price": entry_price,
        "peak_price": entry_price,
        "entry_date": str(date.today()),
    })
    _save(state)


def record_exit(ticker, exit_price, is_loss, config):
    state = _load()
    state["open_positions"] = [p for p in state["open_positions"] if p["ticker"] != ticker]

    if is_loss:
        today = str(date.today())
        state["daily_losses"][today] = state["daily_losses"].get(today, 0) + 1
        if state["daily_losses"][today] >= config.DAILY_LOSS_LIMIT:
            cooldown = date.today() + timedelta(days=config.COOLDOWN_DAYS)
            state["cooldown_until"] = str(cooldown)

    _save(state)


def update_peak(ticker, current_price):
    state = _load()
    for p in state["open_positions"]:
        if p["ticker"] == ticker and current_price > p["peak_price"]:
            p["peak_price"] = current_price
    _save(state)
