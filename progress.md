_Last verified against working tree on 2026-09-22 (uncommitted changes included)._

## ✅ Done

* **LangGraph base workflow**, `START -> query_understanding -> planner -> entity_resolution -> {financial_analysis, news_analysis, research_analysis} -> aggregation -> route_after_aggregation -> {[investment_analysis, risk_analysis] | comparison_analysis | report_generator} -> report_generator -> END`. `investment_analysis`/`risk_analysis` run as parallel siblings (both returned from one conditional-edge fan-out), not alternatives.

* **Query Agent** (`app/agents/query_agent.py`)

  * LLM call with structured output (`QueryUnderstanding`, `app/models/query.py`).
  * Classifies intent (8 values, including `market_ranking`/`company_information`/`risk_analysis` which have no dedicated handling yet), extracts companies, horizon, sector/top_n/ranking_criterion, and `analysis_scope` (explicit dimension narrowing, e.g. "compare the financials of X and Y").
  * This closes out the "Query Agent" item that used to be the top of the roadmap — it's wired in as the real entry node, not a stub.

* **Planner Agent** (`app/agents/planner_agent.py`)

  * Deterministic `QueryUnderstanding.intent -> ExecutionPlan.intent` mapping (`INTENT_MAP`) and `-> default task set` mapping (`INTENT_DEFAULT_TASKS`), documented inline.
  * `analysis_scope`, when set, overrides the default task set entirely via `SCOPE_TO_TASK`.
  * This is the "correct intent-based routing" work that was the stated next priority — it's done for the fan-out stage. See **Issues** for what's still missing on the *post-aggregation* routing side.

* **Entity Resolution Agent** — company names → tickers (`Reliance Industries → RELIANCE.NS`), NSE-preferring.

* **Dynamic parallel execution** — `fan_out_tasks` in `workflow.py` uses `Send()` to dispatch only the specialist nodes in `execution_plan.parallel_tasks`.

* **Financial / News / Research Analysis Agents** — fetch via `market_service`/`news_service`/`yfinance`, write keyed-by-ticker (financial, research) or keyed-by-company (news) results, append to `completed_tasks` and `audit_log`.

* **Aggregation Agent** (`app/agents/aggregation_agent.py`) — fan-in gate after the parallel branches, replaces the old deleted `aggregator_agent.py`.

* **Investment Analysis Agent** — LLM call (grounded in fetched data) producing a structured Buy/Hold/Avoid verdict (`InvestmentVerdict`, `app/models/investment_verdict.py`) with thesis, supporting points, conflicting-signal reconciliation, key risks, horizon note. Falls back to the deterministic `score_company()` quant verdict (`app/tools/scoring.py`) if the LLM call fails; the quant verdict is always kept alongside for auditability. Exposes `build_verdict()` for reuse.

* **Risk Analysis Agent** (`app/agents/risk_analysis_agent.py`) — answers a decoupled question from investment_analysis ("how much could go wrong", not "should I buy"). Reuses `score_company()` (same quant facts as investment_analysis, so the two can't disagree on data) and rule-based thresholds to produce per-dimension risk (financial/leverage, market/volatility, sentiment, business/structural) plus an aggregate `risk_level`/`risk_score`/`confidence`. An LLM call (`RiskAssessment`, `app/models/risk_assessment.py`) turns that into `top_risk_factors`/`mitigating_factors`/`horizon_note`, falling back to a deterministic version (drivers flattened from the dimensions, most severe first) if the call fails — same try/except shape as `build_verdict()`. Runs as a parallel sibling of `investment_analysis`, not a sequential follow-up.

* **Comparison Analysis Agent** (`app/agents/comparison_analysis_agent.py`) — reuses `build_verdict()` per company, then one more LLM call across all companies to produce a comparative narrative (why the leader wins, differentiators, per-company notes), not just a sorted list. Wired into the graph via `route_after_aggregation` on `intent == "comparison"`.

* **Market Ranking Agent** (`app/agents/market_ranking_agent.py`) — the fix for issue 3 below. Runs in place of `entity_resolution` for the `market_ranking` intent (new `route_after_planner` conditional edge, `ExecutionPlan.requires_market_ranking`): resolves `sector` to an NSE sectoral index's constituent list (`app/services/screener_service.py`, backed by niftyindices.com's public per-index CSVs — no session cookies/unofficial API, unlike nseindia.com directly), ranks by `ranking_criterion` via `market_service.get_company_data()` (same fetch path `financial_analysis_agent` uses, not a new bulk data source), and writes the top `top_n` as `companies`/`tickers`. An unrecognized sector, or no sector at all with no NIFTY 500 fallback match, writes empty `companies`/`tickers` + an audit entry rather than raising. `INTENT_MAP["market_ranking"]` now points to `"comparison"` (was `"company_research"`) and its default task set is the full 3 specialists (was `research_analysis`-only) so the resolved shortlist gets the same ranked-narrative treatment `comparison_analysis_agent` gives named companies.

* **Report Generator Agent** — renders all accumulated state into `final_report`, including the new verdict/comparison narrative fields; already reads `risk_assessment` / `verification_result` / `governance_result` / `requires_human_review` defensively via `.get(..., {})`, so wiring those agents in later won't require report-side changes.

* **Verification Agent** (`app/agents/verification_agent.py`) — rewritten against current `AgentState` and the `(state) -> dict` convention (was issue 2 below), deterministic (no LLM call). Runs as a universal fan-in gate after synthesis, before governance: checks per-ticker specialist-data completeness, whether `build_verdict()`/`build_risk_assessment()` fell back to their deterministic path (`synthesis_status != "ok"`), low confidence on either verdict or risk read, and an unreconciled signal (a `Buy` recommendation next to `High`/`Severe` risk with no `conflicting_signals` logged). Degrades gracefully when only some of `investment_analysis`/`risk_assessment`/`comparison_analysis` are populated (varies by intent) or none are (`company_research`/`news_analysis` intents — completeness-only check).

* **Governance Agent** (`app/agents/governance_agent.py`) — rewritten alongside verification (was issue 2 below), deterministic (no LLM call). Runs after verification: always attaches a SEBI-style "not registered investment advice" disclosure, escalates `requires_human_review = True` on `Severe` risk + `Buy`/`Hold`, on verification's fallback+low-confidence combination, and on verification's unreconciled-signal flag. `requires_human_review` and `governance_result` are annotate-only in this pass (rendered as a banner/section by `report_generator`) — no LangGraph `interrupt()`/pause is wired, and `retry_count`/`max_retries` are still untouched (no retry loop). Both agents are wired into `workflow.py` as a fixed `verification -> governance -> report_generator` tail that every intent's path now funnels through (`investment_analysis`/`risk_analysis`, `comparison_analysis`, and the direct `company_research`/`news_analysis` route all point at `verification` instead of `report_generator` directly).

* **State reducers** — `merge_dict` for specialist outputs, `merge_list` for `completed_tasks` and `audit_log`.

* **Test suite** (`tests/`, was issue 6 below) — `pytest` wired via `pyproject.toml`'s `[dependency-groups] dev` + `[tool.pytest.ini_options]` (`testpaths = ["tests"]`, `pythonpath = ["."]`, `addopts = "-m 'not integration'"` so the live-API test is opt-in only). 134 unit tests + 1 integration test, all passing (`uv run pytest -q` → `135 passed, 1 deselected`). Shared fixtures/builders (`make_financial_entry`/`make_news_entry`/`make_research_entry`/`make_execution_plan`/`make_base_state`) live in `tests/conftest.py`. Coverage follows `testsuite.md`'s priority order: `app/tools/scoring.py`'s `score_company()` (11 tests — Buy/Hold/Avoid boundaries, missing-data fallbacks, revenue/analyst-upside nudges), `planner_agent.py` (11 — every `INTENT_MAP`/`INTENT_DEFAULT_TASKS` entry plus a consistency guard that every mapped value is a valid `ExecutionPlan.intent`/`TaskType` literal), `state.py` reducers (5), every specialist/synthesis/aggregation/market-ranking/entity-resolution agent (happy-path + degraded-data path each, LLM calls mocked so fallback branches are exercised), `workflow.py` routing (`route_after_planner`/`route_after_aggregation`/`fan_out_tasks`, 10 tests), and — now that verification/governance are rewired — `test_verification_agent.py` (11) and `test_governance_agent.py` (8) covering the per-ticker flag logic, the fallback+low-confidence and unreconciled-risk-signal escalation rules, and the disclosure/`requires_human_review` output. `tests/integration/test_full_workflow_smoke.py` runs `run.py`'s sample query through the real graph (`@pytest.mark.integration`, needs `GOOGLE_API_KEY` + network), asserting structural properties (non-empty `final_report`, expected section headers) rather than pinning exact LLM output.

---

## 🐞 Issues found (verified in current working tree)

1. ~~**`risk_analysis` intent has no real destination.**~~ **Fixed.** `risk_scoring_agent.py` (stale, wrong state shape) was replaced by `app/agents/risk_analysis_agent.py`, written against the current `AgentState` and the `(state) -> dict` merge-back convention. It reuses `score_company()` (the same quant layer `investment_analysis_agent` uses) and re-projects it into a decoupled risk lens: per-dimension severity (financial/leverage, market/volatility, sentiment, business/structural), an aggregate `risk_level`/`risk_score`/`confidence`, and an LLM-narrative synthesis (`RiskAssessment` model, `app/models/risk_assessment.py`) with a deterministic fallback, mirroring `investment_analysis_agent`'s `build_verdict()` pattern. `route_after_aggregation` now returns `["investment_analysis", "risk_analysis"]` for the `investment_analysis`/`risk_analysis`/`unknown` intents (they're independent lenses over the same aggregated data, not alternatives — a "should I invest" query wants both a verdict and a risk read). Both feed `report_generator`, which renders a real `_format_risk_section()` instead of the old raw `{risk}` dict dump. `comparison_analysis` keeps its own exclusive branch for `intent == "comparison"`.

   Side effect: since `investment_analysis` and `risk_analysis` now run in the same superstep (parallel siblings, like the fan-out specialists), `investment_analysis_agent` no longer writes `current_agent`/`next_action` — those are plain (non-reducer) state fields and two parallel writers in one step raises `InvalidUpdateError`. Same reason the specialist agents never wrote them.

2. ~~**`risk_scoring_agent.py` ... written against a state shape that no longer exists.**~~ **Fixed for risk** (see #1 above; the file was deleted and replaced). ~~`verification_agent.py` and `governance_agent.py` still read stale fields...`~~ **Fixed.** Both rewritten against current `AgentState` and the `(state) -> dict` convention, and wired in as a `verification -> governance -> report_generator` tail every intent passes through (see **Done** above).

3. ~~**No screening/ranking agent for `market_ranking` intent.**~~ **Fixed.** `market_ranking_agent.py` + `screener_service.py` added (see **Done** above) — sector queries now resolve against NSE sectoral index CSVs instead of dead-ending on an empty `companies` list. Coverage is bounded to the ~15 sectors niftyindices.com actually indexes (banking, IT, auto, pharma, FMCG, metal, energy, realty, media, financial services, PSU/private bank) plus a NIFTY 500 sample (capped to 50) as the no-sector "whole market" fallback — a sector outside that set, or a criterion outside the handful mapped in `_CRITERION_FIELD_MAP` (market cap/PE/revenue growth/profit margin/dividend yield), falls back gracefully rather than crashing (empty result or default-to-market-cap, respectively). Not yet covered: BSE-only listings, criteria beyond that handful (e.g. "returns" would need historical price data, not `get_company_data()`), and niftyindices.com's CSV endpoints are still an unofficial dependency (public and stable so far, but not a documented/SLA'd API).

4. **`CLAUDE.md` and (until this update) `progress.md` are stale relative to the code.** `CLAUDE.md` currently states `query_agent.py` is "a stub, 0 lines" and not wired into the graph — it's actually ~280 lines and is the graph's entry node. It also doesn't mention `comparison_analysis_agent.py` or `aggregation_agent.py` (renamed/rebuilt from the deleted `aggregator_agent.py`). Worth a pass to resync `CLAUDE.md` with the actual graph shape so future sessions don't work from wrong assumptions.

5. **Uncommitted work, still open** (previous large batch from issue 5's original write-up is now committed as `12750c1`). Current working tree on top of that: 7 modified tracked files (~480 insertions / ~80 deletions — the verification/governance rewrite + workflow wiring + `progress.md` itself) plus 2 untracked paths (`tests/`, `testsuite.md` — the new test suite). Recommend two commits: "rewrite+wire verification/governance agents" (the 5 non-progress tracked files) and "add pytest test suite" (`tests/` + `testsuite.md` + the `pyproject.toml`/`uv.lock` dependency-group changes), with `progress.md` riding along with whichever it documents.

6. ~~**No test suite, linter, or formatter.**~~ **Test suite fixed** (see **Done** above) — `tests/` + `pytest` config added, 135 tests passing. `testsuite.md` (the planning doc for that pass) is now itself slightly stale: its "Not in scope" section says `verification_agent.py`/`governance_agent.py` are unwired/excluded, but both got rewritten+wired in this same working-tree pass and now have dedicated test files — worth a follow-up note there, or just let this `progress.md` entry supersede it. No linter/formatter yet (e.g. `ruff`) — still open.

7. **Minor:** `run.py`'s `initial_state` doesn't set `"comparison_analysis": {}` (it's present in `AgentState` and read via `.get(..., {})` in the report generator, so it's not a crash — just an inconsistency with how every other state field is pre-seeded there).

---

## 🔨 Need to do

### Immediate priority

Fix or explicitly resolve the remaining issues above **before** adding more surface area (API/frontend). In order of leverage:

1. Commit the current working tree in logical chunks (issue 5): verification/governance rewrite, then the test suite.
2. Resync `CLAUDE.md` with the real graph (issue 4) — it still describes the pre-risk-analysis graph shape, and now also predates the verification/governance wiring and the test suite.
3. Reconcile `testsuite.md` with reality (issue 6) — its "Not in scope" section is now wrong about verification/governance.

### Then, in roughly this order

* **Upgrade Research Agent to RAG** over annual reports, investor presentations, NSE/BSE filings, SEBI documents, industry reports (currently basic `yfinance` company/business info).
* **Linter/formatter** (e.g. `ruff`) — still nothing configured.
* **MCP** — expose market/news/research/financial tools through MCP.
* **Production hardening** — retries/fallbacks (note: `retry_count`/`max_retries` still exist on `AgentState` but nothing reads/increments them; `governance_agent` doesn't retry on its flags, only annotates), Redis/cache, rate limiting, checkpointing, real human-in-the-loop pause (`requires_human_review` is now set by `governance_agent`, but it's annotate-only — rendered in the report, not an actual `interrupt()`-based execution pause), observability, evaluation, prompt/version management, cost/latency monitoring.
* **Deployment**: Docker → CI/CD → Dev/UAT/Prod → GCP.

### After the above (not before)

* FastAPI wrapper + frontend + formatted report rendering. Wrapping the graph in an API/UI now would mean keeping three layers in sync while the core graph is still mid-refactor and has no tests as a safety net — see the discussion above.
