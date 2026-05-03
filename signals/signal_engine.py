def _compute_rsi(series, period):
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))


def generate_signals(df, config):
    close = df["Close"].squeeze()
    volume = df["Volume"].squeeze()
    high = df["High"].squeeze()

    ma50 = close.rolling(config.MA_50).mean()
    ma200 = close.rolling(config.MA_200).mean()
    ma20 = close.rolling(config.MA_20).mean()
    rsi = _compute_rsi(close, config.RSI_PERIOD)
    avg_volume = volume.rolling(config.VOLUME_AVG_PERIOD).mean()
    high_5d = high.rolling(config.HIGH_LOOKBACK).max().shift(1)

    latest = {
        "price": float(close.iloc[-1]),
        "ma50": float(ma50.iloc[-1]),
        "ma200": float(ma200.iloc[-1]),
        "ma20": float(ma20.iloc[-1]),
        "rsi": float(rsi.iloc[-1]),
        "volume": float(volume.iloc[-1]),
        "avg_volume": float(avg_volume.iloc[-1]),
        "high_5d": float(high_5d.iloc[-1]),
    }

    signals = {
        "price_above_ma50": latest["price"] > latest["ma50"],
        "ma50_above_ma200": latest["ma50"] > latest["ma200"],
        "rsi_in_range": config.RSI_ENTRY_LOW <= latest["rsi"] <= config.RSI_ENTRY_HIGH,
        "breakout_5d_high": latest["price"] > latest["high_5d"],
        "volume_surge": latest["volume"] > config.VOLUME_MULTIPLIER * latest["avg_volume"],
    }

    return signals, latest
