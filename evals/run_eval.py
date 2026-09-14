import json
from scoring import rule_based_score

def run():
    with open("evals/labelled_set.jsonl") as f:
        examples = [json.loads(l) for l in f if l.strip()]

    correct = 0
    misses = []
    for ex in examples:
        pred = rule_based_score(ex["input_signals"])
        is_correct = pred["tier"] == ex["expected_tier"]
        correct += is_correct
        if not is_correct:
            misses.append({
                "id": ex["id"], "domain": ex["company_domain"],
                "expected": ex["expected_tier"], "predicted": pred["tier"],
                "notes": ex.get("notes", "")
            })

    accuracy = correct / len(examples)
    print(f"Accuracy: {accuracy:.1%} ({correct}/{len(examples)})")
    if misses:
        print("\nMisclassified:")
        for m in misses:
            print(f"  {m['domain']}: expected {m['expected']}, got {m['predicted']} — {m['notes']}")

if __name__ == "__main__":
    run()