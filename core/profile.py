import pandas as pd
from core.db import conn

NEW_USER_BASE = 8_000_000

def get_profile(user_id):
    with conn() as c:
        genre = pd.read_sql("""
            SELECT g.name, count(*) AS n, round(avg(r.rating)::numeric,2) AS avg_rating
            FROM reviews r JOIN movie_genres mg USING(movie_id)
            JOIN genres g USING(genre_id)
            WHERE r.user_id=%s GROUP BY g.name ORDER BY n DESC""", c, params=(user_id,))
        stat = pd.read_sql("SELECT count(*) n, round(avg(rating)::numeric,2) avg FROM reviews WHERE user_id=%s",
                           c, params=(user_id,)).iloc[0]
        t = pd.read_sql("SELECT trust FROM user_trust WHERE user_id=%s", c, params=(user_id,))
    return {"genre": genre, "n": int(stat.n), "avg": stat["avg"],
            "trust": float(t.trust.iloc[0]) if len(t) else None}

def search_movies(keyword, limit=10):
    with conn() as c:
        return pd.read_sql("SELECT movie_id,title,year,poster_url FROM movies WHERE title ILIKE %s LIMIT %s",
                           c, params=(f"%{keyword}%", limit))

def create_user():
    with conn() as c, c.cursor() as cur:
        cur.execute("SELECT coalesce(max(user_id), %s) + 1 FROM users WHERE user_id >= %s AND user_id < 9000000",
                    (NEW_USER_BASE, NEW_USER_BASE))
        uid = cur.fetchone()[0]
        cur.execute("INSERT INTO users(user_id) VALUES (%s)", (uid,))
        c.commit()
    return uid

def add_rating(user_id, movie_id, rating):
    with conn() as c, c.cursor() as cur:
        cur.execute("""INSERT INTO reviews VALUES (%s,%s,%s,now())
                       ON CONFLICT (user_id,movie_id) DO UPDATE SET rating=EXCLUDED.rating""",
                    (user_id, movie_id, rating))
        c.commit()