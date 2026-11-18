"""Precision@K / Recall@K,並做消融比較(只內容 / 只社群 / 混合)。"""
import numpy as np
from core import recommend as R
from core.db import conn

def split(c, user_id, holdout=0.2, thr=4.0, seed=0):
    liked = R.liked_movies(c, user_id, thr)
    rng = np.random.default_rng(seed); rng.shuffle(liked)
    n = max(1, int(len(liked) * holdout))
    return liked[n:], set(liked[:n])

def pr_at_k(recs, truth, k):
    hit = len(set(recs[:k]) & truth)
    return hit / k, hit / max(1, len(truth))

def run(users, k=10, alpha=0.5, min_liked=10):
    P, Rc = [], []
    for u in users:
        with conn() as c:
            if len(R.liked_movies(c, u)) < min_liked:   # 高分片太少的人不評估
                continue
            _, truth = split(c, u)
        recs = R.recommend(u, topk=k, alpha=alpha, holdout=truth).index.tolist()
        p, r = pr_at_k(recs, truth, k); P.append(p); Rc.append(r)
    print(f"  評估了 {len(P)} 位使用者")
    return round(np.mean(P), 4), round(np.mean(Rc), 4)

def run_popular(users, k=10, min_liked=10):
    """基準線:推薦評分人數最多、且使用者沒看過的電影"""
    import pandas as pd
    P, Rc = [], []
    with conn() as c:
        pop = pd.read_sql("SELECT movie_id, count(*) n FROM reviews GROUP BY movie_id ORDER BY n DESC", c).movie_id.tolist()
    for u in users:
        with conn() as c:
            if len(R.liked_movies(c, u)) < min_liked:
                continue
            _, truth = split(c, u)
            seen = set(pd.read_sql("SELECT movie_id FROM reviews WHERE user_id=%s", c, params=(u,)).movie_id) - truth
        recs = [m for m in pop if m not in seen][:k]
        p, r = pr_at_k(recs, truth, k); P.append(p); Rc.append(r)
    return round(float(np.mean(P)), 4), round(float(np.mean(Rc)), 4)

if __name__ == "__main__":
    import sys, csv
    users = range(1, 301)
    settings = [("熱門榜基準", None), ("只內容", 1.0), ("只社群", 0.0), ("混合", 0.5)]
    only = sys.argv[1] if len(sys.argv) > 1 else None   # 可只跑單一項,例如: python -m core.evaluate 只內容

    with open("eval_results.csv", "a", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        for name, a in settings:
            if only and only != name:
                continue
            print(f"開始:{name}", flush=True)
            res = run_popular(users) if a is None else run(users, alpha=a)
            print(f"{name}: P@10, R@10 = {res}", flush=True)
            w.writerow([name, a, *res]); f.flush()