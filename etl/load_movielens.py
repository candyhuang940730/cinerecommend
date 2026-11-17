"""載入 MovieLens (movies/ratings/links)。用法: python -m etl.load_movielens ./ml-latest-small"""
import sys, re, pandas as pd
from psycopg2.extras import execute_values
from core.db import conn

def main(d, max_movies=5000):
    movies  = pd.read_csv(f"{d}/movies.csv")
    links   = pd.read_csv(f"{d}/links.csv")
    ratings = pd.read_csv(f"{d}/ratings.csv")
    movies = movies.merge(links[["movieId", "tmdbId"]], on="movieId").dropna(subset=["tmdbId"])
    # 取評分數最多的前 N 部,確保 CF 有足夠資料
    top = ratings.movieId.value_counts().head(max_movies).index
    movies = movies[movies.movieId.isin(top)]
    ratings = ratings[ratings.movieId.isin(movies.movieId)]

    with conn() as c, c.cursor() as cur:
        rows = []
        for r in movies.itertuples():
            m = re.search(r"\((\d{4})\)$", r.title)
            rows.append((int(r.movieId), int(r.tmdbId),
                         re.sub(r"\s*\(\d{4}\)$", "", r.title),
                         int(m.group(1)) if m else None))
        execute_values(cur, "INSERT INTO movies(movie_id,tmdb_id,title,year) VALUES %s ON CONFLICT DO NOTHING", rows)

        genres = sorted({g for s in movies.genres for g in s.split("|") if g != "(no genres listed)"})
        execute_values(cur, "INSERT INTO genres(name) VALUES %s ON CONFLICT DO NOTHING", [(g,) for g in genres])
        cur.execute("SELECT name, genre_id FROM genres"); gid = dict(cur.fetchall())
        execute_values(cur, "INSERT INTO movie_genres VALUES %s ON CONFLICT DO NOTHING",
            [(int(r.movieId), gid[g]) for r in movies.itertuples() for g in r.genres.split("|") if g in gid])

        execute_values(cur, "INSERT INTO users(user_id) VALUES %s ON CONFLICT DO NOTHING",
                       [(int(u),) for u in ratings.userId.unique()])
        execute_values(cur, "INSERT INTO reviews VALUES %s ON CONFLICT DO NOTHING",
            [(int(r.userId), int(r.movieId), float(r.rating), pd.to_datetime(r.timestamp, unit="s"))
             for r in ratings.itertuples()], page_size=10000)

if __name__ == "__main__":
    main(sys.argv[1])
