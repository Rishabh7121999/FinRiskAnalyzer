from vaderSentiment.vaderSentiment import (
    SentimentIntensityAnalyzer
)

from app.services.news_service import (
    get_company_news
)


def news_agent(state):

    analyzer = (
        SentimentIntensityAnalyzer()
    )

    companies = state["companies"]

    results = []

    print(
        "\n[News Agent]"
    )

    for company in companies:

        print(
            f"Fetching news for {company}"
        )

        articles = get_company_news(
            company
        )

        article_sentiments = []


        for article in articles:

            title = article.get(
                "title",
                ""
            )

            sentiment = analyzer.polarity_scores(
                title
            )

            article_sentiments.append({

                "title": title,

                "score":
                    sentiment["compound"],

                "published":
                    article.get(
                        "published"
                    ),

            })


        average_sentiment = 0

        if article_sentiments:

            average_sentiment = (

                sum(
                    item["score"]
                    for item in article_sentiments
                )

                /

                len(article_sentiments)

            )


        if average_sentiment > 0.15:

            overall_sentiment = (
                "positive"
            )

        elif average_sentiment < -0.15:

            overall_sentiment = (
                "negative"
            )

        else:

            overall_sentiment = (
                "neutral"
            )


        results.append({

            "company": company,

            "overall_sentiment":
                overall_sentiment,

            "sentiment_score":
                round(
                    average_sentiment,
                    3
                ),

            "articles":
                article_sentiments,

        })


    return {

        "agent_results": [

            {

                "task":
                    "news_analysis",

                "data":
                    results,

            }

        ]

    }