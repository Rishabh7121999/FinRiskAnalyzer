from langchain_google_genai import ChatGoogleGenerativeAI

from app.models.execution_plan import ExecutionPlan

from dotenv import load_dotenv
load_dotenv()

llm = ChatGoogleGenerativeAI(model = "gemini-2.5-flash-lite")


planner_llm = llm.with_structured_output(
    ExecutionPlan
)


def planner_agent(state):

    state["current_agent"] = "planner_agent"

    query = state["user_query"]

    prompt = f"""
You are the planning agent for an AI financial
intelligence system.

Your responsibility is to understand the user's
request and create an execution plan.

Available tasks:

- financial_analysis
- news_analysis
- research_analysis

IMPORTANT:

financial_analysis, news_analysis and research_analysis
are independent tasks.

If more than one of these tasks is required, include
ALL of them in both:

1. tasks
2. parallel_tasks

They can execute concurrently because they do not
depend on each other's results.

Examples:

User:
"Should I invest in Reliance Industries for the next
five years?"

Return:

intent:
investment_analysis

companies:
["Reliance Industries"]

tasks:
[
    "financial_analysis",
    "news_analysis",
    "research_analysis"
]

parallel_tasks:
[
    "financial_analysis",
    "news_analysis",
    "research_analysis"
]


User:
"What is the latest sentiment around Tata Motors?"

Return:

intent:
news_analysis

companies:
["Tata Motors"]

tasks:
[
    "news_analysis"
]

parallel_tasks:
[
    "news_analysis"
]


User:
"Compare TCS and Infosys."

Return:

intent:
comparison

companies:
["TCS", "Infosys"]

tasks:
[
    "financial_analysis",
    "news_analysis",
    "research_analysis"
]

parallel_tasks:
[
    "financial_analysis",
    "news_analysis",
    "research_analysis"
]

User query:

{query}

Create the execution plan.
"""

    plan = planner_llm.invoke(prompt)

    # All specialist tasks are independent.
    # Therefore they can run in parallel.

    plan.parallel_tasks = plan.tasks

    state["execution_plan"] = plan

    state["companies"] = plan.companies

    state["audit_log"].append({
        "agent": "planner_agent",
        "action": "execution_plan_created",
        "intent": plan.intent,
        "companies": plan.companies,
        "tasks": plan.tasks,
    })

    state["next_action"] = "resolve_entities"

    return state