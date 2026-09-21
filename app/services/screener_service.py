import functools
import io

import pandas as pd
import requests

from app.services.market_service import get_company_data


# ============================================================
# SECTOR -> NSE INDEX CONSTITUENT LIST
# ============================================================
# NSE's index arm (niftyindices.com) publishes each sectoral
# index's constituent list as a small, stable, public CSV - no
# auth or session cookies, unlike nseindia.com's unofficial
# JSON API. Free-text sector strings from QueryUnderstanding
# map to one of these index files.

_INDEX_CSV_URL = (
    "https://niftyindices.com/IndexConstituent/{filename}.csv"
)

SECTOR_INDEX_MAP: dict[str, str] = {

    "bank": "ind_niftybanklist",
    "banks": "ind_niftybanklist",
    "banking": "ind_niftybanklist",

    "private bank": "ind_nifty_privatebanklist",
    "private banks": "ind_nifty_privatebanklist",

    "psu bank": "ind_niftypsubanklist",
    "psu banks": "ind_niftypsubanklist",
    "public sector bank": "ind_niftypsubanklist",

    "financial services": "ind_niftyfinancelist",
    "financials": "ind_niftyfinancelist",

    "it": "ind_niftyitlist",
    "information technology": "ind_niftyitlist",
    "tech": "ind_niftyitlist",
    "technology": "ind_niftyitlist",

    "auto": "ind_niftyautolist",
    "automobile": "ind_niftyautolist",
    "automobiles": "ind_niftyautolist",

    "pharma": "ind_niftypharmalist",
    "pharmaceutical": "ind_niftypharmalist",
    "pharmaceuticals": "ind_niftypharmalist",
    "healthcare": "ind_niftypharmalist",

    "fmcg": "ind_niftyfmcglist",
    "consumer goods": "ind_niftyfmcglist",

    "metal": "ind_niftymetallist",
    "metals": "ind_niftymetallist",
    "mining": "ind_niftymetallist",

    "energy": "ind_niftyenergylist",
    "oil and gas": "ind_niftyenergylist",
    "oil & gas": "ind_niftyenergylist",

    "realty": "ind_niftyrealtylist",
    "real estate": "ind_niftyrealtylist",

    "media": "ind_niftymedialist",

}

# Fallback "whole market" universe for market_ranking queries
# with no sector ("top 5 stocks by market cap") - NIFTY 500 is
# used as the broad-market proxy, capped below before the
# per-ticker yfinance loop so an unscoped ranking doesn't fan
# out to 500 individual yfinance calls.
_MARKET_WIDE_FILENAME = "ind_nifty500list"

_MARKET_WIDE_SAMPLE_SIZE = 50

_REQUEST_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0 Safari/537.36"
    ),
}


@functools.lru_cache(maxsize=32)
def _fetch_index_csv(filename: str) -> tuple[tuple[str, str], ...]:

    url = _INDEX_CSV_URL.format(
        filename=filename,
    )

    response = requests.get(
        url,
        headers=_REQUEST_HEADERS,
        timeout=10,
    )

    response.raise_for_status()

    frame = pd.read_csv(
        io.StringIO(response.text)
    )

    return tuple(
        (row["Company Name"], f"{row['Symbol']}.NS")
        for _, row in frame.iterrows()
    )


def fetch_sector_constituents(
    sector: str | None,
) -> list[dict]:

    if sector:

        filename = SECTOR_INDEX_MAP.get(
            sector.strip().lower()
        )

        if filename is None:
            return []

    else:

        filename = _MARKET_WIDE_FILENAME

    try:

        constituents = _fetch_index_csv(
            filename
        )

    except Exception:
        return []

    pairs = [
        {
            "company_name": company_name,
            "ticker": ticker,
        }
        for company_name, ticker in constituents
    ]

    if filename == _MARKET_WIDE_FILENAME:
        pairs = pairs[:_MARKET_WIDE_SAMPLE_SIZE]

    return pairs


# ============================================================
# RANKING
# ============================================================
# criterion alias -> (market_service field, higher_is_better)

_CRITERION_FIELD_MAP: dict[str, tuple[str, bool]] = {

    "market cap": ("market_cap", True),
    "market capitalization": ("market_cap", True),
    "marketcap": ("market_cap", True),

    "pe": ("pe_ratio", False),
    "pe ratio": ("pe_ratio", False),
    "p/e": ("pe_ratio", False),
    "valuation": ("pe_ratio", False),

    "revenue growth": ("revenue_growth", True),
    "growth": ("revenue_growth", True),

    "profit margin": ("profit_margin", True),
    "profitability": ("profit_margin", True),

    "dividend yield": ("dividend_yield", True),
    "dividend": ("dividend_yield", True),

}

_DEFAULT_CRITERION_FIELD = (
    "market_cap",
    True,
)


def rank_by_criterion(
    constituents: list[dict],
    ranking_criterion: str | None,
    top_n: int,
) -> list[dict]:

    field, higher_is_better = _CRITERION_FIELD_MAP.get(
        (ranking_criterion or "").strip().lower(),
        _DEFAULT_CRITERION_FIELD,
    )

    scored = []

    for entry in constituents:

        data = get_company_data(
            entry["ticker"]
        )

        value = data.get(field)

        if value is None:
            continue

        scored.append(
            {
                "company_name": entry["company_name"],
                "ticker": entry["ticker"],
                "criterion": field,
                "value": value,
            }
        )

    ranked = sorted(
        scored,
        key=lambda item: item["value"],
        reverse=higher_is_better,
    )

    return ranked[:top_n]
