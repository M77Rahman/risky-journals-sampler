# Risky Journals Sampler
Flags potentially risky journal entries using simple, explainable rules.

**Outputs**
- `out/risky.csv` – flagged entries with `risk_score` and `reasons`
- `out/summary.md` – quick counts and top drivers

## Rules (weights)
round_100 (1), round_1000 (2), cents_zero (1), weekend (1), late_night (2), risky_memo (2), manual_source (2), duplicate (3), top1pct (2)

## Quickstart (Python 3)
```bash
pip install -r requirements.txt
python risky_journals.py --csv data/sample_journals.csv --out out
```
