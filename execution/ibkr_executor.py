from ib_insync import IB, Stock, MarketOrder


def connect(config):
    ib = IB()
    ib.connect(config.IBKR_HOST, config.IBKR_PORT, clientId=config.IBKR_CLIENT_ID)
    return ib


def disconnect(ib):
    ib.disconnect()


def get_account_value(ib):
    for item in ib.accountValues():
        if item.tag == "NetLiquidation" and item.currency == "USD":
            return float(item.value)
    raise RuntimeError("Could not retrieve account value from IBKR")


def place_buy(ib, ticker, shares):
    contract = Stock(ticker, "SMART", "USD")
    ib.qualifyContracts(contract)
    order = MarketOrder("BUY", shares)
    order.tif = "GTC"
    order.outsideRth = True
    trade = ib.placeOrder(contract, order)
    ib.sleep(3)
    return trade


def place_sell(ib, ticker, shares):
    contract = Stock(ticker, "SMART", "USD")
    ib.qualifyContracts(contract)
    order = MarketOrder("SELL", shares)
    order.tif = "GTC"
    order.outsideRth = True
    trade = ib.placeOrder(contract, order)
    ib.sleep(3)
    return trade
