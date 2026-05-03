def check_exit(position, latest, config):
    entry_price = position["entry_price"]
    peak_price = position["peak_price"]
    price = latest["price"]

    hard_stop = entry_price * (1 - config.HARD_STOP_PCT)
    trailing_stop = peak_price * (1 - config.TRAILING_STOP_PCT)

    if price <= hard_stop:
        return True, f"hard stop hit (price={price:.2f} stop={hard_stop:.2f})"

    if price <= trailing_stop:
        return True, f"trailing stop hit (price={price:.2f} stop={trailing_stop:.2f} peak={peak_price:.2f})"

    if price < latest["ma20"]:
        return True, f"price crossed below MA20 (price={price:.2f} MA20={latest['ma20']:.2f})"

    if latest["rsi"] < config.RSI_EXIT_MIN:
        return True, f"RSI dropped below {config.RSI_EXIT_MIN} (RSI={latest['rsi']:.2f})"

    return False, "hold"
