import yfinance as yf

def fetch_stock_data(ticker: str):

    stock = yf.Ticker(ticker)

    info = stock.info

    return {
        "current_price": info.get("currentPrice"),
        "market_cap": info.get("marketCap"),
        "trailing_pe": info.get("trailingPE"),
        "revenue_growth": info.get("revenueGrowth"),
        "debt_to_equity": info.get("debtToEquity"),
        "profit_margins": info.get("profitMargins"),
        "sector": info.get("sector")
    }