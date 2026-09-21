from datetime import datetime, timezone

import yfinance as yf

from langchain_google_genai import ChatGoogleGenerativeAI

from app.models.research_insight import ResearchInsight

from dotenv import load_dotenv
load_dotenv()

llm = ChatGoogleGenerativeAI(model = "gemini-2.5-flash-lite")


research_llm = llm.with_structured_output(
    ResearchInsight
)


def research_analysis_agent(state):

    tickers = state["tickers"]

    results = {}

    print("\n[Research Agent]")

    for ticker_symbol in tickers:

        print(
            f"Researching {ticker_symbol}"
        )

        try:

            results[ticker_symbol] = _research_ticker(
                ticker_symbol
            )

        except Exception as e:

            results[ticker_symbol] = {

                "ticker":
                    ticker_symbol,

                "error":
                    str(e),

                "retrieved_at":
                    _now(),

            }

    return {

        "research_analysis": results,

        "completed_tasks": [
            "research_analysis"
        ],

    }


def _research_ticker(ticker_symbol: str) -> dict:

    ticker = yf.Ticker(
        ticker_symbol
    )

    info = ticker.info

    business_summary = info.get(
        "longBusinessSummary"
    )

    ownership = {

        "insider_holding_pct":
            info.get(
                "heldPercentInsiders"
            ),

        "institutional_holding_pct":
            info.get(
                "heldPercentInstitutions"
            ),

    }

    analyst_consensus = {

        "recommendation":
            info.get(
                "recommendationKey"
            ),

        "mean_rating":
            info.get(
                "recommendationMean"
            ),

        "num_analysts":
            info.get(
                "numberOfAnalystOpinions"
            ),

        "target_mean_price":
            info.get(
                "targetMeanPrice"
            ),

        "target_high_price":
            info.get(
                "targetHighPrice"
            ),

        "target_low_price":
            info.get(
                "targetLowPrice"
            ),

        "current_price":
            info.get(
                "currentPrice"
            ),

    }

    revenue_trend = _extract_revenue_trend(
        ticker.financials.to_dict()
    )

    result = {

        "ticker":
            ticker_symbol,

        "company_name":
            info.get(
                "longName",
                ticker_symbol
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

        "fifty_two_week_low":
            info.get(
                "fiftyTwoWeekLow"
            ),

        "fifty_two_week_high":
            info.get(
                "fiftyTwoWeekHigh"
            ),

        "dividend_yield":
            info.get(
                "dividendYield"
            ),

        "ownership":
            ownership,

        "analyst_consensus":
            analyst_consensus,

        "revenue_trend":
            revenue_trend,

        "qualitative_research":
            _generate_qualitative_research(
                company_name = info.get(
                    "longName",
                    ticker_symbol
                ),
                sector = info.get(
                    "sector"
                ),
                industry = info.get(
                    "industry"
                ),
                business_summary = business_summary,
                ownership = ownership,
                analyst_consensus = analyst_consensus,
                revenue_trend = revenue_trend,
            ),

        "retrieved_at":
            _now(),

        "source":
            "yfinance",

    }

    return result


def _extract_revenue_trend(income_statement: dict) -> dict:

    revenue_by_year = {}

    for period, rows in income_statement.items():

        revenue = rows.get(
            "Total Revenue"
        )

        if revenue is None or revenue != revenue:
            continue

        year = str(period)[:4]

        revenue_by_year[year] = revenue

    years = sorted(
        revenue_by_year
    )

    if len(years) < 2:

        return {

            "yearly_revenue":
                revenue_by_year,

            "trend":
                "insufficient_data",

        }

    values = [
        revenue_by_year[year]
        for year in years
    ]

    if all(
        b > a
        for a, b in zip(values, values[1:])
    ):
        trend = "growing"

    elif all(
        b < a
        for a, b in zip(values, values[1:])
    ):
        trend = "declining"

    else:
        trend = "volatile"

    return {

        "yearly_revenue":
            revenue_by_year,

        "trend":
            trend,

    }


def _generate_qualitative_research(
    company_name,
    sector,
    industry,
    business_summary,
    ownership,
    analyst_consensus,
    revenue_trend,
):

    if not business_summary:

        return None

    prompt = f"""
You are the Research Analysis agent for an AI
financial intelligence system. Your job is to
produce qualitative, structural research context
that complements (not repeats) quantitative
financial ratios and short-term news sentiment,
which other agents already cover.

Ground every statement ONLY in the data given
below. Do not invent facts, numbers, or events
that are not present or directly implied by this
data. If the data is insufficient to say something
with confidence, say so explicitly instead of
guessing.

Company:
{company_name}

Sector:
{sector}

Industry:
{industry}

Business summary:
{business_summary}

Ownership signals:
{ownership}

Analyst consensus:
{analyst_consensus}

Multi-year revenue trend:
{revenue_trend}

Produce:

1. business_overview: a concise (2-3 sentence)
plain-language summary of what the company does
and how it makes money.

2. competitive_position: an assessment of its
competitive position/moat, informed by the sector,
industry, and any scale/ownership signals given.

3. key_risks: structural or strategic risks
suggested by the data (e.g. weak ownership
conviction, declining revenue trend, thin analyst
coverage). Do not repeat generic market risk
disclaimers.

4. key_catalysts: structural or strategic factors
that could support the business going forward,
suggested by the data given.
"""

    insight = research_llm.invoke(
        prompt
    )

    return insight.model_dump()


def _now() -> str:

    return datetime.now(
        timezone.utc
    ).isoformat()
