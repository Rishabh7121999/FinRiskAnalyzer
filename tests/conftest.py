from app.models.execution_plan import ExecutionPlan


def make_financial_entry(
    normalized_score=0.7,
    assessment="moderate",
    observations=None,
    metrics=None,
    status=None,
):
    entry = {
        "ticker": "TEST.NS",
        "company_name": "Test Co",
        "normalized_score": normalized_score,
        "assessment": assessment,
        "observations": observations or [],
        "metrics": metrics or {},
    }

    if status is not None:
        entry["status"] = status

    return entry


def make_news_entry(
    sentiment_score=0.2,
    overall_sentiment="positive",
    articles=None,
):
    if articles is None:
        articles = [
            {"title": "Test headline", "score": sentiment_score, "published": None}
        ]

    return {
        "company": "Test Co",
        "overall_sentiment": overall_sentiment,
        "sentiment_score": sentiment_score,
        "articles": articles,
    }


def make_research_entry(
    sector="Technology",
    industry="Software",
    revenue_trend="growing",
    target_mean_price=None,
    current_price=None,
    num_analysts=25,
    institutional_holding_pct=0.3,
    key_risks=None,
    key_catalysts=None,
):
    return {
        "ticker": "TEST.NS",
        "company_name": "Test Co",
        "sector": sector,
        "industry": industry,
        "ownership": {
            "insider_holding_pct": 0.1,
            "institutional_holding_pct": institutional_holding_pct,
        },
        "analyst_consensus": {
            "recommendation": "buy",
            "mean_rating": 2.0,
            "num_analysts": num_analysts,
            "target_mean_price": target_mean_price,
            "target_high_price": None,
            "target_low_price": None,
            "current_price": current_price,
        },
        "revenue_trend": {
            "yearly_revenue": {},
            "trend": revenue_trend,
        },
        "qualitative_research": {
            "business_overview": "Test Co builds test software.",
            "competitive_position": "Solid position.",
            "key_risks": key_risks or [],
            "key_catalysts": key_catalysts or [],
        },
    }


def make_execution_plan(**overrides):
    defaults = dict(
        intent="investment_analysis",
        companies=["Test Co"],
        tasks=["financial_analysis", "news_analysis", "research_analysis"],
        parallel_tasks=["financial_analysis", "news_analysis", "research_analysis"],
        requires_financial_analysis=True,
        requires_news_analysis=True,
        requires_research_analysis=True,
        requires_human_review=False,
        requires_market_ranking=False,
        sector=None,
        top_n=None,
        ranking_criterion=None,
        horizon=None,
        user_goal="Evaluate Test Co",
    )
    defaults.update(overrides)
    return ExecutionPlan(**defaults)


def make_base_state(**overrides):
    state = {
        "user_query": "Should I invest in Test Co?",
        "query_understanding": None,
        "execution_plan": make_execution_plan(),
        "companies": ["Test Co"],
        "tickers": ["TEST.NS"],
        "financial_data": {},
        "news_data": [],
        "retrieved_documents": [],
        "financial_analysis": {},
        "news_analysis": {},
        "research_analysis": {},
        "completed_tasks": [],
        "investment_analysis": {},
        "comparison_analysis": {},
        "risk_assessment": {},
        "verification_result": {},
        "governance_result": {},
        "requires_human_review": False,
        "next_action": "",
        "retry_count": 0,
        "max_retries": 2,
        "final_report": "",
        "audit_log": [],
        "current_agent": "",
    }
    state.update(overrides)
    return state
