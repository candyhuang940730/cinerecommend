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

def social_scores(c, user_id, min_common=3, k=50):
    """找品味相似的使用者(Pearson,共評片),相似度 × 信任度 加權其評分。"""
    R = pd.read_sql("SELECT user_id, movie_id, rating FROM reviews", c)\
          .pivot(index="user_id", columns="movie_id", values="rating")
    trust = pd.read_sql("SELECT user_id, trust FROM user_trust", c).set_index("user_id").trust
    me = R.loc[user_id]
    sims = {}
    for u, row in R.drop(user_id).iterrows():
        common = me.notna() & row.notna()
        if common.sum() >= min_common:
            a, b = me[common], row[common]
            if a.std() > 0 and b.std() > 0:
                sims[u] = np.corrcoef(a, b)[0, 1]
    s = pd.Series(sims).dropna().sort_values(ascending=False).head(k)
    w = s.clip(lower=0) * trust.reindex(s.index).fillna(0)       # 相似度 × 信任
    sub = R.loc[w.index]
    centered = sub.sub(sub.mean(axis=1), axis=0)
    unseen_cols = me.index[me.isna()]
    num = centered[unseen_cols].mul(w, axis=0).sum()
    den = sub[unseen_cols].notna().mul(w, axis=0).sum()
    return (num / den.replace(0, np.nan)).dropna()

def list_genres():
    with conn() as c:
        return pd.read_sql("SELECT name FROM genres ORDER BY name", c).name.tolist()

def recommend(user_id, topk=10, alpha=0.5, genres=None):
    with conn() as c:
        cs = content_scores(c, liked_movies(c, user_id))
        ss = social_scores(c, user_id)
        norm = lambda s: (s - s.min()) / (s.max() - s.min() + 1e-9) if len(s) else s
        df = pd.concat([norm(cs).rename("content"), norm(ss).rename("social")], axis=1).fillna(0)
        df["final"] = alpha * df.content + (1 - alpha) * df.social

        if genres:  # 只保留至少屬於一個所選類型的電影
            ok = pd.read_sql(
                """SELECT DISTINCT mg.movie_id FROM movie_genres mg
                   JOIN genres g USING(genre_id) WHERE g.name = ANY(%s)""",
                c, params=(genres,)).movie_id
            df = df[df.index.isin(ok)]

        top = df.sort_values("final", ascending=False).head(topk)
        info = pd.read_sql("SELECT movie_id,title,year,poster_url FROM movies WHERE movie_id = ANY(%s)",
                           c, params=(top.index.tolist(),)).set_index("movie_id")
        return top.join(info)
