import streamlit as st
import pandas as pd

st.set_page_config(page_title="Cybersecurity Prospecting Dashboard", layout="wide")
st.title("🎯 Sales Intelligence — Prospecting Dashboard")
st.caption("Ranking companies by exposure risk, derived from internet-scan signals (Shodan-style data).")

@st.cache_data
def load_data():
    df = pd.read_parquet("companies_final.parquet")
    df["reasoning_summary"] = df["reasoning_summary"].fillna(
        df["rule_reasons"].apply(lambda r: "; ".join(r) if isinstance(r, list) and len(r) > 0 else "No detailed signals available")
    )
    return df

df = load_data()

col1, col2, col3 = st.columns(3)
col1.metric("Total companies", len(df))
col2.metric("Hot leads", (df["tier"] == "hot").sum())
col3.metric("Warm leads", (df["tier"] == "warm").sum())

st.divider()

tier_filter = st.multiselect("Filter by tier", ["hot", "warm", "cold"], default=["hot", "warm"])
filtered = df[df["tier"].isin(tier_filter)].sort_values("rule_score", ascending=False)

st.dataframe(
    filtered[["company_domain", "org", "rule_score", "tier",
              "eol_product_count", "self_signed_count", "distinct_open_ports",
              "reasoning_summary"]],
    use_container_width=True,
    height=500
)

st.divider()
st.subheader("Drill into an account")
selected = st.selectbox("Select a company", filtered["company_domain"])
row = filtered[filtered["company_domain"] == selected].iloc[0]

c1, c2 = st.columns([1, 2])
with c1:
    st.metric("Score", f"{row['rule_score']}/100")
    st.metric("Tier", row["tier"].upper())
    st.write(f"**Org:** {row.get('org', 'Unknown')}")
with c2:
    st.write("**Why this account:**")
    st.info(row["reasoning_summary"])
    st.write("**Raw signals:**")
    st.json({
        "eol_product_count": int(row.get("eol_product_count", 0)),
        "eol_os_count": int(row.get("eol_os_count", 0)),
        "self_signed_count": int(row.get("self_signed_count", 0)),
        "doublepulsar_count": int(row.get("doublepulsar_count", 0)),
        "malware_count": int(row.get("malware_count", 0)),
        "open_dir_count": int(row.get("open_dir_count", 0)),
        "exposed_database_count": int(row.get("exposed_database_count", 0)),
        "distinct_open_ports": int(row.get("distinct_open_ports", 0)),
    })