# Cybersecurity Sales Intelligence Prototype

A prospecting/prioritisation tool for a cybersecurity software sales
team — scores companies by internet-exposure risk (derived from
Shodan-style scan data) and generates a rep-readable explanation for
each account.

**Live app:** [your Streamlit URL]
**Case study brief:** Firmable take-home assignment

## What this does

Given raw internet-scan telemetry (~10.1M scan records), the pipeline:
1. Resolves scan records into company-level entities (filtering out
   hosting providers/CDNs, which the raw data conflates with real
   businesses)
2. Scores each company 0-100 using a deterministic rules engine, based
   on exposure signals (end-of-life software, exposed databases,
   known backdoors like DoublePulsar, self-signed certs, etc.)
3. Generates a natural-language explanation for high-priority accounts
   via LLM (Gemini)
4. Surfaces the ranked, filterable list in a Streamlit dashboard

See `docs/planning.md` for why these specific signals and this use
case were chosen, and `docs/architecture.md` for how the pieces fit
together, key trade-offs, and the cost model.

## Repo structure
├── app.py # Streamlit dashboard
├── scoring.py # rule-based scoring engine
├── llm_reasoning.py # LLM reasoning generation + tracing
├── requirements.txt
├── traces.jsonl # LLM call trace log
├── companies.parquet # aggregated company-level data
├── companies_scored.parquet # + rule scores
├── companies_final.parquet # + LLM reasoning text
├── skills/account-scoring/SKILL.md # packaged AI workflow definition
├── prompts/ # versioned prompts (v1, v2)
├── evals/ # labelled set, harness, results
└── docs/
├── planning.md # use case + signal rationale
└── architecture.md # system design, rule-vs-LLM split, cost model