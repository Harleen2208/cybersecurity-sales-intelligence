# Architecture

## System overview

    Shodan-scan dataset (.zst, ~10.1M records)
              |
              v
    DuckDB: filtered sample + targeted rare-signal sample
              |
              v
    DuckDB: aggregation to company-level rows (companies.parquet)
      - entity resolution: IP-count threshold, cloud/cdn tag exclusion
      - signal counting: eol-product, malware, doublepulsar, etc.
              |
              v
    scoring.py (rules only): companies_scored.parquet
      - deterministic 0-100 score, hot/warm/cold tier
              |
              v
    llm_reasoning.py (LLM): companies_final.parquet + traces.jsonl
      - natural-language reasoning_summary per top account for 21 companies due to Genai limit
              |
              v
    app.py (Streamlit): ranked dashboard, filter by tier, drill-in view

## Rule vs LLM split — and why

**Rules, no LLM:**
- Entity resolution (IP-count thresholding, tag-based exclusion) —
  structural, deterministic, needs to run over millions of rows
  cheaply.
- All signal aggregation (counting tag occurrences per domain) — pure
  arithmetic.
- The 0-100 score and tier bucketing — fixed, auditable business
  logic; a rep or manager needs to be able to explain exactly why a
  score is what it is, which a deterministic rule allows and an LLM
  call does not guarantee consistently.

**LLM:**
- Only the `reasoning_summary` text — synthesising several already-
  computed signals into one specific, readable sentence. This is a
  genuine language-generation task suited to an LLM; a rules-based
  template would either be too rigid (can't naturally vary phrasing
  and emphasis based on which signals are present) or require as much
  engineering effort as just using the LLM correctly.

**Why the split matters:** an LLM call for something a `GROUP BY` or
`COUNT` already does deterministically would add latency, cost, and
non-determinism for no quality benefit — the exact "prompts glued
together" anti-pattern this brief warns against. Every LLM call in
this system is doing something a rule genuinely cannot: generating
natural language.

## Cost model

- 21 of the reasoning_summary generations went through the traced API
  integration (llm_reasoning.py → traces.jsonl) — full request/
  response/token/cost data available for these.
- An additional 136 were generated via manual chat-interface prompting
  with the same v2 system prompt, as a workaround for hitting the free
  API tier's rate limit within the project timeline — these are not
  traced, since they didn't go through the logged code path.
- **Production recommendation:** all reasoning generation should go
  through the API integration exclusively, never a manual chat
  workaround, specifically so every call is traced. The manual
  approach used here was a timeline-constrained workaround, not a
  pattern to keep.
- Model used in development: Gemini 3.6 Flash (free tier) — chosen
  for zero-cost iteration during prototyping.
- Model choice for production: a cheap/fast tier model (Claude Haiku
  or Gemini Flash equivalent) remains appropriate for this specific
  task — reasoning_summary generation is a bounded, low-complexity
  task with a fixed, constrained output schema. A stronger/more
  expensive model would only be justified if a future feature required
  harder judgment, e.g. resolving conflicting or ambiguous signals
  across multiple data sources, or ranking accounts against a written,
  nuanced ICP description rather than fixed numeric thresholds.
- Estimated production cost math (using Claude Haiku pricing as a
  reference point, ~$0.80/million input tokens, ~$4/million output
  tokens): each call uses roughly 425 input tokens (small JSON
  signal payload + system prompt) and ~40-60 output tokens (one
  sentence). At ~425 input + 50 output tokens per call: cost per call
  ≈ (425 × $0.0000008) + (50 × $0.000004) ≈ $0.00054. At 157 calls/day
  cost would be ~$0.08478.
  (only re-scoring top accounts, not the full base, on a daily
  cadence): ≈ $0.01/day, ≈ $0.33/month. Even scaling to re-score 1,000
  accounts daily: ≈ $0.36/day, ≈ $11/month.
- **Cost ceiling I would set in production:** cap LLM reasoning calls
  to top-N accounts by rule score per re-scoring cycle (e.g. top 100
  per day), not all accounts — the rule score alone is sufficient for
  ranking/filtering; the LLM reasoning is a UX enhancement for the
  accounts a rep is actually about to look at, not something every
  account needs generated proactively.

## Tracing & observability schema

Every LLM call logged to `traces.jsonl`, one JSON object per line:

    {
      "timestamp": "ISO8601 UTC",
      "call_id": "uuid",
      "skill": "account-scoring",
      "prompt_version": "v2",
      "model": "gemini-2.0-flash",
      "input_company": "domain string",
      "input_tokens": int,
      "output_tokens": int,
      "latency_ms": int,
      "cost_usd": float,
      "output": { "reasoning_summary": "string" }
    }

This schema is what the eval harness and any future cost audit reads
from directly — it is not a separate estimate, it's computed from
real call data.

## Known trade-offs and limitations

- **Entity resolution is heuristic, not ground-truth.** IP-count
  thresholding (≤10 distinct IPs/domain) plus exclusion of Shodan's
  `cloud`/`cdn` tags catches most infrastructure providers but not
  all (e.g. smaller regional hosting providers/ISPs may still pass
  through, since they don't structurally differ enough from a
  legitimate business with many servers). A production system would
  resolve entities against a verified business registry rather than
  scan-derived heuristics.
- **Development was done on a sample, not the full ~10.1M-row
  dataset**, for iteration speed. Rare high-severity signal tags
  (doublepulsar, malware) occurred only single-digit times even across
  a 200K+ row sample — a production ingestion pipeline processing the
  full file would surface meaningfully more of these highest-value
  signals.
- **Signal weights in the scoring model are reasoned from security-
  domain knowledge, not validated against real sales-outcome data** —
  there is no conversion/close data available in this project to
  confirm these weights predict actual buying likelihood.
- **IP-count thresholding does not catch all infrastructure/ISP domains** — e.g., large telecom providers' reverse-DNS ranges (vodafone-ip.de) can appear as individual low-IP-count domains despite representing shared carrier infrastructure, not a single business. A production system would cross-reference against a known-ISP/ASN registry rather than IP-count alone.