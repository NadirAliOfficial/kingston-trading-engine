import time
import config
from data.market_data import fetch_ohlcv
from signals.signal_engine import generate_signals
from decisions.decision_engine import check_market_filter, make_decision
from risk.risk_engine import (
    get_open_positions, calculate_position_size,
    can_trade, record_entry, record_exit, update_peak,
)
from execution.ibkr_executor import connect, disconnect, get_account_value, place_buy, place_sell
from exit.exit_monitor import check_exit
from logger.trade_logger import get_signal_logger, get_trade_logger

DIVIDER = "=" * 70


def _format_signals(signals):
    return "  ".join(f"{k}: {'Y' if v else 'N'}" for k, v in signals.items())


def run():
    signal_log = get_signal_logger()
    trade_log = get_trade_logger()

    signal_log.info("=== EOD Evaluation Started ===")
    print(f"\n{DIVIDER}")
    print("  RULE-BASED TRADING SYSTEM  |  EOD Evaluation")
    print(DIVIDER)

    ib = connect(config)
    account_value = get_account_value(ib)
    signal_log.info(f"IBKR connected | account value={account_value:.2f}")
    print(f"\nIBKR Paper Account: ${account_value:,.2f}")

    # --- Exit Monitor ---
    print(f"\n{DIVIDER}")
    print("  EXIT MONITOR")
    print(DIVIDER)

    open_positions = get_open_positions()
    if not open_positions:
        print("  No open positions.")
    else:
        for pos in open_positions:
            ticker = pos["ticker"]
            df = fetch_ohlcv(ticker, config.DATA_PERIOD, config.DATA_INTERVAL)
            _, latest = generate_signals(df, config)
            update_peak(ticker, latest["price"])
            if latest["price"] > pos["peak_price"]:
                pos["peak_price"] = latest["price"]

            should_exit, exit_reason = check_exit(pos, latest, config)
            is_loss = latest["price"] < pos["entry_price"]

            if should_exit:
                trade = place_sell(ib, ticker, pos["shares"])
                fill_price = trade.orderStatus.avgFillPrice or latest["price"]
                record_exit(ticker, fill_price, is_loss, config)
                trade_log.info(
                    f"EXIT | {ticker} | shares={pos['shares']} price={fill_price:.2f} "
                    f"status={trade.orderStatus.status} | {exit_reason}"
                )
                print(f"  {ticker} EXIT — {exit_reason} | order {trade.orderStatus.status}")
            else:
                signal_log.info(f"HOLD POSITION | {ticker} | price={latest['price']:.2f} | {exit_reason}")
                print(f"  {ticker} HOLD — {exit_reason}")

    # --- Market Filter ---
    print(f"\n{DIVIDER}")
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

    # --- Signal + Entry ---
    for ticker in config.TICKERS:
        df = fetch_ohlcv(ticker, config.DATA_PERIOD, config.DATA_INTERVAL)
        signals, latest = generate_signals(df, config)
        decision, reason = make_decision(signals, market_ok)

        signal_log.info(
            f"{ticker} | price={latest['price']:.2f} MA50={latest['ma50']:.2f} "
            f"MA200={latest['ma200']:.2f} MA20={latest['ma20']:.2f} RSI={latest['rsi']:.2f} "
            f"vol={latest['volume']:.0f} avg_vol={latest['avg_volume']:.0f} "
            f"5d_high={latest['high_5d']:.2f} | decision={decision} | {reason}"
        )

        if decision == "BUY":
            ok, risk_reason = can_trade(ticker, config)
            if ok:
                shares = calculate_position_size(account_value, latest["price"], config)
                trade = place_buy(ib, ticker, shares)
                fill_price = trade.orderStatus.avgFillPrice or latest["price"]
                record_entry(ticker, shares, fill_price)
                trade_log.info(
                    f"ENTRY BUY | {ticker} | shares={shares} price={fill_price:.2f} "
                    f"status={trade.orderStatus.status} | {reason}"
                )
                decision = "BUY"
                reason = f"executed {shares} shares @ {fill_price:.2f} | order {trade.orderStatus.status}"
            else:
                trade_log.warning(f"BLOCKED | {ticker} | {risk_reason}")
                decision = "BLOCK"
                reason = risk_reason
        elif decision == "BLOCK":
            trade_log.warning(f"BLOCKED | {ticker} | {reason}")

        sig_str = _format_signals(signals)
        print(f"  {ticker:<6}  [{decision:<6}]  {sig_str}")
        print(f"           Reason: {reason}")
        print()

    disconnect(ib)
    print(DIVIDER)
    signal_log.info("=== EOD Evaluation Complete ===")
    print("\nLogs written to logs/")


if __name__ == "__main__":
    while True:
        try:
            run()
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(300)
