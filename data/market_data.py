import yfinance as yf


def fetch_ohlcv(ticker, period="1y", interval="1d"):
    df = yf.download(ticker, period=period, interval=interval, auto_adjust=True, progress=False)
    if df.empty:
        raise ValueError(f"No data returned for {ticker}")
    df.dropna(inplace=True)
    return df
