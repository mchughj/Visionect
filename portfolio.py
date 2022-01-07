import yfinance as yf
import numpy as np
import time

try:
    import equities
    stocks = equities.stocks
except:
    print ("""
WARNING:  No equities.py file found.  Create this file (using the one shown in portfolio as a template) and capture all your equities (stock, etf, mutual fund, whatever) quantities, cost basis, etc.  

For now just using a dummy value!!
""")
    stocks = {
            'AMZN': { 
                'quantity': 30,
                'oPrice': 262.32,
                },
            'FB': {
                'quantity': 3000,
                'oPrice': 165.78,
                },
            }
    
# If the last close value is NaN then this is a security
# which doesn't have intraday value changes.  In that case
# the prior day's open and close value will be one and the same.
# So we look back 2 days for the close value.
def getPriorLastCloseValue(values):
    if np.isnan(values[-1]):
        if len(values) == 2:
            return values[-2]
        else:
            return values[-3]
    else:
        return values[-2]


def getLastCloseValue(values):
    if np.isnan(values[-1]):
        return values[-2]
    else:
        return values[-1]

cachedResult = None
cacheSeconds = 60
cachedResultTime = 0

def getPortfolio():
    global cachedResultTime, cachedResult

    if cachedResultTime != 0 and time.time() - cachedResultTime < cacheSeconds:
        return cachedResult

    cachedResult = dict()

    tickerSymbols = " ".join(stocks.keys())
    yfData = yf.download(tickerSymbols, group_by = 'ticker', interval = "1d", start="2022-01-01", end="2022-12-31")
    d = {idx: gp.xs(idx, level=0, axis=1) for idx, gp in yfData.groupby(level=0, axis=1)}

    for s in stocks.keys():

        openPrice = getPriorLastCloseValue(d[s]['Close'])
        closePrice = getLastCloseValue(d[s]['Close'])
        yearOpenPrice = d[s]['Open'].values[0]
        costBasis = stocks[s]['oPrice']
        value = stocks[s]['quantity'] * closePrice

        e = dict()
        e["ticker"] = s
        e["open"] = openPrice
        e["sopen"] = "${:,.2f}".format(openPrice)
        e["close"] = closePrice
        e["sclose"] = "${:,.2f}".format(closePrice)
        e["value"] = value
        e["svalue"] = "${:,.2f}".format(value)
        e["change"] = closePrice - openPrice
        e["pchange"] = (e["change"] / openPrice) * 100
        e["spchange"] = "{:0.2f}%".format(e["pchange"])
        e["costbasis"] = costBasis
        e["scostbasis"] = "${:,.2f}".format(costBasis)
        e["alltimepchange"] = ((closePrice - costBasis) / costBasis ) * 100
        e["salltimepchange"] = "{:0.2f}%".format(e["alltimepchange"])
        e["yearpchange"] = ((closePrice - yearOpenPrice) / yearOpenPrice ) * 100
        e["syearpchange"] = "{:0.2f}%".format(e["yearpchange"])

        print(f"{s} - open: {e['open']}, close: {e['sclose']}, change: {e['change']}, pchange: {e['spchange']}, costBasis: {e['scostbasis']}, alltimepchange: {e['salltimepchange']}, yearpchange: {e['syearpchange']}.")

        cachedResult[s] = e

    cachedResultTime = time.time()
    return cachedResult


