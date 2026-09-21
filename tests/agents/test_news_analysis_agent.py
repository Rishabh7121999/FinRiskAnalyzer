from unittest.mock import patch

from app.agents.news_analysis_agent import news_analysis_agent


def test_positive_headlines_produce_positive_sentiment():
    state = {"companies": ["Test Co"]}

    articles = [
        {"title": "Test Co posts record profits and strong growth", "published": "d1"},
        {"title": "Analysts raise price target on Test Co after great results", "published": "d2"},
    ]

    with patch(
        "app.agents.news_analysis_agent.get_company_news",
        return_value=articles,
    ):
        result = news_analysis_agent(state)

    analysis = result["news_analysis"]["Test Co"]

    assert analysis["overall_sentiment"] == "positive"
    assert analysis["sentiment_score"] > 0.15
    assert len(analysis["articles"]) == 2
    assert result["completed_tasks"] == ["news_analysis"]


def test_negative_headlines_produce_negative_sentiment():
    state = {"companies": ["Test Co"]}

    articles = [
        {"title": "Test Co shares crash after massive fraud scandal", "published": "d1"},
    ]

    with patch(
        "app.agents.news_analysis_agent.get_company_news",
        return_value=articles,
    ):
        result = news_analysis_agent(state)

    analysis = result["news_analysis"]["Test Co"]

    assert analysis["overall_sentiment"] == "negative"
    assert analysis["sentiment_score"] < -0.15


def test_no_articles_produces_neutral_sentiment():
    state = {"companies": ["Test Co"]}

    with patch(
        "app.agents.news_analysis_agent.get_company_news",
        return_value=[],
    ):
        result = news_analysis_agent(state)

    analysis = result["news_analysis"]["Test Co"]

    assert analysis["overall_sentiment"] == "neutral"
    assert analysis["sentiment_score"] == 0
    assert analysis["articles"] == []


def test_processes_every_company_in_state():
    state = {"companies": ["Test Co", "Other Co"]}

    with patch(
        "app.agents.news_analysis_agent.get_company_news",
        return_value=[],
    ):
        result = news_analysis_agent(state)

    assert set(result["news_analysis"].keys()) == {"Test Co", "Other Co"}
