# Query Agent Specification

## 1. Purpose

The **Query Agent** is the first reasoning step in the workflow.

Its job is to understand **what the user is asking for** and convert the natural-language query into structured information that the **Planner Agent** can use.

**Query Agent:** *What does the user want?*
**Planner Agent:** *What work is required to answer it?*

---

## 2. Responsibilities

The Query Agent extracts:

* **Intent** — what the user wants to achieve
* **Companies/entities** — e.g. Reliance, TCS
* **Market/exchange** — NSE, BSE
* **Sector** — banking, IT, energy, etc.
* **Time horizon** — e.g. 5 years, recently
* **Top N** — e.g. top 5
* **Ranking criterion** — market cap, revenue, returns, etc.
* **Comparison entities** — when comparing stocks
* **User goal** — concise description of the requested outcome
* **Constraints** — any additional requirements

It produces a **structured Pydantic object**, not free-form text.

---

## 3. Supported Intents

```text
investment_analysis
company_information
financial_analysis
news_analysis
comparison
market_ranking
risk_analysis
unknown
```

### Examples

| User Query                                      | Intent                |
| ----------------------------------------------- | --------------------- |
| Should I invest in Reliance for 5 years?        | `investment_analysis` |
| Tell me about Reliance                          | `company_information` |
| What is Reliance's current P/E?                 | `financial_analysis`  |
| What happened to Reliance recently?             | `news_analysis`       |
| Compare Reliance and TCS                        | `comparison`          |
| Top 5 banking stocks by market cap              | `market_ranking`      |
| What are the risks of investing in Tata Motors? | `risk_analysis`       |

---

## 4. Structured Output

```python
from typing import Literal
from pydantic import BaseModel, Field


class QueryUnderstanding(BaseModel):
    intent: Literal[
        "investment_analysis",
        "company_information",
        "financial_analysis",
        "news_analysis",
        "comparison",
        "market_ranking",
        "risk_analysis",
        "unknown",
    ]

    companies: list[str] = Field(default_factory=list)

    comparison_companies: list[str] = Field(default_factory=list)

    horizon: str | None = None
    sector: str | None = None
    market: str | None = None

    top_n: int | None = None
    ranking_criterion: str | None = None

    user_goal: str
    constraints: list[str] = Field(default_factory=list)
```

Example:

```text
Query:
"Should I invest in Reliance for the next 5 years?"

QueryUnderstanding:
{
    intent: "investment_analysis",
    companies: ["Reliance Industries"],
    comparison_companies: [],
    horizon: "5 years",
    sector: None,
    market: "NSE/BSE",
    top_n: None,
    ranking_criterion: None,
    user_goal: "Evaluate Reliance as a 5-year investment",
    constraints: []
}
```

---

## 5. What the Query Agent Does NOT Do

The Query Agent should **not**:

* Resolve company names to NSE/BSE tickers
* Fetch market/news/financial data
* Perform financial analysis
* Perform sentiment analysis
* Retrieve RAG documents
* Decide which agents should execute
* Generate investment conclusions
* Generate the final report

These responsibilities belong to downstream components.

---

## 6. Query → Planner Contract

The Query Agent produces:

```text
User Query
    ↓
Query Agent
    ↓
QueryUnderstanding
    ↓
Planner Agent
    ↓
ExecutionPlan
```

Example:

```text
Query Agent:
intent = investment_analysis
company = Reliance Industries
horizon = 5 years
```

The Planner then decides:

```text
Required Tasks:
- financial_analysis
- news_analysis
- research_analysis

Parallel Tasks:
- financial_analysis
- news_analysis
- research_analysis
```

The **Query Agent identifies the goal; the Planner determines the execution strategy.**

---

## 7. State Integration

Add the structured query understanding to `AgentState`:

```python
query_understanding: QueryUnderstanding
```

Import:

```python
from app.models.query import QueryUnderstanding
```

Workflow:

```text
START
  ↓
Query Agent
  ↓
Planner
  ↓
Entity Resolution
  ↓
Dynamic Specialist Execution
  ↓
Aggregation
  ↓
Intent-based Analysis
  ↓
Risk / Verification / Governance
  ↓
Report
  ↓
END
```

---

## 8. Design Principle

The Query Agent should be **deterministic in its output structure but LLM-powered in language understanding**.

The key separation is:

```text
Query Agent  → Understand the request
Planner      → Plan the work
Entity Agent → Resolve entities
Specialists  → Collect/analyze evidence
Router       → Select the appropriate downstream workflow
Report Agent → Present the result
```

This separation prevents the Query Agent from becoming a **monolithic agent that understands, plans, executes, and answers everything**.
