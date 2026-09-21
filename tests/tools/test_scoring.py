from app.tools.scoring import score_company

from tests.conftest import (
    make_financial_entry,
    make_news_entry,
    make_research_entry,
)


def test_full_data_strong_signals_recommends_buy():
    result = score_company(
        "Test Co",
        "TEST.NS",
        make_financial_entry(normalized_score=0.9),
        make_news_entry(sentiment_score=0.5, articles=[{"title": "x"}] * 5),
        make_research_entry(
            revenue_trend="growing",
            target_mean_price=120,
            current_price=100,
        ),
    )

    assert result["recommendation"] == "Buy"
    assert result["composite_score"] > 0.65
    assert result["confidence"] == 1.0


def test_missing_everything_falls_back_to_neutral_with_reduced_confidence():
    result = score_company(
        "Test Co",
        "TEST.NS",
        None,
        None,
        None,
    )

    assert result["composite_score"] == 0.5
    assert result["recommendation"] == "Hold"
    # -0.3 (no financial) -0.2 (no news) -0.1 (no sector)
    assert result["confidence"] == 0.4


def test_failed_financial_status_is_treated_as_absent():
    failed = score_company(
        "Test Co",
        "TEST.NS",
        make_financial_entry(normalized_score=0.9, status="failed"),
        None,
        None,
    )

    absent = score_company(
        "Test Co",
        "TEST.NS",
        None,
        None,
        None,
    )

    assert failed["composite_score"] == absent["composite_score"]
    assert failed["financial_assessment"] == "unknown"


def test_zero_articles_is_treated_as_no_news_signal():
    result = score_company(
        "Test Co",
        "TEST.NS",
        make_financial_entry(normalized_score=0.9),
        make_news_entry(sentiment_score=0.9, articles=[]),
        None,
    )

    # news_norm falls back to 0.5 because article_count == 0
    only_financial = score_company(
        "Test Co",
        "TEST.NS",
        make_financial_entry(normalized_score=0.9),
        None,
        None,
    )

    assert result["composite_score"] == only_financial["composite_score"]


def test_weak_signals_with_declining_trend_and_downside_recommends_avoid():
    result = score_company(
        "Test Co",
        "TEST.NS",
        make_financial_entry(normalized_score=0.1),
        make_news_entry(sentiment_score=-0.8, articles=[{"title": "x"}] * 3),
        make_research_entry(
            revenue_trend="declining",
            target_mean_price=80,
            current_price=100,
        ),
    )

    assert result["recommendation"] == "Avoid"
    assert result["composite_score"] < 0.45


def test_composite_score_buy_boundary_is_inclusive():
    result = score_company(
        "Test Co",
        "TEST.NS",
        make_financial_entry(normalized_score=0.75),
        None,
        None,
    )

    assert result["composite_score"] == 0.65
    assert result["recommendation"] == "Buy"


def test_composite_score_hold_boundary_is_inclusive():
    result = score_company(
        "Test Co",
        "TEST.NS",
        make_financial_entry(normalized_score=0.75),
        make_news_entry(sentiment_score=-1.0, articles=[{"title": "x"}]),
        None,
    )

    assert result["composite_score"] == 0.45
    assert result["recommendation"] == "Hold"


def test_composite_score_just_below_hold_boundary_recommends_avoid():
    result = score_company(
        "Test Co",
        "TEST.NS",
        make_financial_entry(normalized_score=0.7),
        make_news_entry(sentiment_score=-1.0, articles=[{"title": "x"}]),
        None,
    )

    assert result["composite_score"] < 0.45
    assert result["recommendation"] == "Avoid"


def test_analyst_upside_and_downside_nudge_the_score():
    base = score_company(
        "Test Co",
        "TEST.NS",
        make_financial_entry(normalized_score=0.7),
        None,
        make_research_entry(revenue_trend=None),
    )

    upside = score_company(
        "Test Co",
        "TEST.NS",
        make_financial_entry(normalized_score=0.7),
        None,
        make_research_entry(
            revenue_trend=None,
            target_mean_price=120,
            current_price=100,
        ),
    )

    downside = score_company(
        "Test Co",
        "TEST.NS",
        make_financial_entry(normalized_score=0.7),
        None,
        make_research_entry(
            revenue_trend=None,
            target_mean_price=80,
            current_price=100,
        ),
    )

    assert upside["composite_score"] > base["composite_score"]
    assert downside["composite_score"] < base["composite_score"]
    assert upside["analyst_upside_pct"] == 20.0
    assert downside["analyst_upside_pct"] == -20.0


def test_rationale_includes_observations_sector_and_beta():
    result = score_company(
        "Test Co",
        "TEST.NS",
        make_financial_entry(
            normalized_score=0.7,
            assessment="strong",
            observations=["Great margins"],
            metrics={"beta": 1.6},
        ),
        make_news_entry(),
        make_research_entry(sector="Technology", industry="Software"),
    )

    rationale = " ".join(result["rationale"])

    assert "Great margins" in rationale
    assert "Technology" in rationale
    assert "high" in rationale  # beta 1.6 -> high volatility label
    assert result["beta"] == 1.6


def test_rationale_notes_missing_financial_and_news_data():
    result = score_company(
        "Test Co",
        "TEST.NS",
        None,
        None,
        None,
    )

    rationale = " ".join(result["rationale"])

    assert "Financial data unavailable" in rationale
    assert "No recent news coverage" in rationale
