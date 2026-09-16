# For now:

# mocked sentiment
# later we replace with NewsAPI + FinBERT

def sentiment_analysis_agent(state):

    state["current_agent"] = "sentiment_analysis_agent"

    ticker = state["ticker"]

    # Mock sentiment for MVP
    sentiment = f"""
    Market sentiment around {ticker} is moderately positive.

    Analysts indicate cautious optimism due to
    stable sector performance and earnings growth.
    """

    state["sentiment_analysis"] = sentiment

    state["audit_log"].append({
        "agent": "sentiment_analysis_agent",
        "action": "Completed sentiment analysis"
    })

    state["next_action"] = "risk_scoring"

    return state