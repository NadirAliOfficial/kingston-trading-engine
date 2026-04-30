import config
from data.market_data import fetch_ohlcv
from signals.signal_engine import generate_signals
from decisions.decision_engine import check_market_filter, make_decision
from logger.trade_logger import get_signal_logger, get_trade_logger

DIVIDER = "=" * 70


def _format_signals(signals):
    return "  ".join(f"{k}: {'Y' if v else 'N'}" for k, v in signals.items())


def run():
    signal_log = get_signal_logger()
    trade_log = get_trade_logger()

    signal_log.info("=== EOD Signal Evaluation Started ===")
    print(f"\n{DIVIDER}")
    print("  RULE-BASED TRADING SYSTEM  |  EOD Signal Evaluation")
    print(DIVIDER)

    spy_df = fetch_ohlcv(config.MARKET_FILTER_TICKER, config.DATA_PERIOD, config.DATA_INTERVAL)
    _, spy_latest = generate_signals(spy_df, config)
    market_ok = check_market_filter(spy_latest, config)

    filter_status = "PASS" if market_ok else "FAIL"
    signal_log.info(
        f"MARKET FILTER | SPY price={spy_latest['price']:.2f} "
        f"MA200={spy_latest['ma200']:.2f} RSI={spy_latest['rsi']:.2f} | {filter_status}"
    )
    print(f"\nMarket Filter (SPY): {filter_status}")
    print(f"  SPY price={spy_latest['price']:.2f}  MA200={spy_latest['ma200']:.2f}  RSI={spy_latest['rsi']:.2f}")
    print(f"\n{DIVIDER}")
    print(f"  {'TICKER':<6}  {'DECISION':<8}  SIGNALS")
    print(DIVIDER)

    for ticker in config.TICKERS:
        df = fetch_ohlcv(ticker, config.DATA_PERIOD, config.DATA_INTERVAL)
        signals, latest = generate_signals(df, config)
        decision, reason = make_decision(ticker, signals, market_ok)

        signal_log.info(
            f"{ticker} | price={latest['price']:.2f} MA50={latest['ma50']:.2f} "
            f"MA200={latest['ma200']:.2f} MA20={latest['ma20']:.2f} RSI={latest['rsi']:.2f} "
            f"vol={latest['volume']:.0f} avg_vol={latest['avg_volume']:.0f} "
            f"5d_high={latest['high_5d']:.2f} | decision={decision} | {reason}"
        )

        if decision == "BUY":
            trade_log.info(f"SIGNAL BUY | {ticker} | {reason}")
        elif decision == "BLOCK":
            trade_log.warning(f"BLOCKED | {ticker} | {reason}")

        sig_str = _format_signals(signals)
        print(f"  {ticker:<6}  [{decision:<6}]  {sig_str}")
        print(f"           Reason: {reason}")
        print()

    print(DIVIDER)
    signal_log.info("=== EOD Signal Evaluation Complete ===")
    print("\nLogs written to logs/")


if __name__ == "__main__":
    run()
