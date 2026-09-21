## Project overview

FinRiskAnalyser is a LangGraph multi-agent system for financial/investment analysis. A user query (e.g. "Should I invest in Reliance Industries for the next five years?") flows through a planner, entity resolution, parallel specialist analysis agents, and synthesis/reporting agents, producing a text report.

## Commands

This project uses `uv` for dependency management (Python >= 3.13, see `.python-version`).

```bash
uv sync              # install/sync dependencies from uv.lock
uv run python run.py # run the sample workflow end-to-end (prints the final report)
```

There is no test suite, linter, or formatter configured yet. `requirements.txt` and `pyproject.toml` both exist; `pyproject.toml` + `uv.lock` is the source of truth for dependencies.

A `GOOGLE_API_KEY` must be set in `.env` (loaded via `python-dotenv`) — agents use `langchain-google-genai` (`gemini-2.5-flash-lite`) for LLM calls.

## Architecture

The system is a LangGraph `StateGraph` (`app/graph/workflow.py`) over a single shared `AgentState` TypedDict (`app/models/state.py`). Each node is a plain function `(state) -> dict | state` that LangGraph merges back into state. Fields that multiple parallel branches write to use custom reducers (`merge_dict`, `merge_list` in `state.py`) so concurrent writes don't clobber each other — notably `financial_analysis`, `news_analysis`, `research_analysis`, `completed_tasks`, and `audit_log`.

**Currently wired graph** (see `app/graph/workflow.py`):

```
START -> query_understanding -> planner -> entity_resolution -> fan_out_tasks (conditional/parallel via Send())
      -> {financial_analysis, news_analysis, research_analysis} -> aggregation -> route_after_aggregation
      -> {[investment_analysis, risk_analysis] | comparison_analysis | report_generator} -> report_generator -> END
```

- **query_agent** (`app/agents/query_agent.py`, the graph's entry node): LLM call with structured output (`QueryUnderstanding`, `app/models/query.py`) that classifies intent and extracts companies/horizon/scope.
- **planner_agent**: deterministic (no LLM call) — maps `QueryUnderstanding` to an `ExecutionPlan` via lookup tables (`INTENT_MAP`, `INTENT_DEFAULT_TASKS`, `SCOPE_TO_TASK`) in `app/agents/planner_agent.py`. All planned tasks run in parallel.
- **entity_resolution_agent**: resolves company names to tickers via `app.tools.ticker_resolver.resolve_ticker` (uses `yfinance.Search`, prefers NSE-listed symbols — this is an India-focused analyser).
- **Dynamic fan-out**: `fan_out_tasks` in `workflow.py` reads `execution_plan.parallel_tasks` and uses LangGraph `Send()` to dispatch only the specialist nodes actually needed, each with its own state slice.
- **Specialist agents** (`financial_analysis_agent`, `news_analysis_agent`, `research_analysis_agent`): each fetches data via `app/services/` (`market_service.py` wraps `yfinance`, `news_service.py` scrapes Google News RSS via `feedparser`) or `app/tools/`, computes a simple rule-based score/assessment, writes its result keyed by ticker (financial, research) or by company (news) into its state field, and appends its task name to `completed_tasks`.
- **aggregation_agent**: fan-in gate — checks `completed_tasks` against `execution_plan.parallel_tasks` before allowing the graph to proceed.
- **route_after_aggregation** (`workflow.py`): branches on `execution_plan.intent` — `"comparison"` -> `comparison_analysis`; `"company_research"`/`"news_analysis"` -> straight to `report_generator`; everything else -> both `investment_analysis` and `risk_analysis` in parallel (a verdict and a risk read are independent lenses on the same data, not alternatives).
- **investment_analysis_agent** / **risk_analysis_agent**: both synthesize the specialist outputs per company via `score_company()` (`app/tools/scoring.py`) plus an LLM reconciliation call (`InvestmentVerdict` / `RiskAssessment`), with a deterministic fallback if the LLM call fails. Investment answers "should I buy"; risk answers "how much could go wrong" as a decoupled axis — both read the same quant facts so they can't disagree on data, only framing.
- **comparison_analysis_agent**: reuses `build_verdict()` per company, then one more LLM call across all companies to produce a comparative narrative, not just a sorted list.
- **report_generator_agent**: renders all accumulated state into a single formatted text report (`final_report`); reads `verification_result`/`governance_result`/`requires_human_review` defensively via `.get(..., {})` since those agents aren't wired in yet.

**Agents that exist as files but are not yet wired into `workflow.py`**: `verification_agent.py`, `governance_agent.py` — both still target a stale state shape and mutate `state` in place instead of the `(state) -> dict` convention (see `progress.md` for what they need before wiring in).

Every agent that mutates state appends a structured entry to `audit_log` describing what it did — preserve this pattern when adding or modifying agents.

## Conventions to follow when extending this codebase

- New specialist agents that should run in the parallel fan-out must: accept `state`, return a dict with their output field plus `"completed_tasks": ["<task_name>"]`, and be registered both as a graph node and in `fan_out_tasks`'s `task_to_node` map in `workflow.py`.
- New post-aggregation synthesis agents should reuse `score_company()` rather than re-deriving facts from the raw specialist outputs. If one runs as a parallel sibling of another post-aggregation node, neither may write plain non-reducer `AgentState` fields the other also writes (e.g. `current_agent`, `next_action`) — LangGraph raises `InvalidUpdateError` on concurrent writes to a field without a reducer.
- Follow the existing code's heavily broken-out formatting style (one argument/value per line in nested calls) — it's unusual but consistent across the codebase; match it in agent files rather than collapsing to dense one-liners.
- `ExecutionPlan.tasks`/`TaskType` is the single place defining valid task names; `ExecutionPlan.intent` is the single place defining post-aggregation routing. Keep both in sync with `workflow.py`.
- `progress.md` tracks the current build roadmap and known issues — check it before assuming a missing piece is out of scope.
