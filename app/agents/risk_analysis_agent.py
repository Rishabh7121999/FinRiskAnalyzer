from langchain_google_genai import ChatGoogleGenerativeAI

from app.tools.scoring import score_company

from app.models.risk_assessment import RiskAssessment

from dotenv import load_dotenv
load_dotenv()

llm = ChatGoogleGenerativeAI(model = "gemini-2.5-flash-lite")


risk_llm = llm.with_structured_output(
    RiskAssessment
)


def risk_analysis_agent(state):

    print(
        "\n[Risk Agent] "
        "Synthesizing risk assessment..."
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

    assessments = {}

    for company, ticker in zip(companies, tickers):

        assessments[ticker] = build_risk_assessment(
            company,
            ticker,
            financial.get(ticker),
            news.get(company),
            research.get(ticker),
            horizon,
        )

    risk_assessment = {

        "assessments":
            assessments,

        "status":
            "completed",

    }

    return {

        "risk_assessment":
            risk_assessment,

        "audit_log": [
            {
                "agent":
                    "risk_analysis_agent",

                "action":
                    "risk_assessments_generated",

                "risk_levels": {
                    ticker: assessment["risk_level"]
                    for ticker, assessment in assessments.items()
                },

                "synthesis": {
                    ticker: assessment["synthesis_status"]
                    for ticker, assessment in assessments.items()
                },
            }
        ],

    }


def build_risk_assessment(
    company,
    ticker,
    financial_entry,
    news_entry,
    research_entry,
    horizon,
):

    # Reuse the same quant layer investment_analysis_agent
    # uses, so the two agents never disagree about the
    # underlying facts - this agent only re-projects them
    # into a risk-primary lens.

    quant = score_company(
        company,
        ticker,
        financial_entry,
        news_entry,
        research_entry,
    )

    financial_score, financial_drivers, financial_has_data = _score_financial_risk(
        financial_entry
    )

    market_score, market_drivers, market_has_data = _score_market_risk(
        quant
    )

    sentiment_score, sentiment_drivers, sentiment_has_data = _score_sentiment_risk(
        news_entry
    )

    business_score, business_drivers, business_has_data = _score_business_risk(
        quant,
        research_entry,
    )

    dimensions = {

        "financial_risk": {
            "level": _risk_label(financial_score),
            "score": round(financial_score, 3),
            "drivers": financial_drivers,
        },

        "market_risk": {
            "level": _risk_label(market_score),
            "score": round(market_score, 3),
            "drivers": market_drivers,
        },

        "sentiment_risk": {
            "level": _risk_label(sentiment_score),
            "score": round(sentiment_score, 3),
            "drivers": sentiment_drivers,
        },

        "business_risk": {
            "level": _risk_label(business_score),
            "score": round(business_score, 3),
            "drivers": business_drivers,
        },

    }

    weighted_components = [
        (financial_score, 0.35),
        (market_score, 0.25),
        (sentiment_score, 0.15),
        (business_score, 0.25),
    ]

    risk_score = round(
        sum(
            score * weight
            for score, weight in weighted_components
        ),
        3,
    )

    computed_risk_level = _risk_label(
        risk_score
    )

    confidence = _confidence_from_flags([
        financial_has_data,
        market_has_data,
        sentiment_has_data,
        business_has_data,
    ])

    try:

        narrative = synthesize_risk_assessment(
            company,
            ticker,
            quant,
            dimensions,
            computed_risk_level,
            horizon,
        )

        synthesis_status = "ok"

    except Exception as e:

        narrative = {

            "risk_level":
                computed_risk_level,

            "top_risk_factors":
                _fallback_top_risk_factors(dimensions),

            "mitigating_factors":
                quant.get("key_catalysts", []),

            "horizon_note":
                None,

        }

        synthesis_status = f"failed: {e}"

    return {

        "company":
            company,

        "ticker":
            ticker,

        "risk_level":
            narrative["risk_level"],

        "risk_score":
            risk_score,

        "confidence":
            confidence,

        "dimensions":
            dimensions,

        "top_risk_factors":
            narrative["top_risk_factors"],

        "mitigating_factors":
            narrative["mitigating_factors"],

        "horizon_note":
            narrative["horizon_note"],

        "synthesis_status":
            synthesis_status,

        "quant":
            quant,

    }


def synthesize_risk_assessment(
    company,
    ticker,
    quant,
    dimensions,
    computed_risk_level,
    horizon,
):

    prompt = f"""
You are the Risk Analysis agent for an AI financial
intelligence system. Your job is to assess how risky an
investment in {company} ({ticker}) is - independent of
whether the reward justifies it, which is a separate
agent's job. A stock can legitimately be a strong
investment case and still carry high risk; do not soften
the risk level just because the underlying business looks
good.

Ground every statement ONLY in the data given below. Do
not invent facts, numbers, or events that are not present
or directly implied by this data.

Investor horizon:
{horizon or "Not specified"}

Rule-based risk level (already computed): {computed_risk_level}

Risk dimensions (rule-based, for your reference):
- Financial/leverage risk: {dimensions['financial_risk']['level']} - {dimensions['financial_risk']['drivers']}
- Market/volatility risk: {dimensions['market_risk']['level']} - {dimensions['market_risk']['drivers']}
- Sentiment risk: {dimensions['sentiment_risk']['level']} - {dimensions['sentiment_risk']['drivers']}
- Business/structural risk: {dimensions['business_risk']['level']} - {dimensions['business_risk']['drivers']}

Supporting quant signals:
- Key risks already identified: {quant.get('key_risks')}
- Key catalysts already identified: {quant.get('key_catalysts')}
- Beta (volatility, 1.0 = market average): {quant.get('beta')}
- Valuation multiples: {quant.get('valuation')}

Produce a final risk assessment with these fields:

1. risk_level: Low, Moderate, High, or Severe - your own
judgement after reviewing the dimensions above. It may
differ from the rule-based level if the combination of
factors justifies it.

2. top_risk_factors: the most material risk factors,
most severe first, drawn only from the data above.

3. mitigating_factors: factors that offset or reduce the
risk (e.g. strong cash flow despite high beta), drawn
only from the data above. Write each as a natural
sentence explaining why it mitigates risk - do not copy
a label and its raw value verbatim. Empty list if none
apply.

4. horizon_note: one sentence on how the stated horizon
(if any) changes how much this risk matters - e.g. a long
horizon can absorb short-term volatility that a short
horizon cannot. Leave null if no horizon was given.
"""

    assessment = risk_llm.invoke(
        prompt
    )

    return assessment.model_dump()


def _score_financial_risk(financial_entry):

    metrics = (financial_entry or {}).get(
        "metrics",
        {},
    ) or {}

    risk_points = []

    drivers = []

    debt_to_equity = metrics.get("debt_to_equity")

    if debt_to_equity is not None:

        if debt_to_equity > 150:
            risk_points.append(1.0)
            drivers.append("High debt-to-equity ratio")
        elif debt_to_equity > 100:
            risk_points.append(0.6)
            drivers.append("Elevated debt-to-equity ratio")
        elif debt_to_equity > 50:
            risk_points.append(0.3)
        else:
            risk_points.append(0.1)

    current_ratio = metrics.get("current_ratio")

    if current_ratio is not None:

        if current_ratio < 1.0:
            risk_points.append(0.8)
            drivers.append("Weak short-term liquidity")
        elif current_ratio < 1.5:
            risk_points.append(0.4)
        else:
            risk_points.append(0.1)

    interest_coverage = metrics.get("interest_coverage")

    if interest_coverage is not None:

        if interest_coverage < 3:
            risk_points.append(0.8)
            drivers.append("Thin interest coverage")
        elif interest_coverage < 8:
            risk_points.append(0.4)
        else:
            risk_points.append(0.1)

    free_cash_flow = metrics.get("free_cash_flow")

    if free_cash_flow is not None:

        if free_cash_flow < 0:
            risk_points.append(0.9)
            drivers.append("Negative free cash flow")
        else:
            risk_points.append(0.1)

    if not risk_points:
        return 0.5, drivers, False

    score = sum(risk_points) / len(risk_points)

    return score, drivers, True


def _score_market_risk(quant):

    risk_points = []

    drivers = []

    has_data = False

    beta = quant.get("beta")

    if beta is not None:

        has_data = True

        if beta >= 1.5:
            risk_points.append(1.0)
            drivers.append("High volatility (beta well above market)")
        elif beta >= 1.2:
            risk_points.append(0.6)
            drivers.append("Elevated volatility")
        elif beta <= 0.6:
            risk_points.append(0.3)
        else:
            risk_points.append(0.2)

    valuation = quant.get("valuation") or {}

    peg_ratio = valuation.get("peg_ratio")

    pe_ratio = valuation.get("pe_ratio")

    if peg_ratio is not None and peg_ratio > 0:

        has_data = True

        if peg_ratio > 2:
            risk_points.append(0.7)
            drivers.append("Expensive relative to growth (high PEG)")
        elif peg_ratio > 1:
            risk_points.append(0.4)
        else:
            risk_points.append(0.2)

    elif pe_ratio is not None and pe_ratio > 0:

        has_data = True

        if pe_ratio > 40:
            risk_points.append(0.7)
            drivers.append("Richly valued on trailing earnings (high P/E)")
        elif pe_ratio > 25:
            risk_points.append(0.4)
        else:
            risk_points.append(0.2)

    if not risk_points:
        return 0.5, drivers, False

    score = sum(risk_points) / len(risk_points)

    return score, drivers, has_data


def _score_sentiment_risk(news_entry):

    sentiment_score = (news_entry or {}).get("sentiment_score")

    article_count = len(
        (news_entry or {}).get("articles", [])
    )

    if sentiment_score is None or article_count == 0:
        return 0.5, [], False

    drivers = []

    if sentiment_score < -0.3:
        score = 0.8
        drivers.append("Negative news sentiment")
    elif sentiment_score < -0.1:
        score = 0.5
        drivers.append("Mildly negative news sentiment")
    else:
        score = 0.2

    if article_count < 3:
        score = min(score + 0.1, 1.0)
        drivers.append("Thin news coverage limits sentiment confidence")

    return score, drivers, True


def _score_business_risk(quant, research_entry):

    risk_points = []

    drivers = []

    has_data = False

    key_risks = quant.get("key_risks") or []

    if key_risks:

        has_data = True

        severity = min(len(key_risks) / 3, 1.0)

        risk_points.append(0.3 + (0.5 * severity))

        drivers.extend(key_risks)

    ownership = (research_entry or {}).get("ownership") or {}

    institutional_holding_pct = ownership.get("institutional_holding_pct")

    if institutional_holding_pct is not None:

        has_data = True

        if institutional_holding_pct < 0.10:
            risk_points.append(0.6)
            drivers.append("Low institutional ownership conviction")
        else:
            risk_points.append(0.2)

    analyst_consensus = (research_entry or {}).get("analyst_consensus") or {}

    num_analysts = analyst_consensus.get("num_analysts")

    if num_analysts is not None:

        has_data = True

        if num_analysts < 3:
            risk_points.append(0.5)
            drivers.append("Thin analyst coverage")
        else:
            risk_points.append(0.15)

    if not risk_points:
        return 0.5, drivers, False

    score = sum(risk_points) / len(risk_points)

    return score, drivers, has_data


def _risk_label(score):

    if score >= 0.7:
        return "Severe"

    if score >= 0.5:
        return "High"

    if score >= 0.3:
        return "Moderate"

    return "Low"


def _confidence_from_flags(has_data_flags):

    ratio = sum(has_data_flags) / len(has_data_flags)

    if ratio >= 0.9:
        return "high"

    if ratio >= 0.5:
        return "medium"

    return "low"


def _fallback_top_risk_factors(dimensions):

    ordered = sorted(
        dimensions.values(),
        key = lambda dimension: dimension["score"],
        reverse = True,
    )

    factors = []

    for dimension in ordered:
        factors.extend(dimension["drivers"])

    return factors
