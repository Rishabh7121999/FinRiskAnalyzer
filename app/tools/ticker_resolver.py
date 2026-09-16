import yfinance as yf

def resolve_ticker(company_query: str):

    search = yf.Search(company_query)

    quotes = search.quotes

    if not quotes:
        return None

    for quote in quotes:

        exchange = quote.get("exchange", "")

        # Prefer NSE stocks
        if "NSI" in exchange or "NSE" in exchange:

            return {
                "ticker": quote.get("symbol"),
                "company": quote.get("shortname")
            }

    # fallback
    first = quotes[0]

    return {
        "ticker": first.get("symbol"),
        "company": first.get("shortname")
    }