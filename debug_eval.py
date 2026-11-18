from core import recommend as R, evaluate as E
from core.db import conn

u = 1
with conn() as c:
    _, truth = E.split(c, u)
    print("被藏起來的喜歡片數:", len(truth))

for k in (10, 50, 200):
    recs = R.recommend(u, topk=k, alpha=0.5, holdout=truth)
    print(f"top{k} 命中:", len(set(recs.index) & truth), "| 推薦數:", len(recs))

print(R.recommend(u, topk=10, alpha=0.5, holdout=truth)[["title", "content", "social", "final"]])