Coverage, in priority order (highest blast-radius first)

1. score_company() (app/tools/scoring.py) — the shared quant core every synthesis agent (investment_analysis_agent, risk_analysis_agent, comparison_analysis_agent) depends on via build_verdict(). Cases: full data (financial+news+research present) → correct composite/recommendation bucket at each Buy/Hold/Avoid boundary (0.65, 0.45); missing financial data → 0.5 fallback + confidence penalty; missing/zero-article news → same; revenue_trend growing/declining nudge; analyst_upside_pct ±15% nudge; financial_entry.status == "failed" treated as absent; rationale string assembly for each branch (observations present/absent, sector present/absent, beta volatility labels).
2. planner_agent() (app/agents/planner_agent.py) — every INTENT_MAP/INTENT_DEFAULT_TASKS entry produces the documented ExecutionPlan (intent bucket + task list + requires_* flags + requires_market_ranking only for market_ranking); analysis_scope override replaces rather than adds to the default task set; unknown intent falls back to "unknown" bucket with empty task list. Also a consistency guard test: every value in INTENT_MAP must be a valid ExecutionPlan.intent literal, and every TaskType used in INTENT_DEFAULT_TASKS/SCOPE_TO_TASK must be a valid TaskType literal — this directly encodes the invariant CLAUDE.md calls out ("keep ExecutionPlan.tasks/TaskType... and ExecutionPlan.intent... in sync with workflow.py"), so a future edit that breaks it fails a test instead of failing silently at runtime.
3. State reducers (app/models/state.py) — merge_dict (later key wins, doesn't mutate existing), merge_list (concatenates, doesn't mutate existing) — cheap tests, but this is exactly the concurrency-safety mechanism the parallel fan-out depends on.
4. financial_analysis_agent.analyze_financials() and its _score_* helpers (app/agents/financial_analysis_agent.py) — each helper's boundary thresholds (growth/earnings/profitability/valuation/leverage/cash), CAGR-preferred-oic, "error" in data →status: "failed" short-circuit, composite weighting → strong/moderate/
5. risk_analysis_agent's _score_financial_risk/_score_market_risk/_score_sentiment_riisk_label/_confidence_from_flags/_fallback_top_risk_factors
   (app/agents/risk style ofboundary-threshold tests, plus the has_data flags driving
   confidence.
6. Routing (app/graph/workflow.py) — route_after_planner
   (market_ranking  onrequires_market_ranking), route_after_aggregation (comparison /
   company_researchoth-investment-and-risk, covering every ExecutionPlan.intent literal), fan_out_tasks (only
   known tasks in pnd, unknown task namesare silently skipped, each Send carries the right state slice).
7. Agent-level testes — one happy-path +one degraded-data path each:
   - entity_resoluticker (patched atapp.agents.entity_resolution_agent.resolve_ticker); also
     test_ticker_redirectly to test theNSE-preference/fallback/no-quotes logic in resolve_ticker()
     itself.
   - financial_analysis_agent — mock
     get_company_da.
   - news_analysis_agent — mock get_company_news; real
     SentimentIntenc, no network) sosentiment bucketing is tested for real.
   - research_analy; one test withbusiness_summary=None (skips the qualitative LLM call), one with
     it set and resextract_revenue_trend() tested directly for
     growing/declindata.
   - aggregation_agent — pure, no mocking:
     required.issub
   - market_ranking_agent — mock
     fetch_sector_cion; empty-constituentspath returns empty companies/tickers + audit entry instead of
     crashing.
8. Synthesis agents' LLM-fallback paths — these have a try/except
   around every LLM fallback, and bothbranches need coverage since an untested fallback is exactly what
   silently drifts:
   - investment_analysis_agent.build_verdict() — mock
     synthesize_invccess path (returnsverdict dict as given) and make it raise for the fallback path
     (asserts fallbquant["recommendation"]/rationale/_confidence_bucket()).
   - risk_analysis_t() — same patternagainst synthesize_risk_assessment, asserting fallback uses
     _fallback_top_
   - comparison_analysis_agent — mock build_verdict (imported from
     investment_ananking/rank-assignmentlogic from scoring; separately mock synthesize_comparison
     success/failurck ("{leader} rankshighest...") and the empty-ranking edge case ("No companies to
     compare.").
9. report_generator_agent — pure string rendering given a
   fully-populated pected section headersand content; and the defensive .get(..., {}) paths for risk_assess
   ment/verificatio/requires_human_reviewrender sensibly when those keys are absent (mirrors the exact gap
   result.md's samp
10. tests/integration/test_full_workflow_smoke.py (opt-in) —
    graph.invoke()  (e.g. reuse run.py'ssample query), marked @pytest.mark.integration, asserting
    structural prop-empty, final_reportcontains expected section headers, no unhandled exception) rather
    than pinning exy default via addopts;documented in a short note (README or a comment in the test file)
    on how to run iation, requiresGOOGLE_API_KEY in .env).

Not in scope for this pass

- verification_agent.py / governance_agent.py — unwired and targeting
  a stale state sha2); testing them nowwould mean testing code that's about to be rewritten. Revisit once
  they're rewired.
- query_agent.py's prompt content itself — covered structurally by
  the integration sompt wording would bebrittle and low-value.
- Full coverage too added later if useful;not blocking.

Verification                                                        
- uv sync after adding pytest, then uv run pytest — should run the  full suite (integass.
- uv run pytest -m integration — runs the live smoke test (requires GOOGLE_API_KEY).
- Spot check: intentionally break one boundary threshold (e.g. the Buy/Hold cutoff ifirm the correspondingtest fails, to sanity-check the test isn't vacuous.
