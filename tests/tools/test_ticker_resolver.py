from unittest.mock import MagicMock, patch

from app.tools.ticker_resolver import resolve_ticker


def _mock_search(quotes):
    search = MagicMock()
    search.quotes = quotes
    return search


def test_resolve_ticker_prefers_nse_listing():
    quotes = [
        {"symbol": "RELI", "shortname": "Reliance Inc", "exchange": "NYQ"},
        {"symbol": "RELIANCE.NS", "shortname": "Reliance Industries", "exchange": "NSI"},
    ]

    with patch("app.tools.ticker_resolver.yf.Search", return_value=_mock_search(quotes)):
        result = resolve_ticker("Reliance Industries")

    assert result == {"ticker": "RELIANCE.NS", "company": "Reliance Industries"}


def test_resolve_ticker_falls_back_to_first_quote_when_no_nse_listing():
    quotes = [
        {"symbol": "AAPL", "shortname": "Apple Inc", "exchange": "NMS"},
    ]

    with patch("app.tools.ticker_resolver.yf.Search", return_value=_mock_search(quotes)):
        result = resolve_ticker("Apple")

    assert result == {"ticker": "AAPL", "company": "Apple Inc"}


def test_resolve_ticker_returns_none_when_no_quotes():
    with patch("app.tools.ticker_resolver.yf.Search", return_value=_mock_search([])):
        result = resolve_ticker("Nonexistent Company")

    assert result is None
