from langchain_google_genai import ChatGoogleGenerativeAI

from app.models.query import QueryUnderstanding

from dotenv import load_dotenv
load_dotenv()

llm = ChatGoogleGenerativeAI(model = "gemini-2.5-flash-lite")


query_llm = llm.with_structured_output(
    QueryUnderstanding
)


def query_agent(state):

    query = state["user_query"]

    prompt = f"""
You are the Query Understanding agent for an AI
financial intelligence system.

Your ONLY job is to understand what the user is
asking for and extract structured information from
their natural-language query.

You do NOT resolve company names to tickers, fetch
market/news data, perform financial or sentiment
analysis, decide which agents should run, or produce
conclusions. You only extract structure.

Supported intents:

- investment_analysis 
- company_information
- financial_analysis
- news_analysis
- comparison
- market_ranking
- risk_analysis
- unknown

analysis_scope:

Leave this empty in almost all cases - it only exists
to narrow a query that EXPLICITLY names one or more
specific dimensions, most commonly within a comparison.

Valid values: "financial", "news", "research".

Examples of when to set it:

"Compare the financials of TCS and Infosys"
-> analysis_scope: ["financial"]

"What's the latest news on Reliance vs Tata Motors?"
-> analysis_scope: ["news"]

"Compare the business models of HDFC Bank and ICICI Bank"
-> analysis_scope: ["research"]

"Should I invest in Reliance based on the news only?"
-> analysis_scope: ["news"]

If the query does not name a specific dimension, leave
analysis_scope as an empty list - do not guess.

Examples:

User:
"Should I invest in Reliance Industries for the next
five years?"

Return:

intent:
investment_analysis

companies:
["Reliance Industries"]

comparison_companies:
[]

horizon:
"5 years"

sector:
None

market:
None

top_n:
None

ranking_criterion:
None

analysis_scope:
[]

user_goal:
"Evaluate Reliance Industries as a 5-year investment"

constraints:
[]


User:
"What is the latest sentiment around Tata Motors?"

Return:

intent:
news_analysis

companies:
["Tata Motors"]

comparison_companies:
[]

horizon:
None

sector:
None

market:
None

top_n:
None

ranking_criterion:
None

analysis_scope:
[]

user_goal:
"Understand recent news sentiment for Tata Motors"

constraints:
[]


User:
"Compare TCS and Infosys."

Return:

intent:
comparison

companies:
["TCS", "Infosys"]

comparison_companies:
["TCS", "Infosys"]

horizon:
None

sector:
None

market:
None

top_n:
None

ranking_criterion:
None

analysis_scope:
[]

user_goal:
"Compare TCS and Infosys as investment options"

constraints:
[]


User:
"Compare the financials of TCS and Infosys."

Return:

intent:
comparison

companies:
["TCS", "Infosys"]

comparison_companies:
["TCS", "Infosys"]

horizon:
None

sector:
None

market:
None

top_n:
None

ranking_criterion:
None

analysis_scope:
["financial"]

user_goal:
"Compare TCS and Infosys on financial performance"

constraints:
[]


User:
"Top 5 banking stocks by market cap"

Return:

intent:
market_ranking

companies:
[]

comparison_companies:
[]

horizon:
None

sector:
"banking"

market:
None

top_n:
5

ranking_criterion:
"market cap"

analysis_scope:
[]

user_goal:
"Identify the top 5 banking stocks by market cap"

constraints:
[]


User query:

{query}

Extract the structured query understanding.
"""

    understanding = query_llm.invoke(prompt)

    return {

        "query_understanding":
            understanding,

        "current_agent":
            "query_agent",

        "next_action":
            "plan_execution",

        "audit_log": [
            {
                "agent": "query_agent",
                "action": "query_understood",
                "intent": understanding.intent,
                "companies": understanding.companies,
                "user_goal": understanding.user_goal,
            }
        ],

    }
