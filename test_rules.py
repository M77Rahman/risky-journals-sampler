import pandas as pd
from risky_journals import analyze
def make_df(**k): return pd.DataFrame(k)
def test_round():
    df = make_df(entry_id=['A','B'],date=['2024-01-01 10:00:00','2024-01-01 10:05:00'],user=['U','U'],account=['1000','1000'],amount=[200.00,123.45],memo=['x','x'],source=['SYSTEM','SYSTEM'])
    out = analyze(df); assert bool(out.loc[0,'round_100']) and not bool(out.loc[1,'round_100'])
