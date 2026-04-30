def check_market_filter(spy_latest, config):
    spy_above_ma200 = spy_latest["price"] > spy_latest["ma200"]
    spy_rsi_ok = spy_latest["rsi"] > config.RSI_MARKET_MIN
    return spy_above_ma200 and spy_rsi_ok


def make_decision(ticker, signals, market_filter_pass):
    if not market_filter_pass:
        return "BLOCK", "market filter failed: SPY below MA200 or RSI < 50"

    failed = [k for k, v in signals.items() if not v]
    if not failed:
        return "BUY", "all entry conditions met"

    return "HOLD", f"conditions not met: {', '.join(failed)}"
