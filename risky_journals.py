#!/usr/bin/env python3
"""
Risky Journals Sampler
Flags potential risky journal entries using simple, explainable rules.
Outputs:
  out/risky.csv   -> flagged entries with scores and reasons
  out/summary.md  -> counts and quick insights
Usage:
  python risky_journals.py --csv data/sample_journals.csv --out out
"""
import argparse, os
import pandas as pd
import numpy as np

RISKY_MEMO_TERMS = [
    "manual override","adjustment","adj","suspense","top-side","plug","write-off","reclass","misc"
]

WEIGHTS = {
    "round_100": 1,
    "round_1000": 2,
    "cents_zero": 1,
    "weekend": 1,
    "late_night": 2,
    "risky_memo": 2,
    "manual_source": 2,
    "duplicate": 3,
    "top1pct": 2,
}

def _is_round_multiple(x, m):
    try:
        return (abs(x) % m) == 0
    except Exception:
        return False

def analyze(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    d["amount"] = pd.to_numeric(d["amount"], errors="coerce")
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    d["memo"] = d["memo"].astype(str).fillna("")
    d["user"] = d["user"].astype(str).fillna("")
    d["account"] = d["account"].astype(str).fillna("")
    d["source"] = d.get("source", pd.Series(["SYSTEM"]*len(d))).astype(str)

    d["round_100"] = d["amount"].apply(lambda x: _is_round_multiple(x, 100))
    d["round_1000"] = d["amount"].apply(lambda x: _is_round_multiple(x, 1000))
    d["cents_zero"] = (np.round((np.abs(d["amount"]) * 100) % 100, 2) == 0.0)

    d["weekend"] = d["date"].dt.weekday.isin([5,6])
    d["late_night"] = d["date"].dt.hour.isin([22,23,0,1,2,3,4,5])

    lower_memo = d["memo"].str.lower()
    d["risky_memo"] = lower_memo.apply(lambda s: any(term in s for term in RISKY_MEMO_TERMS))

    d["manual_source"] = ~d["source"].str.upper().eq("SYSTEM")

    abs_amt = d["amount"].abs()
    cutoff = abs_amt.quantile(0.99) if len(d) >= 100 else abs_amt.quantile(0.95)
    d["top1pct"] = abs_amt >= cutoff

    key = pd.to_datetime(d["date"]).dt.date.astype(str) + "|" + d["account"] + "|" + d["amount"].round(2).astype(str) + "|" + lower_memo
    counts = key.value_counts()
    d["duplicate"] = key.map(lambda k: counts.get(k, 0) > 1)

    cols = ["round_100","round_1000","cents_zero","weekend","late_night","risky_memo","manual_source","duplicate","top1pct"]
    d["risk_score"] = d[cols].mul(pd.Series(WEIGHTS)).sum(axis=1).astype(int)
    d["reasons"] = d.apply(lambda row: ",".join([name for name in cols if bool(row[name])]), axis=1)

    d = d.sort_values(["risk_score", d["amount"].abs()], ascending=[False, False])
    return d

def write_outputs(d: pd.DataFrame, outdir: str):
    os.makedirs(outdir, exist_ok=True)
    risky = d[d["risk_score"] >= 2].copy()
    risky_cols = ["entry_id","date","user","account","amount","memo","source","risk_score","reasons"]
    risky[risky_cols].to_csv(os.path.join(outdir, "risky.csv"), index=False)

    total = len(d)
    flagged = len(risky)
    top_rules = (risky["reasons"].str.split(",").explode().value_counts().head(5)).to_dict()
    by_user = risky.groupby("user")["risk_score"].sum().sort_values(ascending=False).head(5).to_dict()
    by_account = risky.groupby("account")["risk_score"].sum().sort_values(ascending=False).head(5).to_dict()

    md = []
    md.append("# Risky Journals — Summary")
    md.append(f"- Rows scanned: **{total}**")
    md.append(f"- Rows flagged (score ≥ 2): **{flagged}**")
    md.append("")
    md.append("## Top rule triggers")
    for k,v in top_rules.items():
        md.append(f"- {k}: **{v}**")
    md.append("")
    md.append("## Highest aggregate risk by user")
    for k,v in by_user.items():
        md.append(f"- {k}: **{v}**")
    md.append("")
    md.append("## Highest aggregate risk by account")
    for k,v in by_account.items():
        md.append(f"- {k}: **{v}**")
    md.append("")
    md.append("## How scoring works")
    for k,v in WEIGHTS.items():
        md.append(f"- {k}: {v}")
    md.append("")
    md.append("> Heuristics only. Use as a starting point for investigation.")
    with open(os.path.join(outdir, "summary.md"), "w") as f:
        f.write("\n".join(md))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out", default="out")
    args = ap.parse_args()
    df = pd.read_csv(args.csv)
    analyzed = analyze(df)
    write_outputs(analyzed, args.out)

if __name__ == "__main__":
    main()
