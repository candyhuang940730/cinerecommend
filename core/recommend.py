"""混合推薦:final = alpha*內容相似度(多模態) + (1-alpha)*社群信任加權 CF"""
import numpy as np, pandas as pd
from core.db import conn

def liked_movies(c, user_id, thr=4.0):
    return pd.read_sql("SELECT movie_id FROM reviews WHERE user_id=%s AND rating>=%s",
                       c, params=(user_id, thr)).movie_id.tolist()

def content_scores(c, liked, w_text=0.6, w_img=0.4):
    """用 pgvector 計算候選片與使用者喜歡片 centroid 的 cosine 相似度。"""
    if not liked:
        return pd.Series(dtype=float)
    q = """
    WITH prof AS (SELECT avg(text_vec) t, avg(poster_vec) p FROM movie_features WHERE movie_id = ANY(%s))
    SELECT f.movie_id,
           %s*(1-(f.text_vec <=> prof.t)) + %s*COALESCE(1-(f.poster_vec <=> prof.p),0) AS s
    FROM movie_features f, prof WHERE f.movie_id <> ALL(%s)"""
    return pd.read_sql(q, c, params=(liked, w_text, w_img, liked)).set_index("movie_id").s

def social_scores(c, user_id, min_common=5, k=50, holdout=None,
                  shrink=10, min_support=2, damping=1.0, use_trust=True):
    R = pd.read_sql("SELECT user_id, movie_id, rating FROM reviews", c)\
          .pivot(index="user_id", columns="movie_id", values="rating")
    if holdout:
        R.loc[user_id, [m for m in holdout if m in R.columns]] = np.nan
    trust = pd.read_sql("SELECT user_id, trust FROM user_trust", c).set_index("user_id").trust
    me = R.loc[user_id]
    sims = {}
    for u, row in R.drop(user_id).iterrows():
        common = me.notna() & row.notna()
        n = int(common.sum())
        if n >= min_common:
            a, b = me[common], row[common]
            if a.std() > 0 and b.std() > 0:
                sims[u] = np.corrcoef(a, b)[0, 1] * n / (n + shrink)   # 共評越少,相似度越打折
    s = pd.Series(sims).dropna().sort_values(ascending=False).head(k)
    t = trust.reindex(s.index).fillna(0) if use_trust else 1.0
    w = s.clip(lower=0) * t
    sub = R.loc[w.index]
    centered = sub.sub(sub.mean(axis=1), axis=0)
    cols = me.index[me.isna()]
    num = centered[cols].mul(w, axis=0).sum()
    den = sub[cols].notna().mul(w, axis=0).sum()
    support = sub[cols].notna().sum()
    pred = (num / (den + damping))[support >= min_support]               # 阻尼 + 最低支持度
    return pred.dropna()

def list_genres():
    with conn() as c:
        return pd.read_sql("SELECT name FROM genres ORDER BY name", c).name.tolist()


def recommend(user_id, topk=10, alpha=0.5, genres=None, holdout=None):
    holdout = set(holdout or [])
    with conn() as c:
        liked = [m for m in liked_movies(c, user_id) if m not in holdout]
        cs = content_scores(c, liked)
        ss = social_scores(c, user_id, holdout=holdout)
        norm = lambda s: (s - s.min()) / (s.max() - s.min() + 1e-9) if len(s) else s
        df = pd.concat([norm(cs).rename("content"), norm(ss).rename("social")], axis=1).fillna(0)
        df["final"] = alpha * df.content + (1 - alpha) * df.social
        if genres:
            ok = pd.read_sql("""SELECT DISTINCT mg.movie_id FROM movie_genres mg
                                JOIN genres g USING(genre_id) WHERE g.name = ANY(%s)""",
                             c, params=(genres,)).movie_id
            df = df[df.index.isin(ok)]
        top = df.sort_values("final", ascending=False).head(topk)
        info = pd.read_sql("SELECT movie_id,title,year,poster_url FROM movies WHERE movie_id = ANY(%s)",
                           c, params=(top.index.tolist(),)).set_index("movie_id")
        return top.join(info)
