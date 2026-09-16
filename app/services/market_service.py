import yfinance as yf


def get_company_data(ticker_symbol: str):

    try:

        ticker = yf.Ticker(ticker_symbol)

        info = ticker.info

        return {

            "ticker": ticker_symbol,

            "company_name": info.get(
                "longName"
            ),

            "sector": info.get(
                "sector"
            ),

            "industry": info.get(
                "industry"
            ),

            "current_price": info.get(
                "currentPrice"
            ),

            "market_cap": info.get(
                "marketCap"
            ),

            "pe_ratio": info.get(
                "trailingPE"
            ),

            "pb_ratio": info.get(
                "priceToBook"
            ),

            "roe": info.get(
                "returnOnEquity"
            ),

            "profit_margin": info.get(
                "profitMargins"
            ),

            "debt_to_equity": info.get(
                "debtToEquity"
            ),

            "total_revenue": info.get(
                "totalRevenue"
            ),

            "revenue_growth": info.get(
                "revenueGrowth"
            ),

            "earnings_growth": info.get(
                "earningsGrowth"
            ),

            "total_debt": info.get(
                "totalDebt"
            ),

            "total_cash": info.get(
                "totalCash"
            ),

        }

    except Exception as e:

        return {

            "ticker": ticker_symbol,

            "error": str(e),

        }


def get_financial_statements(
    ticker_symbol: str
):

    try:

        ticker = yf.Ticker(
            ticker_symbol
        )

        income_statement = (
            ticker.financials
        )

        balance_sheet = (
            ticker.balance_sheet
        )

        cash_flow = (
            ticker.cashflow
        )

        return {

            "income_statement":
                income_statement.to_dict(),

            "balance_sheet":
                balance_sheet.to_dict(),

            "cash_flow":
                cash_flow.to_dict(),

        }

    except Exception as e:

        return {

            "error": str(e)

        }