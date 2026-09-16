import yfinance as yf


def research_agent(state):

    companies = state["companies"]

    tickers = state["tickers"]

    results = []

    print(
        "\n[Research Agent]"
    )


    for company, ticker_symbol in zip(
        companies,
        tickers
    ):

        try:

            ticker = yf.Ticker(
                ticker_symbol
            )

            info = ticker.info


            research = {

                "company":
                    company,

                "ticker":
                    ticker_symbol,

                "business_summary":
                    info.get(
                        "longBusinessSummary"
                    ),

                "sector":
                    info.get(
                        "sector"
                    ),

                "industry":
                    info.get(
                        "industry"
                    ),

                "employees":
                    info.get(
                        "fullTimeEmployees"
                    ),

                "website":
                    info.get(
                        "website"
                    ),

            }


            results.append(
                research
            )


        except Exception as e:

            results.append({

                "company":
                    company,

                "ticker":
                    ticker_symbol,

                "error":
                    str(e),

            })


    return {

        "agent_results": [

            {

                "task":
                    "research_analysis",

                "data":
                    results,

            }

        ]

    }