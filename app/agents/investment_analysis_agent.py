from langchain_google_genai import ChatGoogleGenerativeAI

from app.tools.scoring import score_company

from app.models.investment_verdict import InvestmentVerdict

from dotenv import load_dotenv
load_dotenv()

llm = ChatGoogleGenerativeAI(model = "gemini-2.5-flash-lite")


verdict_llm = llm.with_structured_output(
    InvestmentVerdict
)


def investment_analysis_agent(state):

    print(
        "\n[Investment Agent] "
        "Synthesizing specialist analyses..."
    )

    companies = state["companies"]

    tickers = state["tickers"]

    financial = state.get(
        "financial_analysis",
        {}
    )

    news = state.get(
        "news_analysis",
        {}
    )

    research = state.get(
        "research_analysis",
        {}
    )

    execution_plan = state.get(
        "execution_plan"
    )

    horizon = getattr(
        execution_plan,
        "horizon",
        None,
    )

    user_goal = getattr(
        execution_plan,
        "user_goal",
        None,
    )

    verdicts = {}

    for company, ticker in zip(companies, tickers):

        verdicts[ticker] = build_verdict(
            company,
            ticker,
            financial.get(ticker),
            news.get(company),
            research.get(ticker),
            horizon,
            user_goal,
        )

    investment_analysis = {

        "verdicts":
            verdicts,

        "status":
            "completed",

    }

    return {

        "investment_analysis":
            investment_analysis,

        "audit_log": [
            {
                "agent":
                    "investment_analysis_agent",

                "action":
                    "investment_verdicts_generated",

                "recommendations": {
                    ticker: verdict["recommendation"]
                    for ticker, verdict in verdicts.items()
                },

                "synthesis": {
                    ticker: verdict["synthesis_status"]
                    for ticker, verdict in verdicts.items()
                },
            }
        ],

    }


def build_verdict(
    company,
    ticker,
    financial_entry,
    news_entry,
    research_entry,
    horizon,
    user_goal,
):

    quant = score_company(
        company,
        ticker,
        financial_entry,
        news_entry,
        research_entry,
    )

    try:

        narrative = synthesize_investment_verdict(
            company,
            ticker,
            quant,
            research_entry,
            horizon,
            user_goal,
        )

        synthesis_status = "ok"

    except Exception as e:

        narrative = {

            "recommendation":
                quant["recommendation"],

            "confidence":
                _confidence_bucket(quant["confidence"]),

            "thesis":
                "; ".join(quant["rationale"]),

            "supporting_points":
                quant["rationale"],

            "conflicting_signals":
                [],

            "key_risks":
                quant.get("key_risks", []),

            "horizon_note":
                None,

        }

        synthesis_status = f"failed: {e}"

    return {

        "company":
            company,

        "ticker":
            ticker,

        "recommendation":
            narrative["recommendation"],

        "confidence":
            narrative["confidence"],

        "thesis":
            narrative["thesis"],

        "supporting_points":
            narrative["supporting_points"],

        "conflicting_signals":
            narrative["conflicting_signals"],

        "key_risks":
            narrative["key_risks"],

        "horizon_note":
            narrative["horizon_note"],

        "composite_score":
            quant["composite_score"],

        "synthesis_status":
            synthesis_status,

        "quant":
            quant,

    }


def synthesize_investment_verdict(
    company,
    ticker,
    quant,
    research_entry,
    horizon,
    user_goal,
):

    qualitative_research = (
        research_entry.get("qualitative_research")
        if research_entry
        else None
    ) or {}

    prompt = f"""
You are the Investment Analysis agent for an AI
financial intelligence system. Your job is to produce
a final Buy/Hold/Avoid verdict for {company} ({ticker})
by reconciling the quantitative and qualitative signals
already produced by other agents in this system.

Ground every statement ONLY in the data given below. Do
not invent facts, numbers, or events that are not
present or directly implied by this data. If two
signals point in different directions, say so
explicitly in conflicting_signals and explain how you
weighed them, rather than silently picking one.

Investor horizon:
{horizon or "Not specified"}

Investor goal:
{user_goal or "Not specified"}

Quantitative signal (rule-based, already computed):
- Rule-based recommendation: {quant['recommendation']}
- Composite score (0-1, higher is better): {quant['composite_score']}
- Confidence: {quant['confidence']}
- Financial assessment: {quant['financial_assessment']}
- News sentiment: {quant['news_sentiment']}
- Revenue trend: {quant.get('revenue_trend')}
- Analyst target price upside/downside: {quant.get('analyst_upside_pct')}%
- Volatility (beta, 1.0 = market average): {quant.get('beta')}
- Valuation multiples: {quant.get('valuation')}
- Rationale points: {quant['rationale']}

Qualitative research:
- Business overview: {qualitative_research.get('business_overview')}
- Competitive position: {qualitative_research.get('competitive_position')}
- Key risks: {qualitative_research.get('key_risks')}
- Key catalysts: {qualitative_research.get('key_catalysts')}

Produce a final verdict with these fields:

1. recommendation: Buy, Hold, or Avoid - your own
judgement after reconciling all signals above. It may
differ from the rule-based recommendation if the
qualitative signals justify it, but explain why in
conflicting_signals if it does.

2. confidence: low, medium, or high.

3. thesis: 2-3 sentences directly answering whether the
investor should invest, tailored to their stated
horizon and goal if given.

4. supporting_points: the strongest points in favour of
your recommendation.

5. conflicting_signals: any signals that pointed in a
different direction than your final recommendation, and
a one-line note on why you weighed it the way you did.
Empty list if nothing conflicted.

6. key_risks: the most important risks to this thesis,
drawn from the data above. If beta indicates high
volatility, consider whether it belongs here given the
investor's horizon (short horizon + high beta is riskier
than long horizon + high beta).

7. horizon_note: one sentence on how the stated horizon
(if any) affected your judgement - e.g. a long horizon
can absorb short-term volatility or a "declining" revenue
trend that a short horizon cannot. Leave null if no
horizon was given.
"""

    verdict = verdict_llm.invoke(
        prompt
    )

    return verdict.model_dump()


def _confidence_bucket(confidence_score):

    if confidence_score >= 0.7:
        return "high"

    if confidence_score >= 0.4:
        return "medium"

    return "low"
