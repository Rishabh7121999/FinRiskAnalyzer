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

            "forward_pe": info.get(
                "forwardPE"
            ),

            "peg_ratio": info.get(
                "pegRatio"
            ),

            "ev_to_ebitda": info.get(
                "enterpriseToEbitda"
            ),

            "dividend_yield": info.get(
                "dividendYield"
            ),

            "operating_margin": info.get(
                "operatingMargins"
            ),

            "gross_margin": info.get(
                "grossMargins"
            ),

            "roa": info.get(
                "returnOnAssets"
            ),

            "current_ratio": info.get(
                "currentRatio"
            ),

            "quick_ratio": info.get(
                "quickRatio"
            ),

            "free_cash_flow": info.get(
                "freeCashflow"
            ),

            "operating_cash_flow": info.get(
                "operatingCashflow"
            ),

            "beta": info.get(
                "beta"
            ),

        }

    except Exception as e:

        return {

            "ticker": ticker_symbol,

            "error": str(e),

        }


def get_growth_and_coverage(ticker_symbol: str):

    try:

        income_statement = yf.Ticker(
            ticker_symbol
        ).financials

        return {

            "revenue_cagr":
                _calculate_cagr(
                    income_statement,
                    "Total Revenue",
                ),

            "net_income_cagr":
                _calculate_cagr(
                    income_statement,
                    "Net Income",
                ),

            "interest_coverage":
                _calculate_interest_coverage(
                    income_statement
                ),

        }

    except Exception:

        return {

            "revenue_cagr": None,

            "net_income_cagr": None,

            "interest_coverage": None,

        }


def _calculate_cagr(income_statement, row_label):

    if row_label not in income_statement.index:
        return None

    row = income_statement.loc[row_label].dropna()

    if len(row) < 2:
        return None

    periods = sorted(row.index)

    start_value = row[periods[0]]

    end_value = row[periods[-1]]

    years = len(periods) - 1

    if not start_value or start_value <= 0 or years <= 0:
        return None

    cagr = (
        (float(end_value) / float(start_value)) ** (1 / years)
    ) - 1

    return round(cagr, 4)


def _latest_row_value(income_statement, candidate_labels):

    for label in candidate_labels:

        if label not in income_statement.index:
            continue

        row = income_statement.loc[label].dropna()

        if len(row) == 0:
            continue

        latest_period = sorted(row.index)[-1]

        return row[latest_period]

    return None


def _calculate_interest_coverage(income_statement):

    ebit = _latest_row_value(
        income_statement,
        ["Operating Income", "EBIT"],
    )

    interest_expense = _latest_row_value(
        income_statement,
        ["Interest Expense", "Interest Expense Non Operating"],
    )

    if not ebit or not interest_expense:
        return None

    return round(
        float(ebit) / abs(float(interest_expense)),
        2,
    )


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