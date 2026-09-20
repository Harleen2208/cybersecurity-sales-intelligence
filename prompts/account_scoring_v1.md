# account_scoring — prompt v1

**Status:** deprecated — an earlier, simpler version of the prompt,
included here to demonstrate prompt versioning as requested in the
brief.

## System prompt (v1)

You are scoring a company for cybersecurity sales prioritisation.
Given the company data, output a score from 0-100 and a one-sentence
reason.

## Why v2 replaced it

- No instruction preventing the model from re-deriving its own score
  instead of using the rules-engine score passed in — risked drift
  between the displayed score and the LLM's reasoning.
- No explicit handling of missing/zero signal values — no instruction
  to distinguish "no risk found" from "this field wasn't populated."
- No constraint on output format — free-form text rather than
  structured JSON, making downstream parsing in the app unreliable.
- Reasoning text had no requirement to cite specific numbers from the
  input, risking generic output ("this company shows some risk")
  rather than grounded, specific explanations.

v2 (prompts/account_scoring_v2.md) addresses all four directly — see
that file's system prompt and changelog.