# Eval results

## Run: [20260914]

- Prompt/logic version: rule-based scoring v2 (scoring.py)
- 30 examples: [your real count, e.g. 24]
- Accuracy (tier match): [86.7 %]
- Misclassified: ["iforte.net.id","verizon.net","mretec.com", "turk.net"  ]

## How labelling was done

Each example's `expected_tier` was assigned by manually reviewing the
raw signal values (input_signals) and applying the same hot/warm/cold
criteria the rule engine uses conceptually — without looking at the
system's own tier output first, to avoid circular validation.Re did the
exercise twice and evaluated based on input signals

## What 86.7% accuracy does and doesn't tell us

The rule-based scorer weights severe, specific indicators (DoublePulsar, malware, exposed databases) far more heavily than it weights the breadth of moderate signals — a company with many mild issues stacked together can under-score relative to how a human reviewer perceives cumulative risk. This is a deliberate design choice (severe signals should dominate), but the current thresholds don't explicitly account for signal breadth as its own escalation factor. The four misclassifications in this eval set were concentrated in exactly this pattern.

## Known weakness

The rule engine's fixed point-additive scoring evaluated surfaced four rubric-boundary disagreements rather than four arbitrary model failures