"""社群可信度:每位使用者一個 trust ∈ [0,1]。
trust = w1*consistency + w2*volume + w3*diversity
 - consistency: 評分與各片群眾平均的偏離越小越高 (1/(1+RMSE))
 - volume:      評分數量 log 飽和(太少=不可信)
 - diversity:   評分分佈熵;全給 5 星/1 星(灌水、洗負評)熵低 → 低分
"""
import numpy as np, pandas as pd
from core.db import conn

W = (0.5, 0.2, 0.3)

def compute(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["item_mean"] = df.groupby("movie_id").rating.transform("mean")
    df["item_n"]    = df.groupby("movie_id").rating.transform("count")
    df = df[df.item_n >= 5]
    df["sq"] = (df.rating - df.item_mean) ** 2
    g = df.groupby("user_id")
    cons = 1 / (1 + np.sqrt(g.sq.mean()))
    vol  = (np.log1p(g.size()) / np.log1p(200)).clip(0, 1)

    def ent(x):
        p = x.round().value_counts(normalize=True)
        return -(p * np.log2(p)).sum() / np.log2(5)
    div = g.rating.apply(ent)

    out = pd.DataFrame({"consistency": cons, "volume": vol, "diversity": div})
    out["trust"] = W[0] * out.consistency + W[1] * out.volume + W[2] * out.diversity
    return out

def main():
    with conn() as c:
        df = pd.read_sql("SELECT user_id, movie_id, rating FROM reviews", c)
        t = compute(df)
        with c.cursor() as cur:
            cur.executemany("""INSERT INTO user_trust VALUES (%s,%s,%s,%s,%s)
                ON CONFLICT (user_id) DO UPDATE SET consistency=EXCLUDED.consistency,
                volume=EXCLUDED.volume, diversity=EXCLUDED.diversity, trust=EXCLUDED.trust""",
                [(int(u), float(r.consistency), float(r.volume), float(r.diversity), float(r.trust))
                 for u, r in t.iterrows()])
        c.commit()

if __name__ == "__main__":
    main()
