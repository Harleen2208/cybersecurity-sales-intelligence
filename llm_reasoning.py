import json
import time
import uuid
from datetime import datetime, timezone
from google import genai
from google.genai import types
import pandas as pd
import os

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL_NAME = "gemini-3.6-flash"  # error message told us to use this instead of 2.0-flash

SYSTEM_PROMPT_V2 = open("prompts/account_scoring_v2.md").read()

def get_reasoning(row: dict, log_file="traces.jsonl") -> str:
    signals = {
        "eol_product_count": row.get("eol_product_count", 0),
        "eol_os_count": row.get("eol_os_count", 0),
        "self_signed_count": row.get("self_signed_count", 0),
        "doublepulsar_count": row.get("doublepulsar_count", 0),
        "malware_count": row.get("malware_count", 0),
        "open_dir_count": row.get("open_dir_count", 0),
        "exposed_database_count": row.get("exposed_database_count", 0),
        "rule_score": row.get("rule_score", 0),
    }

    start = time.time()
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=json.dumps(signals),
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT_V2,
        ),
    )
    latency_ms = int((time.time() - start) * 1000)

    text = response.text.strip()
    if text.startswith("```"):
        text = text.strip("`").replace("json", "", 1).strip()
    parsed = json.loads(text)

    usage = response.usage_metadata
    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "call_id": str(uuid.uuid4()),
        "skill": "account-scoring",
        "prompt_version": "v2",
        "model": MODEL_NAME,
        "input_company": row.get("company_domain"),
        "input_tokens": usage.prompt_token_count,
        "output_tokens": usage.candidates_token_count,
        "latency_ms": latency_ms,
        "cost_usd": 0.0,
        "output": parsed,
    }
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    return parsed["reasoning_summary"]


if __name__ == "__main__":
    df = pd.read_parquet("companies_scored.parquet")
    top = df.sort_values("rule_score", ascending=False).head(21).copy()

    results = []
    for r in top.to_dict("records"):
        results.append(get_reasoning(r))
        time.sleep(4)

    top["reasoning_summary"] = results
    top.to_parquet("companies_final.parquet")
    print(top[["company_domain", "rule_score", "reasoning_summary"]])