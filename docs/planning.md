# Planning

## Use case chosen

Account scoring and prioritisation for outbound cybersecurity sales
reps — surfacing which companies, out of a large scanned population,
show concrete technical evidence of security exposure right now, and
giving the rep a one-line reason to open a call with.

## Why this over the alternatives

The brief allows scoring, summaries, signal classification, or
outreach drafting as the core LLM feature.

- Outreach draft generation was not chosen as the primary feature —
  it's the least differentiated capability; any team can already ask
  an LLM to draft an email. The harder, more interesting problem this
  dataset poses is *which* company to draft for.
- Company summaries alone were rejected as a standalone feature — a
  summary without a ranking doesn't solve a rep's actual daily
  workflow (deciding who to call next).
- Account scoring was chosen because it's directly gradable (a score
  can be compared against labelled ground truth for the eval
  requirement), it's the natural home for the "hidden signal"
  creativity the brief asks for, and it's what a rep would open the
  tool for every single day.

## The dataset, and a material correction to my original plan

The provided dataset is Shodan-style internet-scan telemetry — one
record per scanned IP/port, not one record per company. This was not
apparent from the brief's "thousands of businesses" framing; the raw
file decompresses to ~10.1 million scan records. This materially
changed the project:

1. **Entity resolution became the first engineering problem**, before
   any scoring logic — multiple scan records had to be aggregated
   into one row per company domain.
2. **A significant portion of "companies" in the raw aggregation were
   actually cloud/hosting infrastructure** (e.g. amazonaws.com,
   googleusercontent.com), not real sales targets — a single hosting
   provider's domain can sit behind thousands of unrelated customer
   IPs, which initially produced false "maximum risk" scores for
   infrastructure providers rather than businesses. This was corrected
   via a structural filter (distinct IP-count per domain, plus
   excluding Shodan's own `cloud`/`cdn` tags) rather than a manual
   company-name blocklist, since a blocklist cannot generalise to
   providers not already known by name.
3. Given the scale, the working prototype operates on a stratified
   sample (a random sample plus a targeted pull of rare high-severity
   tags) rather than the full 10.1M-row file — documented as a
   limitation in architecture.md, not hidden.

## Signals used and why

| Signal | Why it matters for cybersecurity buying | Confidence |
|---|---|---|
| doublepulsar / malware tags | Direct evidence of likely existing compromise, not just risk | [Certain] — these are well-documented indicators, not inferred |
| eol-product / eol-os tags | Running unsupported software with known unpatched vulnerabilities | [Certain] — Shodan's own classification |
| self-signed certificates | Signals weak/ad-hoc security practices | [Likely] |
| open directory listings | Direct misconfiguration, accidental data exposure | [Likely] |
| exposed databases | Database directly reachable from the internet — high severity misconfiguration | [Likely] |
| distinct open port count | Proxy for attack surface size | [Guessing] — a weaker, more indirect signal than the others; weighted lowest accordingly |

**Note on confidence:** none of these signals have been validated
against actual sales outcomes (did companies with these signals
actually convert to customers?) — that data doesn't exist in this
project. The weights in scoring.py reflect security-domain reasoning
(a backdoor is worse than an open port), not outcome-validated sales
data. This is stated explicitly rather than implied as proven.

## What I deliberately did not build

- Real-time re-scanning or live signal refresh — the prototype scores
  a static snapshot.
- Multi-user auth, CRM integration, outreach send capability — out of
  scope for a prototype demonstrating the core prioritisation logic.
- Full-dataset processing (10.1M rows) — worked from a sample for
  development-speed reasons; see architecture.md for what a
  production ingestion pipeline would need to change.