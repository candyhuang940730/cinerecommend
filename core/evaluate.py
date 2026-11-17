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

def run(users, k=10, alpha=0.5):
    P, Rc = [], []
    for u in users:
        # TODO: 評估時需把 holdout 的評分暫時遮蔽(例如建 reviews_train 表),否則會資料洩漏
        recs = R.recommend(u, topk=k, alpha=alpha).index.tolist()
        with conn() as c:
            _, truth = split(c, u)
        p, r = pr_at_k(recs, truth, k); P.append(p); Rc.append(r)
    return np.mean(P), np.mean(Rc)

if __name__ == "__main__":
    for a in (1.0, 0.0, 0.5):   # 1.0=只內容, 0.0=只社群, 0.5=混合
        print(f"alpha={a}: (P@10, R@10) =", run(range(1, 51), alpha=a))
