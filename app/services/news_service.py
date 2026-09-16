import feedparser

from urllib.parse import quote


def get_company_news(
    company: str,
    limit: int = 10
):

    query = quote(
        f"{company} stock India"
    )

    url = (
        "https://news.google.com/rss/search?"
        f"q={query}"
        "&hl=en-IN"
        "&gl=IN"
        "&ceid=IN:en"
    )

    feed = feedparser.parse(
        url
    )

    articles = []

    for entry in feed.entries[:limit]:

        articles.append({

            "title":
                entry.get("title"),

            "link":
                entry.get("link"),

            "published":
                entry.get("published"),

        })

    return articles