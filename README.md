# Rule-Based Trading System — Phase 1

Modular rule-based trading decision engine integrated with IBKR. Phase 1 covers data ingestion, signal generation, and decision output via CLI with full logging. No live trades are executed in this phase.

---

## Architecture

```
kingston-trading-engine/
├── config.py            # All parameters (tickers, MA periods, RSI thresholds, etc.)
├── main.py              # Entry point — runs EOD evaluation and prints decisions
├── data/
│   └── market_data.py   # Data layer — fetches OHLCV via yfinance
├── signals/
│   └── signal_engine.py # Signal layer — computes MAs, RSI, volume, breakout
├── decisions/
│   └── decision_engine.py # Decision layer — applies market filter and entry rules
├── logger/
│   └── trade_logger.py  # Logging layer — writes signals and trades to dated log files
└── logs/                # Runtime log output (created automatically)
```

---

## Modules

### Data Layer (`data/market_data.py`)
Fetches daily OHLCV data for each ticker using `yfinance`. Configurable period and interval via `config.py`.

### Signal Engine (`signals/signal_engine.py`)
Computes all technical indicators from raw OHLCV:
- 50-day, 200-day, 20-day simple moving averages
- RSI(14) using exponential smoothing
- 5-day high breakout level
- 20-day average volume

### Decision Engine (`decisions/decision_engine.py`)
Applies entry rules per ticker after checking the market filter.

**Market Filter** — evaluated on SPY:
- SPY price > 200-day MA
- SPY RSI > 50

**Entry Rules** — all must pass:
- Price > 50-day MA
- 50-day MA > 200-day MA
- RSI between 55 and 65
- Price above 5-day high (breakout)
- Volume > 1.2x 20-day average

**Decisions:**
- `BUY` — all entry conditions pass
- `HOLD` — market filter passes but one or more entry conditions fail
- `BLOCK` — market filter fails (no trades for any ticker)

### Logging Layer (`logger/trade_logger.py`)
Writes two dated log files to `logs/`:
- `signals_YYYYMMDD.log` — full signal detail for every ticker evaluated
- `trades_YYYYMMDD.log` — BUY signals and BLOCK events only

---

## Configuration (`config.py`)

| Parameter | Default | Description |
|---|---|---|
| `TICKERS` | SPY, QQQ, AAPL, MSFT | Instruments to evaluate |
| `MARKET_FILTER_TICKER` | SPY | Market regime filter ticker |
| `MA_50` | 50 | Fast MA period |
| `MA_200` | 200 | Trend MA period |
| `MA_20` | 20 | Exit MA period |
| `HIGH_LOOKBACK` | 5 | Days for breakout level |
| `RSI_PERIOD` | 14 | RSI lookback |
| `RSI_ENTRY_LOW` | 55 | RSI entry lower bound |
| `RSI_ENTRY_HIGH` | 65 | RSI entry upper bound |
| `RSI_MARKET_MIN` | 50 | SPY RSI minimum for market filter |
| `VOLUME_MULTIPLIER` | 1.2 | Volume surge threshold |

---

## Setup

```bash
pip install -r requirements.txt
python main.py
```

---

## Phase 2 (Upcoming)

- Risk engine: 1% risk per trade, max 3 open positions, daily loss limit (2 losses), 1-day cooldown
- IBKR paper execution via `ib_insync`
- Exit rule monitoring: MA20 cross, RSI < 50, 2% trailing stop, 2% hard stop
- Full trade lifecycle logging (entry, exit, blocked)
<!-- updated: 2025-12-09 -->

