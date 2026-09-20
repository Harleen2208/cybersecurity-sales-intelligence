import pandas as pd

def rule_based_score(row: dict) -> dict:
    score = 0
    reasons = []

    if row.get("doublepulsar_count", 0) > 0:
        score += 60
        reasons.append("DoublePulsar backdoor detected — likely already compromised")
    if row.get("malware_count", 0) > 0:
        score += 60
        reasons.append("Active malware detected on exposed host")
    if row.get("eol_product_count", 0) > 0:
        score += 25
        reasons.append(f"{row['eol_product_count']} end-of-life software services exposed")
    if row.get("eol_os_count", 0) > 0:
        score += 20
        reasons.append(f"{row['eol_os_count']} end-of-life operating systems exposed")
    if row.get("self_signed_count", 0) > 0:
        score += 10
        reasons.append(f"{row['self_signed_count']} self-signed certificates found")
    if row.get("open_dir_count", 0) > 0:
        score += 15
        reasons.append("Open directory listing exposed")
    if row.get("exposed_database_count", 0) > 0:
        score += 20
        reasons.append(f"{row['exposed_database_count']} database service(s) directly exposed")

    open_ports = row.get("distinct_open_ports", 0)
    if open_ports >= 10:
        score += 15
    elif open_ports >= 5:
        score += 8

    score = min(score, 100)
    tier = "hot" if score >= 70 else "warm" if score >= 40 else "cold"
    return {"rule_score": score, "tier": tier, "rule_reasons": reasons}


if __name__ == "__main__":
    df = pd.read_parquet("companies.parquet")
    records = df.to_dict("records")
    results = [{**row, **rule_based_score(row)} for row in records]
    out = pd.DataFrame(results)
    out.to_parquet("companies_scored.parquet")
    print(out[["company_domain", "rule_score", "tier"]].merge(df[["company_domain","distinct_ip_count","org"]], on="company_domain").sort_values("rule_score", ascending=False).head(20))