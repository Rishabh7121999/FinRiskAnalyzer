from langchain_google_genai import ChatGoogleGenerativeAI

from app.agents.investment_analysis_agent import build_verdict

from app.models.comparison_insight import ComparisonInsight

from dotenv import load_dotenv
load_dotenv()

llm = ChatGoogleGenerativeAI(model = "gemini-2.5-flash-lite")


comparison_llm = llm.with_structured_output(
    ComparisonInsight
)


def comparison_analysis_agent(state):

    print(
        "\n[Comparison Agent] "
        "Ranking companies against each other..."
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

    verdicts = [
        build_verdict(
            company,
            ticker,
            financial.get(ticker),
            news.get(company),
            research.get(ticker),
            horizon,
            user_goal,
        )
        for company, ticker in zip(companies, tickers)
    ]

    ranking = sorted(
        verdicts,
        key=lambda verdict: verdict["composite_score"],
        reverse=True,
    )

    for position, verdict in enumerate(ranking, start=1):

        verdict["rank"] = position

    try:

        insight = synthesize_comparison(
            ranking,
            horizon,
            user_goal,
        )

        comparison_status = "ok"

    except Exception as e:

        insight = {

            "overall_verdict":
                (
                    f"{ranking[0]['company']} ranks highest "
                    f"on the combined signal."
                    if ranking
                    else "No companies to compare."
                ),

            "leader_rationale":
                "; ".join(
                    ranking[0]["supporting_points"]
                )
                if ranking
                else "",

            "key_differentiators":
                [],

            "company_notes":
                [],

        }

        comparison_status = f"failed: {e}"

    comparison_analysis = {

        "ranking":
            ranking,

        "leader":
            ranking[0]["company"] if ranking else None,

        "overall_verdict":
            insight["overall_verdict"],

        "leader_rationale":
            insight["leader_rationale"],

        "key_differentiators":
            insight["key_differentiators"],

        "company_notes":
            insight["company_notes"],

        "status":
            "completed",

    }

    return {

        "comparison_analysis":
            comparison_analysis,

        "next_action":
            "generate_report",

        "current_agent":
            "comparison_analysis_agent",

        "audit_log": [
            {
                "agent":
                    "comparison_analysis_agent",

                "action":
                    "companies_ranked",

                "ranking": [
                    verdict["ticker"]
                    for verdict in ranking
                ],

                "synthesis":
                    comparison_status,
            }
        ],

    }


def synthesize_comparison(
    ranking,
    horizon,
    user_goal,
):

    companies_block = "\n\n".join(

        f"{verdict['rank']}. {verdict['company']} "
        f"({verdict['ticker']})\n"
        f"   Recommendation: {verdict['recommendation']} "
        f"(confidence: {verdict['confidence']})\n"
        f"   Composite score: {verdict['composite_score']}\n"
        f"   Volatility (beta): {verdict['quant'].get('beta')}\n"
        f"   Valuation multiples: {verdict['quant'].get('valuation')}\n"
        f"   Thesis: {verdict['thesis']}\n"
        f"   Supporting points: {verdict['supporting_points']}\n"
        f"   Key risks: {verdict['key_risks']}"

        for verdict in ranking
    )

    prompt = f"""
You are the Comparison Analysis agent for an AI
financial intelligence system. You are given the
per-company investment verdicts already produced by the
Investment Analysis agent for {len(ranking)} companies,
ranked highest composite score first. Your job is to
explain the comparison, not to re-score the companies.

Ground every statement ONLY in the data given below. Do
not invent facts, numbers, or events not present or
directly implied by this data.

Investor horizon:
{horizon or "Not specified"}

Investor goal:
{user_goal or "Not specified"}

Companies (ranked):
{companies_block}

Produce:

1. overall_verdict: 2-3 sentences giving a concrete,
comparative recommendation across all the companies
above - not a repeat of any single company's thesis.

2. leader_rationale: 1-2 sentences on specifically why
the top-ranked company leads the others, referencing the
concrete signals that separate it from the rest.

3. key_differentiators: the specific factors that most
separate these companies from each other (e.g. one has
stronger fundamentals, another has better growth
catalysts or lower risk) - not generic statements that
could apply to any comparison.

4. company_notes: one short note per company (using its
exact name as given above) on its specific role in this
comparison, e.g. why it ranked where it did relative to
the others.
"""

    insight = comparison_llm.invoke(
        prompt
    )

    return insight.model_dump()
